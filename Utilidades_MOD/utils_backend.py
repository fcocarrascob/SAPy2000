import comtypes.client
import sys, os
import math
from collections import OrderedDict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code


STEEL_MATERIALS = {
    "A36": {"Fy_MPa": 250, "Fu_MPa": 400, "E_MPa": 200000},
    "A572 Gr50": {"Fy_MPa": 345, "Fu_MPa": 450, "E_MPa": 200000},
    "A992": {"Fy_MPa": 345, "Fu_MPa": 450, "E_MPa": 200000},
    "A500 Gr B": {"Fy_MPa": 317, "Fu_MPa": 400, "E_MPa": 200000},
    "A500 Gr C": {"Fy_MPa": 345, "Fu_MPa": 427, "E_MPa": 200000},
}


SECTION_TYPES = OrderedDict([
    ("W", {
        "display": "W (I-Beam)",
        "params": [("d", "d - Peralte", 30.0), ("bf", "bf - Ancho de ala", 15.0),
                   ("tf", "tf - Espesor de ala", 1.5), ("tw", "tw - Espesor de alma", 0.9),
                   ("bf_bot", "bf_bot - Ancho ala inf. (0=sim)", 0.0),
                   ("tfb", "tfb - Espesor ala inf. (0=sim)", 0.0)],
    }),
    ("C", {
        "display": "C (Canal)",
        "params": [("d", "d - Peralte", 25.0), ("bf", "bf - Ancho de ala", 7.5),
                   ("tf", "tf - Espesor de ala", 1.2), ("tw", "tw - Espesor de alma", 0.7)],
    }),
    ("L", {
        "display": "L (Angulo)",
        "params": [("d", "d - Ala larga", 15.0), ("b", "b - Ala corta", 10.0),
                   ("t", "t - Espesor", 1.2)],
    }),
    ("HSS_RECT", {
        "display": "HSS Rect (Tubo)",
        "params": [("H", "H - Altura", 20.0), ("B", "B - Ancho", 15.0),
                   ("t", "t - Espesor de pared", 1.2)],
    }),
    ("HSS_ROUND", {
        "display": "HSS Round (Tubo circular)",
        "params": [("OD", "OD - Diametro exterior", 20.0), ("t", "t - Espesor de pared", 1.0)],
    }),
    ("2L", {
        "display": "2L (Doble angulo)",
        "params": [("d", "d - Ala larga", 15.0), ("b", "b - Ala corta", 10.0),
                   ("t", "t - Espesor", 1.2), ("sep", "sep - Separacion", 1.0)],
    }),
    ("2C", {
        "display": "2C (Doble canal)",
        "params": [("d", "d - Peralte", 25.0), ("bf", "bf - Ancho de ala", 7.5),
                   ("tf", "tf - Espesor de ala", 1.2), ("tw", "tw - Espesor de alma", 0.7),
                   ("sep", "sep - Separacion", 1.0)],
    }),
    ("WT", {
        "display": "WT (T cortada)",
        "params": [("d", "d - Peralte del vastago", 15.0), ("bf", "bf - Ancho de ala", 15.0),
                   ("tf", "tf - Espesor de ala", 1.5), ("tw", "tw - Espesor del vastago", 0.9)],
    }),
])


