"""Backend para la creación de Modelo Base en SAP2000.

Maneja la lógica de negocio para crear modelos estandarizados, incluyendo
materiales, patrones de carga y espectros de diseño NCh.
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Infrastructure imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code

# Dependiendo de cómo se ejecute, el import relativo puede fallar si no es un paquete
# Asumimos que la app corre desde el root y esto es un módulo.
from .config import (
    TON_M_UNITS, GRAVITY, AR_BY_ZONE, SOIL_PARAMS,
    LOAD_PATTERNS, DEFAULT_MATERIALS, LRFD_COMBOS, ASD_COMBOS, NCH_COMBOS,
    DEFAULT_REBARS, DEFAULT_I_SECTIONS, DEFAULT_TUBE_SECTIONS,
    DEFAULT_ANGLE_SECTIONS, DEFAULT_CHANNEL_SECTIONS
)


@dataclass
class BaseModelResult:
    """Resultado de la creación del modelo base."""
    success: bool
    message: str
    materials_created: int = 0
    patterns_created: int = 0
    functions_created: int = 0
    cases_created: int = 0
    combos_created: int = 0
    sections_created: int = 0
    rebars_created: int = 0
    errors: List[str] = field(default_factory=list)


class BaseModelBackend:
    def __init__(self, sap_model):
        self.SapModel = sap_model
        self.logger = AppLogger()

    def _ret_ok(self, ret: Any) -> bool:
        """Wrapper sobre check_ret_code centralizado."""
        return check_ret_code(ret)

    def create_base_model(
        self, 
        zone: int, 
        soil: str, 
        r_x: float, 
        r_y: float, 
        importance: float, 
        damping: float,
        damping_y: Optional[float] = None,
        xi_v: float = 0.03,
        r_v: float = 3.0,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> BaseModelResult:
        """Orquesta la creación completa del modelo base.
        
        Args:
            zone: Zona sísmica (1, 2 o 3)
            soil: Tipo de suelo (A-E)
            r_x: Factor de reducción R en dirección X
            r_y: Factor de reducción R en dirección Y
            importance: Factor de importancia I
            damping: Amortiguamiento X (ej. 0.05 para 5%)
            damping_y: Amortiguamiento Y (opcional, defaults to damping X)
            xi_v: Amortiguamiento vertical (default 0.03)
            r_v: Factor de reducción vertical (default 3.0)
            progress_callback: Función opcional para reportar progreso (percent, message)
        
        Returns:
            BaseModelResult con resumen de la creación
        """
        if damping_y is None:
            damping_y = damping

        if not self.SapModel:
            return BaseModelResult(False, "No hay conexión con SAP2000.")

        result = BaseModelResult(success=True, message="")
        
        def report(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            # 1. Start New Model
            report(5, "Inicializando modelo nuevo...")
            ret = self.SapModel.InitializeNewModel(TON_M_UNITS)
            if not self._ret_ok(ret):
                return BaseModelResult(False, f"Error al inicializar modelo nuevo. Code: {ret}")

            ret = self.SapModel.File.NewBlank()
            if not self._ret_ok(ret):
                return BaseModelResult(False, f"Error al crear archivo en blanco. Code: {ret}")
            
            # 2. Materials
            report(10, "Configurando materiales...")
            errs, mat_count = self._setup_materials()
            result.materials_created = mat_count
            if errs:
                result.errors.extend(errs)
            
            # 3. Load Patterns
            report(20, "Creando patrones de carga...")
            pat_count = self._setup_load_patterns()
            result.patterns_created = pat_count
            
            # 4. Frame Sections
            report(30, "Definiendo secciones de frame...")
            sec_count = self._setup_frame_sections()
            result.sections_created = sec_count
            
            # 5. Rebar Properties
            report(35, "Creando propiedades de armadura...")
            rebar_count = self._setup_rebars()
            result.rebars_created = rebar_count
            
            # 6. Seismic Spectrum & Cases (Horizontal + Vertical)
            report(40, "Configurando espectros sísmicos...")
            func_count, case_count = self._setup_seismic_definitions(
                zone, soil, r_x, r_y, importance, damping, damping_y, xi_v, r_v
            )
            result.functions_created = func_count
            result.cases_created = case_count
            
            # 7. Combinations (NCh, LRFD, ASD, Envelopes)
            report(60, "Creando combinaciones de carga...")
            combo_count = self._setup_combinations()
            result.combos_created = combo_count
            
            # 8. Envelopes
            report(80, "Creando envolventes...")
            self._create_envelopes()
            
            report(100, "Modelo base creado exitosamente.")
            result.message = (
                f"Modelo base creado: {result.materials_created} materiales, "
                f"{result.patterns_created} patrones, {result.sections_created} secciones, "
                f"{result.rebars_created} rebars, "
                f"{result.functions_created} funciones, {result.cases_created} casos RS, "
                f"{result.combos_created} combinaciones."
            )
            return result
            
        except Exception as e:
            logger.exception("Error crítico al crear modelo base: %s", str(e))
            return BaseModelResult(False, f"Excepción crítica: {str(e)}", errors=[str(e)])

    def _setup_materials(self) -> Tuple[List[str], int]:
        """Configura materiales acero y hormigón de forma explícita.
        
        Returns:
            Tuple de (lista de errores, cantidad de materiales creados)
        """
        if not self.SapModel:
            return ["No hay conexión con SAP2000"], 0

        errors = []
        count = 0
        for mat in DEFAULT_MATERIALS:
            name = mat["name"]
            
            # Type code from config (1=Steel, 2=Concrete)
            m_type = mat.get("mat_type_enum", 1)
            
            # 1. Definir Material (SetMaterial crea o edita)
            ret = self.SapModel.PropMaterial.SetMaterial(name, m_type)
            if not self._ret_ok(ret):
                errors.append(f"SetMaterial '{name}' failed (Code {ret})")
                continue

            # 2. Propiedades Isotrópicas (E, U, A)
            iso = mat["isotropic"]
            ret = self.SapModel.PropMaterial.SetMPIsotropic(name, iso["E"], iso["U"], iso["A"])
            if not self._ret_ok(ret):
                errors.append(f"SetMPIsotropic '{name}' failed")

            # 3. Peso y Masa
            ret = self.SapModel.PropMaterial.SetWeightAndMass(name, 1, mat["w"])
            if not self._ret_ok(ret):
                errors.append(f"SetWeightAndMass '{name}' failed")

            # 4. Propiedades de Diseño (SetOSteel_1 / SetOConcrete_1)
            if m_type == 1:  # Steel
                s = mat["steel"]
                ret = self.SapModel.PropMaterial.SetOSteel_1(
                    name, s["fy"], s["fu"], s["efy"], s["efu"],
                    s["sstype"], s["shys"], s["sh"], s["smax"], s["srup"], 0.0
                )
            elif m_type == 2:  # Concrete
                c = mat["concrete"]
                ret = self.SapModel.PropMaterial.SetOConcrete_1(
                    name, c["fc"], c["is_light"], c["fcs"],
                    c["sstype"], c["shys"], c["sfc"], c["sult"], 0.0
                )
            
            if not self._ret_ok(ret):
                errors.append(f"SetDesignProps '{name}' failed")
            else:
                count += 1

        return errors, count

    def _setup_load_patterns(self) -> int:
        """Crea patrones de carga estándar.
        
        Returns:
            Cantidad de patrones creados
        """
        if not self.SapModel:
            return 0

        count = 0
        for lp in LOAD_PATTERNS:
            # Add(Name, Type, SelfWtMult, AddLoadCase)
            ret = self.SapModel.LoadPatterns.Add(lp["name"], lp["type"], lp["self_wt"], True)
            if self._ret_ok(ret):
                count += 1
        return count

    def _setup_frame_sections(self) -> int:
        """Crea secciones de frame predeterminadas.
        
        Returns:
            Cantidad de secciones creadas
        """
        if not self.SapModel:
            return 0
        
        count = 0
        
        # I-Sections (W shapes)
        for sec in DEFAULT_I_SECTIONS:
            # SetISection(Name, MatProp, t3, t2, tf, tw, t2b, tfb, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetISection(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["tf"], sec["tw"],
                sec["t2"], sec["tf"],  # t2b, tfb (symmetric)
                -1, "", ""
            )
            if self._ret_ok(ret):
                count += 1
        
        # Tube Sections (HSS rectangular)
        for sec in DEFAULT_TUBE_SECTIONS:
            # SetTube(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetTube(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["t"], sec["t"],
                -1, "", ""
            )
            if self._ret_ok(ret):
                count += 1
        
        # Angle Sections
        for sec in DEFAULT_ANGLE_SECTIONS:
            # SetAngle(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetAngle(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["t"], sec["t"],
                -1, "", ""
            )
            if self._ret_ok(ret):
                count += 1
        
        # Channel Sections
        for sec in DEFAULT_CHANNEL_SECTIONS:
            # SetChannel(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetChannel(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["tf"], sec["tw"],
                -1, "", ""
            )
            if self._ret_ok(ret):
                count += 1
        
        return count

    def _setup_rebars(self) -> int:
        """Crea propiedades de armadura (rebar) predeterminadas.
        
        Returns:
            Cantidad de rebars creados
        """
        if not self.SapModel:
            return 0
        
        count = 0
        
        for rebar in DEFAULT_REBARS:
            # SetProp(Name, Area, Diameter)
            ret = self.SapModel.PropRebar.SetProp(
                rebar["name"],
                rebar["area"],
                rebar["diameter"]
            )
            if self._ret_ok(ret):
                count += 1
        
        return count

    def _setup_seismic_definitions(
        self, zone: int, soil: str, r_x: float, r_y: float, 
        I: float, damp_x: float, damp_y: float, xi_v: float, r_v: float
    ) -> Tuple[int, int]:
        """Calcula espectros NCh (horizontal y vertical) y define Functions + Load Cases.
        
        Returns:
            Tuple de (funciones creadas, casos creados)
        """
        if not self.SapModel:
            return 0, 0

        func_count = 0
        case_count = 0
        
        # 1. Espectros Horizontales (Corregido: Usa R real)
        # Check if identical (R and Damping)
        same_r = abs(r_x - r_y) < 1e-6
        same_damp = abs(damp_x - damp_y) < 1e-6
        use_single_spectrum = same_r and same_damp

        func_name_x = f"SaH_{zone}{soil}_R{r_x}"
        
        # Espectro X
        periods_x, accels_x = self._compute_nch_spectrum(zone, soil, I, r_x, damp_x)
        if periods_x:
            ret = self.SapModel.Func.FuncRS.SetUser(func_name_x, len(periods_x), periods_x, accels_x, damp_x)
            if self._ret_ok(ret):
                func_count += 1
                
        # Espectro Y
        if use_single_spectrum:
            func_name_y = func_name_x
        else:
            func_name_y = f"SaH_{zone}{soil}_R{r_y}"
            periods_y, accels_y = self._compute_nch_spectrum(zone, soil, I, r_y, damp_y)
            if periods_y:
                ret = self.SapModel.Func.FuncRS.SetUser(func_name_y, len(periods_y), periods_y, accels_y, damp_y)
                if self._ret_ok(ret):
                    func_count += 1
        
        # 2. Espectro Vertical
        periods_v, accels_v = self._compute_vertical_spectrum(zone, soil, I, r_v, xi_v)
        
        func_name_v = f"SaV_{zone}{soil}_R{r_v}"
        if periods_v:
            ret = self.SapModel.Func.FuncRS.SetUser(func_name_v, len(periods_v), periods_v, accels_v, xi_v)
            if self._ret_ok(ret):
                func_count += 1
        
        # 3. Load Cases para Response Spectrum
        # Scale factor = GRAVITY (el factor R ya está aplicado en el espectro tras la corrección)
        scale = GRAVITY
        
        # Horizontal cases
        if self._set_rs_case("EQX", func_name_x, "U1", scale, damp_x):
            case_count += 1
        if self._set_rs_case("EQY", func_name_y, "U2", scale, damp_y):
            case_count += 1
        
        # Vertical case (uses vertical spectrum with its own damping)
        if self._set_rs_case("EQZ", func_name_v, "U3", scale, xi_v):
            case_count += 1
        
        return func_count, case_count

    def _set_rs_case(self, case_name: str, func_name: str, dir_flag: str, scale: float, damp: float) -> bool:
        """Configura un caso de espectro de respuesta.
        
        Args:
            case_name: Nombre del Load Case (ej: EQX)
            func_name: Nombre de la función de espectro asignada
            dir_flag: Dirección (U1, U2, U3)
            scale: Factor de escala (usualmente GRAVITY 9.81)
            damp: Amortiguamiento modal constante (ej: 0.03 para 3%)
            
        Returns:
            True si se creó exitosamente
        """
        if not self.SapModel:
            return False

        try:
            # 1. Crear/Inicializar el caso como Response Spectrum
            ret = self.SapModel.LoadCases.ResponseSpectrum.SetCase(case_name)
            if not self._ret_ok(ret): return False

            # 2. Asignar las Cargas (Dirección y Función)
            # SetLoads (Name, N, LoadName, Func, SF, CSys, Ang)
            ret = self.SapModel.LoadCases.ResponseSpectrum.SetLoads(
                case_name, 1, [dir_flag], [func_name], [scale], ["Global"], [0.0]
            )
            if not self._ret_ok(ret): return False

            # 3. Asignar Amortiguamiento Modal Constante
            ret = self.SapModel.LoadCases.ResponseSpectrum.SetDampConstant(case_name, damp)
            if not self._ret_ok(ret): return False
            
            return True
        except Exception as e:
            logger.error(f"Error al configurar caso RS '{case_name}': {str(e)}")
            return False

    def _setup_combinations(self) -> int:
        """Crea Load Combinations (NCh, LRFD, ASD).
        
        Returns:
            Cantidad de combinaciones creadas
        """
        if not self.SapModel:
            return 0

        count = 0
        known_combos = set()
        
        # 1. Combos NCh (E1, E2, E3) - estos son SRSS de casos RS
        for combo_name, items in NCH_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)  # 0=Linear Add
            if self._ret_ok(ret):
                count += 1
                known_combos.add(combo_name)
                for case_name, sf in items:
                    # Items de NCH_COMBOS (RS_EQX, etc) son Load Cases (type=0)
                    ret = self.SapModel.RespCombo.SetCaseList(combo_name, 0, case_name, sf)
                    if not self._ret_ok(ret):
                        logger.warning("SetCaseList falló: combo='%s', case='%s'", combo_name, case_name)
        
        # 2. Combos LRFD
        for combo_name, items in LRFD_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)
            if not self._ret_ok(ret):
                continue
            
            count += 1
            known_combos.add(combo_name)

            for cname, sf in items:
                # Determinar si es Load Case (0) o Combo (1)
                c_type = 1 if cname in known_combos else 0
                ret = self.SapModel.RespCombo.SetCaseList(combo_name, c_type, cname, sf)
                if not self._ret_ok(ret):
                    logger.warning("SetCaseList falló: combo='%s', item='%s'", combo_name, cname)
            # Set as Design Combo
            self.SapModel.DesignSteel.SetComboStrength(combo_name, True)
            self.SapModel.DesignConcrete.SetComboStrength(combo_name, True)
        
        # 3. Combos ASD
        for combo_name, items in ASD_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)
            if not self._ret_ok(ret):
                continue
            
            count += 1
            known_combos.add(combo_name)

            for cname, sf in items:
                c_type = 1 if cname in known_combos else 0
                ret = self.SapModel.RespCombo.SetCaseList(combo_name, c_type, cname, sf)
                if not self._ret_ok(ret):
                    logger.warning("SetCaseList falló: combo='%s', item='%s'", combo_name, cname)
            
            # Set as ASD Design Combo
            self.SapModel.DesignSteel.SetComboStrength(combo_name, True)
            self.SapModel.DesignConcrete.SetComboStrength(combo_name, True)
        
        return count

    def _create_envelopes(self):
        """Crea envolventes de diseño (ENV_LRFD, ENV_ASD)."""
        if not self.SapModel:
            return

        # ENV_LRFD: Envolvente de todas las combinaciones LRFD
        lrfd_names = [name for name, _ in LRFD_COMBOS]
        if lrfd_names:
            self.SapModel.RespCombo.Add("ENV_LRFD", 1)  # 1=Envelope
            for name in lrfd_names:
                self.SapModel.RespCombo.SetCaseList("ENV_LRFD", 1, name, 1.0)
        
        # ENV_ASD: Envolvente de todas las combinaciones ASD
        asd_names = [name for name, _ in ASD_COMBOS]
        if asd_names:
            self.SapModel.RespCombo.Add("ENV_ASD", 1)  # 1=Envelope
            for name in asd_names:
                self.SapModel.RespCombo.SetCaseList("ENV_ASD", 1, name, 1.0)

    def _spectrum_shape(self, ar: float, sp, T: float, scale_factor: float = 1.0, period_shift: float = 1.0) -> float:
        """Calcula la forma espectral Sa para un período dado.
        
        Args:
            ar: Aceleración efectiva de la zona
            sp: Parámetros de suelo (SoilParams)
            T: Período estructural (s)
            scale_factor: Factor de escala (1.0 horizontal, 0.7 vertical)
            period_shift: Desplazamiento de período (1.0 horizontal, 1.7 vertical)
            
        Returns:
            Aceleración espectral (g) sin reducción R ni corrección damping
        """
        if T == 0:
            return scale_factor * ar * sp.S
        
        T_shifted = period_shift * T
        ratio = (T_shifted / sp.T0) if sp.T0 > 0 else 0.0
        num = 1.0 + sp.r * (ratio ** sp.p)
        den = 1.0 + (ratio ** sp.q)
        return scale_factor * ar * sp.S * num / den

    def _r_star(self, T: float, R: float, t1: float) -> float:
        """Calcula R* (factor de reducción corregido por período corto).
        
        NCh2369: Para períodos cortos, R se interpola linealmente 
        desde 1.5 hasta R en el rango [0, 0.16·R·T1].
        
        Args:
            T: Período estructural (s)
            R: Factor de reducción nominal
            t1: Período característico del suelo T1
            
        Returns:
            R* corregido
        """
        limit = 0.16 * R * t1
        if limit <= 0 or T >= limit:
            return R
        return 1.5 + (R - 1.5) * (T / limit)

    def _generate_spectrum(
        self, zone: int, soil: str, I: float, R: float, damp: float,
        scale_factor: float = 1.0, period_shift: float = 1.0, apply_r_star: bool = True
    ) -> Tuple[List[float], List[float]]:
        """Genera un espectro de diseño NCh2369 (horizontal o vertical).
        
        Args:
            zone: Zona sísmica (1, 2, 3)
            soil: Tipo de suelo (A-E)
            I: Factor de importancia
            R: Factor de reducción
            damp: Amortiguamiento (ej: 0.05)
            scale_factor: 1.0 para horizontal, 0.7 para vertical
            period_shift: 1.0 para horizontal, 1.7 para vertical
            apply_r_star: True para horizontal (aplica R*), False para vertical (R directo)
            
        Returns:
            Tuple de (períodos, aceleraciones) en unidades g
        """
        if zone not in AR_BY_ZONE or soil not in SOIL_PARAMS:
            return [], []

        ar = AR_BY_ZONE[zone]
        sp = SOIL_PARAMS[soil]
        
        period_limit = 5.0
        period_step = 0.01
        n_points = int(period_limit / period_step)
        
        periods = []
        accels = []
        
        damping_scale = (0.05 / damp) ** 0.4
        
        for i in range(n_points + 1):
            T = round(i * period_step, 4)
            periods.append(T)
            
            sa = self._spectrum_shape(ar, sp, T, scale_factor, period_shift)
            
            r_eff = self._r_star(T, R, sp.T1) if apply_r_star else R
            
            accel = I * sa * damping_scale / r_eff
            accels.append(accel)
        
        return periods, accels

    def _compute_nch_spectrum(
        self, zone: int, soil: str, I: float, R: float, damp: float
    ) -> Tuple[List[float], List[float]]:
        """Calcula espectro horizontal NCh2369."""
        return self._generate_spectrum(
            zone, soil, I, R, damp,
            scale_factor=1.0, period_shift=1.0, apply_r_star=True
        )

    def _compute_vertical_spectrum(
        self, zone: int, soil: str, I: float, R_v: float, xi_v: float
    ) -> Tuple[List[float], List[float]]:
        """Calcula espectro vertical NCh2369.
        
        Factor 0.7 y período desplazado 1.7×T. No aplica R*.
        """
        return self._generate_spectrum(
            zone, soil, I, R_v, xi_v,
            scale_factor=0.7, period_shift=1.7, apply_r_star=False
        )