class SteelSectionCalc:
    """Calculadora de propiedades geometricas de secciones de acero."""

    @staticmethod
    def calc_properties(section_type, dims):
        """
        Calcula propiedades geometricas para la seccion dada.

        Args:
            section_type: str clave de SECTION_TYPES
            dims: dict con valores de los parametros
        Returns:
            dict con A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h_web
            o None si hay error
        """
        calculators = {
            "W": SteelSectionCalc._calc_w,
            "C": SteelSectionCalc._calc_c,
            "L": SteelSectionCalc._calc_l,
            "HSS_RECT": SteelSectionCalc._calc_hss_rect,
            "HSS_ROUND": SteelSectionCalc._calc_hss_round,
            "2L": SteelSectionCalc._calc_2l,
            "2C": SteelSectionCalc._calc_2c,
            "WT": SteelSectionCalc._calc_wt,
        }
        calc_fn = calculators.get(section_type)
        if not calc_fn:
            return None
        try:
            return calc_fn(dims)
        except (ZeroDivisionError, ValueError, KeyError):
            return None

    @staticmethod
    def _build_result(A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h_web):
        return {
            "A": A,
            "Ix": Ix,
            "Iy": Iy,
            "Sx_top": Sx_top,
            "Sx_bot": Sx_bot,
            "Sy": Sy,
            "Zx": Zx,
            "Zy": Zy,
            "rx": rx,
            "ry": ry,
            "J": J,
            "Cw": Cw,
            "h_web": h_web,
        }

    @staticmethod
    def _positive(*vals):
        return all(v > 0 for v in vals)

    @staticmethod
    def _composite_props(rects):
        area = 0.0
        qx = 0.0
        qy = 0.0
        for x0, x1, y0, y1 in rects:
            w = x1 - x0
            h = y1 - y0
            if w <= 0 or h <= 0:
                return None
            a = w * h
            area += a
            qx += a * ((x0 + x1) * 0.5)
            qy += a * ((y0 + y1) * 0.5)
        if area <= 0:
            return None
        x_bar = qx / area
        y_bar = qy / area

        Ix = 0.0
        Iy = 0.0
        for x0, x1, y0, y1 in rects:
            w = x1 - x0
            h = y1 - y0
            a = w * h
            cx = (x0 + x1) * 0.5
            cy = (y0 + y1) * 0.5
            Ix += (w * h ** 3) / 12.0 + a * (cy - y_bar) ** 2
            Iy += (h * w ** 3) / 12.0 + a * (cx - x_bar) ** 2
        return area, x_bar, y_bar, Ix, Iy

    @staticmethod
    def _find_pna(rects, axis):
        if axis == "x":
            lo = min(r[2] for r in rects)
            hi = max(r[3] for r in rects)
            total = sum((r[1] - r[0]) * (r[3] - r[2]) for r in rects)

            def area_below(y_ref):
                a = 0.0
                for x0, x1, y0, y1 in rects:
                    w = x1 - x0
                    if y_ref <= y0:
                        continue
                    if y_ref >= y1:
                        a += w * (y1 - y0)
                    else:
                        a += w * (y_ref - y0)
                return a

            target = 0.5 * total
            for _ in range(64):
                mid = 0.5 * (lo + hi)
                if area_below(mid) < target:
                    lo = mid
                else:
                    hi = mid
            return 0.5 * (lo + hi)

        lo = min(r[0] for r in rects)
        hi = max(r[1] for r in rects)
        total = sum((r[1] - r[0]) * (r[3] - r[2]) for r in rects)

        def area_left(x_ref):
            a = 0.0
            for x0, x1, y0, y1 in rects:
                h = y1 - y0
                if x_ref <= x0:
                    continue
                if x_ref >= x1:
                    a += h * (x1 - x0)
                else:
                    a += h * (x_ref - x0)
            return a

        target = 0.5 * total
        for _ in range(64):
            mid = 0.5 * (lo + hi)
            if area_left(mid) < target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    @staticmethod
    def _plastic_modulus(rects, axis):
        if not rects:
            return 0.0
        ref = SteelSectionCalc._find_pna(rects, axis)
        q = 0.0

        if axis == "x":
            for x0, x1, y0, y1 in rects:
                w = x1 - x0
                yb = min(ref, y1)
                if yb > y0:
                    a = w * (yb - y0)
                    c = 0.5 * (y0 + yb)
                    q += a * (ref - c)
                ya = max(ref, y0)
                if y1 > ya:
                    a = w * (y1 - ya)
                    c = 0.5 * (ya + y1)
                    q += a * (c - ref)
            return q

        for x0, x1, y0, y1 in rects:
            h = y1 - y0
            xl = min(ref, x1)
            if xl > x0:
                a = h * (xl - x0)
                c = 0.5 * (x0 + xl)
                q += a * (ref - c)
            xr = max(ref, x0)
            if x1 > xr:
                a = h * (x1 - xr)
                c = 0.5 * (xr + x1)
                q += a * (c - ref)
        return q

    @staticmethod
    def _calc_w(dims):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        bf_bot = float(dims.get("bf_bot", 0.0))
        tfb = float(dims.get("tfb", 0.0))
        if bf_bot <= 0:
            bf_bot = bf
        if tfb <= 0:
            tfb = tf
        if not SteelSectionCalc._positive(d, bf, tf, tw, bf_bot, tfb):
            return None

        h = d - tf - tfb
        if h <= 0:
            return None

        rects = [
            (-0.5 * bf_bot, 0.5 * bf_bot, 0.0, tfb),
            (-0.5 * tw, 0.5 * tw, tfb, tfb + h),
            (-0.5 * bf, 0.5 * bf, tfb + h, d),
        ]
        props = SteelSectionCalc._composite_props(rects)
        if not props:
            return None
        A, _, y_bar, Ix, Iy = props

        if y_bar <= 0 or d - y_bar <= 0:
            return None
        Sx_top = Ix / (d - y_bar)
        Sx_bot = Ix / y_bar
        Sy = (2.0 * Iy) / max(bf, bf_bot)
        Zx = SteelSectionCalc._plastic_modulus(rects, "x")
        Zy = (tf * bf ** 2) / 4.0 + (h * tw ** 2) / 4.0 + (tfb * bf_bot ** 2) / 4.0
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = (2.0 * bf * tf ** 3 + bf_bot * tfb ** 3 + h * tw ** 3) / 3.0
        Cw = (Iy * h ** 2) / 4.0

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h)

    @staticmethod
    def _calc_c(dims):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        if not SteelSectionCalc._positive(d, bf, tf, tw):
            return None

        h = d - 2.0 * tf
        if h <= 0:
            return None

        rects = [
            (0.0, bf, 0.0, tf),
            (0.0, tw, tf, d - tf),
            (0.0, bf, d - tf, d),
        ]
        props = SteelSectionCalc._composite_props(rects)
        if not props:
            return None
        A, x_bar, _, Ix, Iy = props

        c_top = d * 0.5
        c_left = x_bar
        c_right = bf - x_bar
        if c_top <= 0 or c_left <= 0 or c_right <= 0:
            return None

        Sx = Ix / c_top
        Sy_left = Iy / c_right
        Sy_right = Iy / c_left
        Sy = min(Sy_left, Sy_right)
        Zx = SteelSectionCalc._plastic_modulus(rects, "x")
        Zy = SteelSectionCalc._plastic_modulus(rects, "y")
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = (2.0 * bf * tf ** 3 + h * tw ** 3) / 3.0
        Cw = 0.0

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx, Sx, Sy, Zx, Zy, rx, ry, J, Cw, h)

    @staticmethod
    def _angle_core(d, b, t):
        if not SteelSectionCalc._positive(d, b, t):
            return None
        if d <= t or b <= t:
            return None
        rects = [
            (0.0, t, 0.0, d),
            (t, b, 0.0, t),
        ]
        props = SteelSectionCalc._composite_props(rects)
        if not props:
            return None
        A, x_bar, y_bar, Ix, Iy = props
        return rects, A, x_bar, y_bar, Ix, Iy

    @staticmethod
    def _calc_l(dims):
        d = float(dims["d"])
        b = float(dims["b"])
        t = float(dims["t"])
        core = SteelSectionCalc._angle_core(d, b, t)
        if not core:
            return None
        rects, A, x_bar, y_bar, Ix, Iy = core
        if y_bar <= 0 or d - y_bar <= 0:
            return None

        Sx_top = Ix / (d - y_bar)
        Sx_bot = Ix / y_bar
        Sy = Iy / max(x_bar, b - x_bar)
        Zx = SteelSectionCalc._plastic_modulus(rects, "x")
        Zy = SteelSectionCalc._plastic_modulus(rects, "y")
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = (d + b - t) * t ** 3 / 3.0
        Cw = 0.0
        h_web = max(d, b) - t

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h_web)

    @staticmethod
    def _calc_hss_rect(dims):
        H = float(dims["H"])
        B = float(dims["B"])
        t = float(dims["t"])
        if not SteelSectionCalc._positive(H, B, t):
            return None
        Hi = H - 2.0 * t
        Bi = B - 2.0 * t
        if Hi <= 0 or Bi <= 0:
            return None

        A = B * H - Bi * Hi
        if A <= 0:
            return None
        Ix = (B * H ** 3 - Bi * Hi ** 3) / 12.0
        Iy = (H * B ** 3 - Hi * Bi ** 3) / 12.0
        Sx = Ix / (H * 0.5)
        Sy = Iy / (B * 0.5)
        Zx = (B * H ** 2) / 4.0 - (Bi * Hi ** 2) / 4.0
        Zy = (H * B ** 2) / 4.0 - (Hi * Bi ** 2) / 4.0
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)

        Bm = B - t
        Hm = H - t
        if Bm <= 0 or Hm <= 0:
            return None
        J = (2.0 * t * (Bm ** 2) * (Hm ** 2)) / (Bm + Hm)
        Cw = 0.0
        h_web = H - 3.0 * t

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx, Sx, Sy, Zx, Zy, rx, ry, J, Cw, h_web)

    @staticmethod
    def _calc_hss_round(dims):
        OD = float(dims["OD"])
        t = float(dims["t"])
        if not SteelSectionCalc._positive(OD, t):
            return None
        ID = OD - 2.0 * t
        if ID <= 0:
            return None

        A = math.pi * (OD ** 2 - ID ** 2) / 4.0
        I = math.pi * (OD ** 4 - ID ** 4) / 64.0
        if A <= 0 or I <= 0:
            return None
        S = I / (OD * 0.5)
        Z = (OD ** 3 - ID ** 3) / 6.0
        r = math.sqrt(I / A)
        J = 2.0 * I
        Cw = 0.0
        h_web = 0.0

        return SteelSectionCalc._build_result(A, I, I, S, S, S, Z, Z, r, r, J, Cw, h_web)

    @staticmethod
    def _calc_2l(dims):
        d = float(dims["d"])
        b = float(dims["b"])
        t = float(dims["t"])
        sep = float(dims["sep"])
        if sep < 0:
            return None
        single = SteelSectionCalc._calc_l({"d": d, "b": b, "t": t})
        core = SteelSectionCalc._angle_core(d, b, t)
        if not single or not core:
            return None
        _, A1, x_bar, y_bar, Ix1, Iy1 = core

        A = 2.0 * A1
        Ix = 2.0 * Ix1
        dist = sep * 0.5 + x_bar
        Iy = 2.0 * (Iy1 + A1 * dist ** 2)
        if y_bar <= 0 or d - y_bar <= 0:
            return None
        Sx_top = Ix / (d - y_bar)
        Sx_bot = Ix / y_bar

        c_y = sep * 0.5 + b
        if c_y <= 0:
            return None
        Sy = Iy / c_y
        Zx = 2.0 * single["Zx"]
        Zy = 2.0 * (single["Zy"] + A1 * dist)
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = 2.0 * single["J"]
        Cw = 0.0
        h_web = single["h_web"]

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h_web)

    @staticmethod
    def _calc_2c(dims):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        sep = float(dims["sep"])
        if sep < 0:
            return None

        single = SteelSectionCalc._calc_c({"d": d, "bf": bf, "tf": tf, "tw": tw})
        if not single:
            return None

        h = d - 2.0 * tf
        if h <= 0:
            return None
        A1 = 2.0 * bf * tf + h * tw
        x_bar = (2.0 * bf * tf * (bf * 0.5) + h * tw * (tw * 0.5)) / A1

        A = 2.0 * A1
        Ix = 2.0 * single["Ix"]
        dist = sep * 0.5 + x_bar
        Iy = 2.0 * (single["Iy"] + A1 * dist ** 2)

        c_x = d * 0.5
        c_y = sep * 0.5 + bf
        if c_x <= 0 or c_y <= 0:
            return None
        Sx = Ix / c_x
        Sy = Iy / c_y
        Zx = 2.0 * single["Zx"]
        Zy = 2.0 * (single["Zy"] + A1 * dist)
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = 2.0 * single["J"]
        Cw = 0.0

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx, Sx, Sy, Zx, Zy, rx, ry, J, Cw, h)

    @staticmethod
    def _calc_wt(dims):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        if not SteelSectionCalc._positive(d, bf, tf, tw):
            return None
        stem_h = d - tf
        if stem_h <= 0:
            return None

        rects = [
            (-0.5 * tw, 0.5 * tw, 0.0, stem_h),
            (-0.5 * bf, 0.5 * bf, stem_h, d),
        ]
        props = SteelSectionCalc._composite_props(rects)
        if not props:
            return None
        A, _, y_bar, Ix, Iy = props

        if y_bar <= 0 or d - y_bar <= 0:
            return None
        Sx_top = Ix / (d - y_bar)
        Sx_bot = Ix / y_bar
        Sy = 2.0 * Iy / bf
        Zx = SteelSectionCalc._plastic_modulus(rects, "x")
        Zy = SteelSectionCalc._plastic_modulus(rects, "y")
        rx = math.sqrt(Ix / A)
        ry = math.sqrt(Iy / A)
        J = (bf * tf ** 3 + stem_h * tw ** 3) / 3.0
        Cw = 0.0
        h_web = stem_h

        return SteelSectionCalc._build_result(A, Ix, Iy, Sx_top, Sx_bot, Sy, Zx, Zy, rx, ry, J, Cw, h_web)


class SlendernessClassifier:
    """Clasificador de esbeltez segun AISC 360-16 Tabla B4.1."""

    CLASSIFICATION_ORDER = {"Compacto": 0, "No Compacto": 1, "Esbelto": 2}

    @staticmethod
    def classify(section_type, dims, Fy, E):
        """
        Clasifica los elementos de la seccion segun AISC 360-16 Table B4.1.

        Args:
            section_type: str key from SECTION_TYPES
            dims: dict of dimension values
            Fy: yield stress (any consistent unit)
            E: elastic modulus (same unit as Fy)
        Returns:
            dict with:
                "elements": list of dicts per element
                "overall_flexure": str
                "overall_compression": str
            or None on error
        """
        try:
            Fy = float(Fy)
            E = float(E)
            if Fy <= 0 or E <= 0:
                return None
        except (TypeError, ValueError):
            return None

        classifiers = {
            "W": SlendernessClassifier._classify_w,
            "C": SlendernessClassifier._classify_c,
            "L": SlendernessClassifier._classify_l,
            "HSS_RECT": SlendernessClassifier._classify_hss_rect,
            "HSS_ROUND": SlendernessClassifier._classify_hss_round,
            "2L": SlendernessClassifier._classify_2l,
            "2C": SlendernessClassifier._classify_2c,
            "WT": SlendernessClassifier._classify_wt,
        }
        fn = classifiers.get(section_type)
        if not fn:
            return None

        try:
            elements = fn(dims, Fy, E)
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            return None
        if not elements:
            return None

        overall_flexure = "Compacto"
        for elem in elements:
            cls = elem["class_flexure"]
            if SlendernessClassifier.CLASSIFICATION_ORDER[cls] > SlendernessClassifier.CLASSIFICATION_ORDER[overall_flexure]:
                overall_flexure = cls

        overall_comp = "No Esbelto"
        if any(elem["class_compression"] == "Esbelto" for elem in elements):
            overall_comp = "Esbelto"

        return {
            "elements": elements,
            "overall_flexure": overall_flexure,
            "overall_compression": overall_comp,
        }

    @staticmethod
    def _make_element(name, lam, formula, lam_p, lam_r_flex, lam_r_comp):
        if lam <= lam_p:
            class_flex = "Compacto"
        elif lam <= lam_r_flex:
            class_flex = "No Compacto"
        else:
            class_flex = "Esbelto"

        class_comp = "No Esbelto" if lam <= lam_r_comp else "Esbelto"

        return {
            "name": name,
            "lambda_val": lam,
            "formula": formula,
            "lambda_p": lam_p,
            "lambda_r_flex": lam_r_flex,
            "class_flexure": class_flex,
            "lambda_r_comp": lam_r_comp,
            "class_compression": class_comp,
        }

    @staticmethod
    def _classify_w(dims, Fy, E):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        bf_bot = float(dims.get("bf_bot", 0.0))
        tfb = float(dims.get("tfb", 0.0))
        if bf_bot <= 0:
            bf_bot = bf
        if tfb <= 0:
            tfb = tf
        if min(d, bf, tf, tw, bf_bot, tfb, Fy, E) <= 0:
            return None

        sqrt_ratio = math.sqrt(E / Fy)
        bf_eff = max(bf, bf_bot)
        tf_eff = min(tf, tfb)
        h = d - tf - tfb
        if tf_eff <= 0 or h <= 0:
            return None

        e1 = SlendernessClassifier._make_element(
            "Ala (no rigidizada)",
            bf_eff / (2.0 * tf_eff),
            "bf/(2*tf)",
            0.38 * sqrt_ratio,
            1.0 * sqrt_ratio,
            0.56 * sqrt_ratio,
        )
        e2 = SlendernessClassifier._make_element(
            "Alma (rigidizada en flexion)",
            h / tw,
            "h/tw",
            3.76 * sqrt_ratio,
            5.70 * sqrt_ratio,
            1.49 * sqrt_ratio,
        )
        return [e1, e2]

    @staticmethod
    def _classify_c(dims, Fy, E):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        if min(d, bf, tf, tw, Fy, E) <= 0:
            return None

        h = d - 2.0 * tf
        if h <= 0:
            return None
        sqrt_ratio = math.sqrt(E / Fy)

        e1 = SlendernessClassifier._make_element(
            "Ala (no rigidizada)",
            bf / tf,
            "bf/tf",
            0.38 * sqrt_ratio,
            1.0 * sqrt_ratio,
            0.56 * sqrt_ratio,
        )
        e2 = SlendernessClassifier._make_element(
            "Alma (rigidizada)",
            h / tw,
            "h/tw",
            3.76 * sqrt_ratio,
            5.70 * sqrt_ratio,
            1.49 * sqrt_ratio,
        )
        return [e1, e2]

    @staticmethod
    def _classify_l(dims, Fy, E):
        d = float(dims["d"])
        b = float(dims["b"])
        t = float(dims["t"])
        if min(d, b, t, Fy, E) <= 0:
            return None

        sqrt_ratio = math.sqrt(E / Fy)
        limits = (0.54 * sqrt_ratio, 0.91 * sqrt_ratio, 0.45 * sqrt_ratio)

        elements = [
            SlendernessClassifier._make_element("Ala larga", d / t, "d/t", limits[0], limits[1], limits[2])
        ]
        if abs(b - d) > 1e-9:
            elements.append(
                SlendernessClassifier._make_element("Ala corta", b / t, "b/t", limits[0], limits[1], limits[2])
            )
        return elements

    @staticmethod
    def _classify_hss_rect(dims, Fy, E):
        H = float(dims["H"])
        B = float(dims["B"])
        t = float(dims["t"])
        if min(H, B, t, Fy, E) <= 0:
            return None

        b_eff = B - 3.0 * t
        h_eff = H - 3.0 * t
        if b_eff <= 0 or h_eff <= 0:
            return None
        sqrt_ratio = math.sqrt(E / Fy)

        e1 = SlendernessClassifier._make_element(
            "Ala/Pared ancha (rigidizada)",
            b_eff / t,
            "(B-3t)/t",
            1.12 * sqrt_ratio,
            1.40 * sqrt_ratio,
            1.40 * sqrt_ratio,
        )
        e2 = SlendernessClassifier._make_element(
            "Alma/Pared alta (rigidizada)",
            h_eff / t,
            "(H-3t)/t",
            2.42 * sqrt_ratio,
            5.70 * sqrt_ratio,
            1.49 * sqrt_ratio,
        )
        return [e1, e2]

    @staticmethod
    def _classify_hss_round(dims, Fy, E):
        OD = float(dims["OD"])
        t = float(dims["t"])
        if min(OD, t, Fy, E) <= 0:
            return None

        ratio = E / Fy
        e1 = SlendernessClassifier._make_element(
            "Pared",
            OD / t,
            "OD/t",
            0.07 * ratio,
            0.31 * ratio,
            0.11 * ratio,
        )
        return [e1]

    @staticmethod
    def _classify_2l(dims, Fy, E):
        return SlendernessClassifier._classify_l(dims, Fy, E)

    @staticmethod
    def _classify_2c(dims, Fy, E):
        return SlendernessClassifier._classify_c(dims, Fy, E)

    @staticmethod
    def _classify_wt(dims, Fy, E):
        d = float(dims["d"])
        bf = float(dims["bf"])
        tf = float(dims["tf"])
        tw = float(dims["tw"])
        if min(d, bf, tf, tw, Fy, E) <= 0:
            return None

        stem_h = d - tf
        if stem_h <= 0:
            return None
        sqrt_ratio = math.sqrt(E / Fy)

        e1 = SlendernessClassifier._make_element(
            "Ala (no rigidizada)",
            bf / (2.0 * tf),
            "bf/(2*tf)",
            0.38 * sqrt_ratio,
            1.0 * sqrt_ratio,
            0.56 * sqrt_ratio,
        )
        e2 = SlendernessClassifier._make_element(
            "Vastago (no rigidizado en flexion)",
            stem_h / tw,
            "(d-tf)/tw",
            0.84 * sqrt_ratio,
            1.52 * sqrt_ratio,
            0.75 * sqrt_ratio,
        )
        return [e1, e2]

class SapUtils:
    def __init__(self, sap_model=None):
        """
        Inicializa la utilidad.
        
        Args:
            sap_model: Objeto SapModel opcional ya conectado.
        """
        self.SapModel = sap_model
        self.logger = AppLogger()

    def create_mesh_by_coord(self, width, length, nx, ny, start_x=0.0, start_y=0.0, start_z=0.0, plane="XY", prop_name="Default"):
        """
        Crea una malla rectangular de áreas usando AddByCoord en el plano especificado.
        
        Args:
            width (float): Dimensión 1 (X en XY/XZ, Y en YZ).
            length (float): Dimensión 2 (Y en XY, Z en XZ/YZ).
            nx (int): Número de divisiones en Dimensión 1.
            ny (int): Número de divisiones en Dimensión 2.
            start_x, start_y, start_z (float): Coordenadas de la esquina origen.
            plane (str): Plano de dibujo ("XY", "XZ", "YZ").
            prop_name (str): Nombre de la propiedad de área a asignar.
            
        Returns:
            list: Lista de nombres de las áreas creadas.
        """
        if self.SapModel is None:
            self.logger.warning("No hay conexión con SAP2000")
            return []

        created_areas = []
        
        # Asegurar tipos
        try:
            width = float(width)
            length = float(length)
            nx = int(nx)
            ny = int(ny)
            start_x = float(start_x)
            start_y = float(start_y)
            start_z = float(start_z)
        except ValueError as e:
            print(f"Error en conversión de tipos: {e}")
            return []

        d1 = width / nx
        d2 = length / ny
        
        self.logger.info(f"Generando malla {nx}x{ny} en plano {plane} (d1={d1:.2f}, d2={d2:.2f})...")
        
        # Bloquear pantalla para mejorar rendimiento (opcional, pero recomendado para muchas operaciones)
        # self.SapModel.SetModelIsLocked(False) 
        
        for i in range(nx):
            for j in range(ny):
                # Coordenadas locales 2D (u, v)
                u0 = i * d1
                v0 = j * d2
                
                # 4 esquinas en local 2D (antihorario)
                us = [u0, u0 + d1, u0 + d1, u0]
                vs = [v0, v0, v0 + d2, v0 + d2]
                
                xs, ys, zs = [], [], []
                
                for k in range(4):
                    u, v = us[k], vs[k]
                    if plane.upper() == "XY":
                        xs.append(start_x + u)
                        ys.append(start_y + v)
                        zs.append(start_z)
                    elif plane.upper() == "XZ":
                        xs.append(start_x + u)
                        ys.append(start_y)
                        zs.append(start_z + v)
                    elif plane.upper() == "YZ":
                        xs.append(start_x)
                        ys.append(start_y + u)
                        zs.append(start_z + v)
                
                try:
                    # AddByCoord(NumberPoints, x, y, z, Name, PropName, UserName, CSys)
                    # En Python comtypes, los parámetros ByRef de salida se retornan en una tupla.
                    # La firma esperada retorna: [Name, RetCode] (o similar, dependiendo de la versión exacta de la API y comtypes)
                    # Nota: AddByCoord retorna 0 si es exitoso como último elemento.
                    
                    ret = self.SapModel.AreaObj.AddByCoord(4, xs, ys, zs, "", prop_name, "", "Global")
                    
                    # Manejo robusto del retorno (Regla de Oro)
                    # ret puede ser un int (solo código) o una tupla/lista
                    area_name = ""
                    if check_ret_code(ret):
                        if isinstance(ret, (list, tuple)) and len(ret) > 1:
                            area_name = str(ret[0])
                        if area_name:
                            created_areas.append(area_name)
                    else:
                        code = ret[-1] if isinstance(ret, (list, tuple)) and len(ret) > 0 else ret
                        self.logger.error(f"Error creando área en celda ({i},{j}): Código {code}")
                        
                except Exception as e:
                    self.logger.error(f"Excepción en celda ({i},{j}): {e}")
                    
        self.logger.success(f"Se crearon {len(created_areas)} áreas en {plane}.")
        
        # Refrescar vista
        try:
            self.SapModel.View.RefreshView(0, False)
        except Exception:
            pass
        
        return created_areas

    # --- Funciones Auxiliares de Geometría y Creación ---

    def create_point(self, x, y, z, name=""):
        """Crea un punto en SAP2000 y retorna su nombre."""
        try:
            # AddCartesian(x, y, z, Name, UserName, CSys, ...)
            # Retorna [Name, RetCode]
            ret = self.SapModel.PointObj.AddCartesian(x, y, z, "", name, "Global")
            if check_ret_code(ret):
                if isinstance(ret, (list, tuple)) and len(ret) > 1:
                    return str(ret[0])
                return name
            elif isinstance(ret, int) and ret == 0:
                return name
        except Exception as e:
            self.logger.error(f"Error creando punto ({x},{y},{z}): {e}")
        return None

    def create_area_by_points(self, points, prop_name="Default"):
        """Crea un área dada una lista de nombres de puntos."""
        try:
            # AddByPoint(NumberPoints, PointNames, Name, PropName, UserName)
            ret = self.SapModel.AreaObj.AddByPoint(len(points), points, "", prop_name, "")
            if check_ret_code(ret):
                if isinstance(ret, (list, tuple)) and len(ret) > 1:
                    return str(ret[0])
        except Exception as e:
            self.logger.error(f"Error creando área con puntos {points}: {e}")
        return None

    def _get_shape_coords_2d(self, shape_type, center_u, center_v, dim, num_points):
        """
        Genera coordenadas 2D (u, v) para una forma dada.
        shape_type: 'Círculo' o 'Cuadrado'
        dim: Diámetro (si es círculo) o Lado (si es cuadrado)
        """
        coords = []
        radius = dim / 2.0
        
        # Pre-calculation for square (equidistant spacing)
        # Perimeter = 4 * dim
        # Step = Perimeter / num_points
        perimeter = 4.0 * dim
        step = perimeter / float(num_points) if num_points > 0 else 0
        
        for i in range(num_points):
            if shape_type.lower() == "círculo":
                # Ángulo negativo para sentido horario (eje 3 → +Z)
                angle = -2 * math.pi * i / num_points
                u = center_u + radius * math.cos(angle)
                v = center_v + radius * math.sin(angle)
                coords.append((u, v))
                
            elif shape_type.lower() == "cuadrado":
                # Equidistant walking along perimeter
                # Start at Angle 0 (Right Middle) -> (radius, 0) relative to center
                # CW direction: Down -> Left -> Up -> Right (eje 3 → +Z)
                
                current_dist = i * step
                
                u_local = 0.0
                v_local = 0.0
                
                # Phase 1: Right edge, moving DOWN (from 0 to -radius)
                if current_dist < radius:
                    u_local = radius
                    v_local = -current_dist
                # Phase 2: Bottom edge, moving LEFT
                elif current_dist < radius + dim:
                    rem = current_dist - radius
                    u_local = radius - rem
                    v_local = -radius
                # Phase 3: Left edge, moving UP
                elif current_dist < radius + 2*dim:
                    rem = current_dist - (radius + dim)
                    u_local = -radius
                    v_local = -radius + rem
                # Phase 4: Top edge, moving RIGHT
                elif current_dist < radius + 3*dim:
                    rem = current_dist - (radius + 2*dim)
                    u_local = -radius + rem
                    v_local = radius
                # Phase 5: Right edge, moving DOWN (from +radius to 0)
                else:
                    rem = current_dist - (radius + 3*dim)
                    u_local = radius
                    v_local = radius - rem
                
                u = center_u + u_local
                v = center_v + v_local
                coords.append((u, v))
                
        return coords

    def create_hole_mesh(self, 
                         outer_shape, outer_dim, 
                         inner_shape, inner_dim, 
                         num_angular, num_radial, 
                         origin_x, origin_y, origin_z, 
                         plane="XY", prop_name="Default"):
        """
        Crea una malla con orificio (o transición de formas) interpolando entre dos anillos.
        
        Args:
            outer_shape (str): "Círculo" o "Cuadrado".
            outer_dim (float): Dimensión externa (Lado o Diámetro).
            inner_shape (str): "Círculo" o "Cuadrado".
            inner_dim (float): Dimensión interna (Lado o Diámetro).
            num_angular (int): Número de puntos por anillo.
            num_radial (int): Número de subdivisiones radiales (anillos de áreas).
            origin_x, origin_y, origin_z (float): Coordenada de la esquina de referencia (bounding box).
            plane (str): "XY", "XZ", "YZ".
            prop_name (str): Propiedad de área.
        """
        if self.SapModel is None:
            return []

        self.logger.info(f"Generando malla con orificio: {inner_shape} -> {outer_shape} en {plane}...")
        
        # 1. Definir centro local (u, v) relativo al origen (esquina)
        # Asumimos que el origen es la esquina inferior izquierda del bounding box externo
        center_u = outer_dim / 2.0
        center_v = outer_dim / 2.0
        
        # Crear nodo en el centro
        if plane.upper() == "XY":
            cx = origin_x + center_u
            cy = origin_y + center_v
            cz = origin_z
        elif plane.upper() == "XZ":
            cx = origin_x + center_u
            cy = origin_y
            cz = origin_z + center_v
        elif plane.upper() == "YZ":
            cx = origin_x
            cy = origin_y + center_u
            cz = origin_z + center_v
        else:
            cx, cy, cz = origin_x, origin_y, origin_z
            
        self.create_point(cx, cy, cz)
        
        # 2. Generar coordenadas locales 2D para anillo interno y externo
        inner_coords = self._get_shape_coords_2d(inner_shape, center_u, center_v, inner_dim, num_angular)
        outer_coords = self._get_shape_coords_2d(outer_shape, center_u, center_v, outer_dim, num_angular)
        
        # 3. Generar anillos intermedios y crear puntos en SAP2000
        # all_rings_points[r][i] guardará el nombre del punto
        all_rings_points = [] 
        
        # Total de anillos de puntos = num_radial + 1
        # r=0 es interno, r=num_radial es externo
        
        for r in range(num_radial + 1):
            fraction = r / float(num_radial) if num_radial > 0 else 1.0
            ring_points = []
            
            for i in range(num_angular):
                u_in, v_in = inner_coords[i]
                u_out, v_out = outer_coords[i]
                
                # Interpolación lineal
                u = u_in + (u_out - u_in) * fraction
                v = v_in + (v_out - v_in) * fraction
                
                # Transformar a Global 3D según plano
                if plane.upper() == "XY":
                    gx = origin_x + u
                    gy = origin_y + v
                    gz = origin_z
                elif plane.upper() == "XZ":
                    gx = origin_x + u
                    gy = origin_y
                    gz = origin_z + v
                elif plane.upper() == "YZ":
                    gx = origin_x
                    gy = origin_y + u
                    gz = origin_z + v
                else:
                    gx, gy, gz = origin_x, origin_y, origin_z
                
                # Crear punto
                p_name = self.create_point(gx, gy, gz)
                if p_name:
                    ring_points.append(p_name)
                else:
                    # Fallback si falla crear punto (no debería pasar)
                    ring_points.append("")
            
            all_rings_points.append(ring_points)
            
        # 4. Crear Áreas conectando anillos
        created_areas = []
        
        for r in range(num_radial):
            inner_ring = all_rings_points[r]
            outer_ring = all_rings_points[r+1]
            
            # Verificar que tenemos puntos válidos
            if not inner_ring or not outer_ring:
                continue
                
            for i in range(num_angular):
                # Conectar 4 puntos: 
                # P1(inner, i) -> P2(inner, i+1) -> P3(outer, i+1) -> P4(outer, i)
                # Sentido antihorario usualmente
                
                p1 = inner_ring[i]
                p2 = inner_ring[(i+1) % num_angular]
                p3 = outer_ring[(i+1) % num_angular]
                p4 = outer_ring[i]
                
                if all([p1, p2, p3, p4]):
                    aname = self.create_area_by_points([p1, p2, p3, p4], prop_name)
                    if aname:
                        created_areas.append(aname)
        
        self.logger.success(f"Se crearon {len(created_areas)} áreas con orificio.")
        try:
            self.SapModel.View.RefreshView(0, False)
        except Exception:
            pass
            
        return created_areas

    def get_selected_point_coords(self):
        """
        Retorna las coordenadas (x, y, z) del primer punto seleccionado.
        Retorna None si no hay conexión o no hay puntos seleccionados.
        """
        if self.SapModel is None:
            if self._connect_to_sap() is None:
                return None
        
        # 1. Obtener objetos seleccionados
        # GetSelected(NumberItems, ObjectTypes, ObjectNames)
        try:
            ret_sel = self.SapModel.SelectObj.GetSelected(0, [], [])
            # ret_sel[-1] es RetCode
            if not check_ret_code(ret_sel): 
                return None
            
            num_items = ret_sel[0]
            if num_items == 0: 
                return None
            
            # Los arrays suelen venir en ret_sel[1] y ret_sel[2]
            obj_types = ret_sel[1]
            obj_names = ret_sel[2]
            
            point_name = None
            
            # Buscar el primer objeto de tipo 1 (PointObject)
            for i in range(num_items):
                # Asegurar que sea entero, a veces viene como int, a veces smallint
                if int(obj_types[i]) == 1:
                    point_name = obj_names[i]
                    break
            
            if not point_name:
                return None
                
            # 2. Obtener coordenadas
            # GetCoordCartesian(Name, x, y, z, CSys)
            ret_coord = self.SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0, "Global")

            if check_ret_code(ret_coord):
                # Retorna [x, y, z, RetCode]
                return {
                    "name": point_name,
                    "x": ret_coord[0],
                    "y": ret_coord[1],
                    "z": ret_coord[2]
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo selección: {e}")
            
        return None

    def get_available_tables(self):
        """
        Obtiene la lista de tablas disponibles en el modelo.
        Retorna: Lista de tuplas (TableKey, TableName)
        """
        if self.SapModel is None:
            print("Error: No hay conexión con SAP2000.")
            return []

        # GetAvailableTables(NumberTables, TableKey[], TableName[], ImportType[], RetCode)
        try:
            ret = self.SapModel.DatabaseTables.GetAvailableTables(0, [], [], [])
            
            if ret[-1] == 0:
                table_keys = ret[1]
                table_names = ret[2]
                
                tables = []
                # Validar que tengamos datos
                if table_keys and table_names:
                    count = min(len(table_keys), len(table_names))
                    for i in range(count):
                        tables.append((table_keys[i], table_names[i]))
                
                return tables
            else:
                print(f"Error obteniendo tablas disponibles, código: {ret[-1]}")
                return []
        except Exception as e:
            print(f"Excepción obteniendo tablas: {e}")
            return []

    def get_load_cases(self):
        """Obtiene lista de nombres de Casos de Carga."""
        if self.SapModel is None: return []
        try:
            # GetNameList_1(NumberNames, MyName, RetCode)
            ret = self.SapModel.LoadCases.GetNameList_1()
            if ret[-1] == 0:
                return ret[1] if ret[0] > 0 else []
        except Exception:
            pass
        return []

    def get_load_combos(self):
        """Obtiene lista de nombres de Combinaciones de Carga."""
        if self.SapModel is None: return []
        try:
            # GetNameList(NumberNames, MyName, RetCode)
            ret = self.SapModel.RespCombo.GetNameList()
            if ret[-1] == 0:
                return ret[1] if ret[0] > 0 else []
        except Exception:
            pass
        return []

    def get_table_data(self, table_key, group_name="All", load_cases=None, load_combos=None):
        """
        Obtiene los datos de una tabla específica para visualización.
        Args:
            table_key: Clave interna de la tabla.
            group_name: Grupo de objetos (default "All").
            load_cases: Lista de nombres de casos de carga a incluir.
            load_combos: Lista de nombres de combinaciones a incluir.
        Retorna: (headers, data_rows)
        """
        if self.SapModel is None:
            return None, None

        try:
            # Configurar selección de output si se especifica
            # Nota: Si se envían listas vacías, SAP podría interpretar "Ninguno" o "Todos" dependiendo la versión/función.
            # Asumiremos que si es None no tocamos la selección (o seleccionamos todo si es requerido).
            # Para tablas de resultados, usualmente se necesita AL MENOS un caso/combo.
            
            if load_cases is not None:
                # Asegurar que se pasa una lista válida o un string vacío si está vacía
                # Convertir a tupla por compatibilidad COM
                cases_arg = tuple(load_cases) if load_cases else ("",)
                ret_c = self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_arg)
                # ret_c puede ser una tupla o un entero dependiendo de la versión de comtypes/API
                code = ret_c[-1] if isinstance(ret_c, (tuple, list)) else ret_c
                if code != 0:
                     print(f"Warning: SetLoadCasesSelectedForDisplay devolvió {code}")
            
            if load_combos is not None:
                combos_arg = tuple(load_combos) if load_combos else ("",)
                ret_cb = self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay(combos_arg)
                code = ret_cb[-1] if isinstance(ret_cb, (tuple, list)) else ret_cb
                if code != 0:
                     print(f"Warning: SetLoadCombinationsSelectedForDisplay devolvió {code}")

            # GetTableForDisplayArray Returns:
            # [0] FieldKeyList (empty)
            # [1] TableVersion
            # [2] FieldKeysIncluded (Headers)
            # [3] NumberRecords
            # [4] TableData (1D array)
            # [5] RetCode
            ret = self.SapModel.DatabaseTables.GetTableForDisplayArray(table_key, [], group_name, 0, [], 0, [])

            if ret[-1] == 0:
                fields = ret[2] # Corrected from [4]
                num_records = ret[3] # Corrected from [5]
                data_flat = ret[4] # Corrected from [6]
                
                if not fields:
                     return [], []
                     
                num_fields = len(fields)
                
                if num_records == 0 or num_fields == 0:
                     return fields, []

                data_rows = []
                for i in range(num_records):
                    start_idx = i * num_fields
                    end_idx = start_idx + num_fields
                    row = data_flat[start_idx:end_idx]
                    data_rows.append(row)
                    
                return fields, data_rows
            else:
                print(f"Error obteniendo datos de tabla {table_key}, código: {ret[-1]}. Posiblemente falte seleccionar casos/combos.")
                return None, None
        except Exception as e:
             print(f"Excepción obteniendo datos de tabla {table_key}: {e}")
             return None, None

    def get_steel_materials(self):
        """Obtiene la lista de materiales de acero del modelo SAP2000."""
        if not self.SapModel:
            return []
        from sap_utils_common import get_materials_by_type
        return get_materials_by_type(self.SapModel, 1)  # 1 = Steel

    def create_frame_section(self, section_type, name, material, dims):
        """
        Crea una seccion frame en SAP2000.

        Args:
            section_type: Key from SECTION_TYPES
            name: Section name
            material: Material name (must exist in SAP model)
            dims: dict of dimension values
        Returns:
            True if successful
        """
        if not self.SapModel:
            self.logger.warning("No hay conexion con SAP2000")
            return False

        try:
            if section_type == "W":
                bf_bot = dims.get("bf_bot", 0)
                tfb = dims.get("tfb", 0)
                if bf_bot <= 0:
                    bf_bot = dims["bf"]
                if tfb <= 0:
                    tfb = dims["tf"]
                ret = self.SapModel.PropFrame.SetISection(
                    name, material, dims["d"], dims["bf"], dims["tf"], dims["tw"], bf_bot, tfb)
            elif section_type == "C":
                ret = self.SapModel.PropFrame.SetChannel(
                    name, material, dims["d"], dims["bf"], dims["tf"], dims["tw"])
            elif section_type == "L":
                ret = self.SapModel.PropFrame.SetAngle(
                    name, material, dims["d"], dims["b"], dims["t"], dims["t"])
            elif section_type == "HSS_RECT":
                ret = self.SapModel.PropFrame.SetTube(
                    name, material, dims["H"], dims["B"], dims["t"], dims["t"])
            elif section_type == "HSS_ROUND":
                ret = self.SapModel.PropFrame.SetPipe(
                    name, material, dims["OD"], dims["t"])
            elif section_type == "2L":
                ret = self.SapModel.PropFrame.SetDblAngle(
                    name, material, dims["d"], dims["b"], dims["t"], dims["t"], dims["sep"])
            elif section_type == "2C":
                ret = self.SapModel.PropFrame.SetDblChannel(
                    name, material, dims["d"], dims["bf"], dims["tf"], dims["tw"], dims["sep"])
            elif section_type == "WT":
                ret = self.SapModel.PropFrame.SetTee(
                    name, material, dims["d"], dims["bf"], dims["tf"], dims["tw"])
            else:
                self.logger.error(f"Tipo de seccion desconocido: {section_type}")
                return False

            if check_ret_code(ret):
                self.logger.success(f"Seccion '{name}' ({section_type}) creada exitosamente.")
                return True
            code = ret[-1] if isinstance(ret, (list, tuple)) else ret
            self.logger.error(f"Error creando seccion '{name}': codigo {code}")
            return False
        except Exception as e:
            self.logger.error(f"Excepcion creando seccion '{name}': {e}")
            return False
