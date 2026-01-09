"""Backend para la creación de Modelo Base en SAP2000.

Maneja la lógica de negocio para crear modelos estandarizados, incluyendo
materiales, patrones de carga y espectros de diseño NCh.
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional, Callable

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
    errors: List[str] = field(default_factory=list)


class BaseModelBackend:
    def __init__(self, sap_model):
        self.SapModel = sap_model

    def create_base_model(
        self, 
        zone: int, 
        soil: str, 
        r_x: float, 
        r_y: float, 
        importance: float, 
        damping: float,
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
            damping: Amortiguamiento (ej. 0.05 para 5%)
            xi_v: Amortiguamiento vertical (default 0.03)
            r_v: Factor de reducción vertical (default 3.0)
            progress_callback: Función opcional para reportar progreso (percent, message)
        
        Returns:
            BaseModelResult con resumen de la creación
        """
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
            if ret != 0:
                return BaseModelResult(False, f"Error al inicializar modelo nuevo. Code: {ret}")

            ret = self.SapModel.File.NewBlank()
            if ret != 0:
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
            
            # 5. Seismic Spectrum & Cases (Horizontal + Vertical)
            report(40, "Configurando espectros sísmicos...")
            func_count, case_count = self._setup_seismic_definitions(
                zone, soil, r_x, r_y, importance, damping, xi_v, r_v
            )
            result.functions_created = func_count
            result.cases_created = case_count
            
            # 6. Combinations (NCh, LRFD, ASD, Envelopes)
            report(60, "Creando combinaciones de carga...")
            combo_count = self._setup_combinations()
            result.combos_created = combo_count
            
            # 7. Envelopes
            report(80, "Creando envolventes...")
            self._create_envelopes()
            
            report(100, "Modelo base creado exitosamente.")
            result.message = (
                f"Modelo base creado: {result.materials_created} materiales, "
                f"{result.patterns_created} patrones, {result.sections_created} secciones, "
                f"{result.functions_created} funciones, {result.cases_created} casos RS, "
                f"{result.combos_created} combinaciones."
            )
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return BaseModelResult(False, f"Excepción crítica: {str(e)}", errors=[str(e)])

    def _setup_materials(self) -> Tuple[List[str], int]:
        """Configura materiales acero y hormigón de forma explícita.
        
        Returns:
            Tuple de (lista de errores, cantidad de materiales creados)
        """
        errors = []
        count = 0
        for mat in DEFAULT_MATERIALS:
            name = mat["name"]
            
            # Type code from config (1=Steel, 2=Concrete)
            m_type = mat.get("mat_type_enum", 1)
            
            # 1. Definir Material (SetMaterial crea o edita)
            ret = self.SapModel.PropMaterial.SetMaterial(name, m_type)
            if ret != 0:
                errors.append(f"SetMaterial '{name}' failed (Code {ret})")
                continue

            # 2. Propiedades Isotrópicas (E, U, A)
            iso = mat["isotropic"]
            ret = self.SapModel.PropMaterial.SetMPIsotropic(name, iso["E"], iso["U"], iso["A"])
            if ret != 0:
                errors.append(f"SetMPIsotropic '{name}' failed")

            # 3. Peso y Masa
            ret = self.SapModel.PropMaterial.SetWeightAndMass(name, 1, mat["w"])
            if ret != 0:
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
            
            if ret != 0:
                errors.append(f"SetDesignProps '{name}' failed")
            else:
                count += 1

        return errors, count

    def _setup_load_patterns(self) -> int:
        """Crea patrones de carga estándar.
        
        Returns:
            Cantidad de patrones creados
        """
        count = 0
        for lp in LOAD_PATTERNS:
            # Add(Name, Type, SelfWtMult, AddLoadCase)
            ret = self.SapModel.LoadPatterns.Add(lp["name"], lp["type"], lp["self_wt"], True)
            if ret == 0:
                count += 1
        return count

    def _setup_frame_sections(self) -> int:
        """Crea secciones de frame predeterminadas.
        
        Returns:
            Cantidad de secciones creadas
        """
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
            if ret == 0:
                count += 1
        
        # Tube Sections (HSS rectangular)
        for sec in DEFAULT_TUBE_SECTIONS:
            # SetTube(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetTube(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["t"], sec["t"],
                -1, "", ""
            )
            if ret == 0:
                count += 1
        
        # Angle Sections
        for sec in DEFAULT_ANGLE_SECTIONS:
            # SetAngle(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetAngle(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["t"], sec["t"],
                -1, "", ""
            )
            if ret == 0:
                count += 1
        
        # Channel Sections
        for sec in DEFAULT_CHANNEL_SECTIONS:
            # SetChannel(Name, MatProp, t3, t2, tf, tw, Color, Notes, GUID)
            ret = self.SapModel.PropFrame.SetChannel(
                sec["name"], sec["material"],
                sec["t3"], sec["t2"], sec["tf"], sec["tw"],
                -1, "", ""
            )
            if ret == 0:
                count += 1
        
        return count

    def _setup_seismic_definitions(
        self, zone: int, soil: str, r_x: float, r_y: float, 
        I: float, damp: float, xi_v: float, r_v: float
    ) -> Tuple[int, int]:
        """Calcula espectros NCh (horizontal y vertical) y define Functions + Load Cases.
        
        Returns:
            Tuple de (funciones creadas, casos creados)
        """
        func_count = 0
        case_count = 0
        
        # 1. Espectro Horizontal
        periods_h, accels_h = self._compute_nch_spectrum(zone, soil, I, 1.0, damp)
        
        func_name_h = "NCh_Design_Spectrum_H"
        if periods_h:
            ret = self.SapModel.Func.FuncRS.SetUser(func_name_h, len(periods_h), periods_h, accels_h, damp)
            rc = ret[-1] if isinstance(ret, (list, tuple)) else ret
            if rc == 0:
                func_count += 1
        
        # 2. Espectro Vertical
        periods_v, accels_v = self._compute_vertical_spectrum(zone, soil, I, r_v, xi_v)
        
        func_name_v = "NCh_Design_Spectrum_V"
        if periods_v:
            ret = self.SapModel.Func.FuncRS.SetUser(func_name_v, len(periods_v), periods_v, accels_v, xi_v)
            rc = ret[-1] if isinstance(ret, (list, tuple)) else ret
            if rc == 0:
                func_count += 1
        
        # 3. Load Cases para Response Spectrum
        # Scale factor = GRAVITY (el factor R ya está aplicado en el espectro)
        scale = GRAVITY
        
        # Horizontal cases
        if self._set_rs_case("EQX", func_name_h, "U1", scale, damp):
            case_count += 1
        if self._set_rs_case("EQY", func_name_h, "U2", scale, damp):
            case_count += 1
        
        # Vertical case (uses vertical spectrum with its own damping)
        if self._set_rs_case("EQZ", func_name_v, "U3", scale, xi_v):
            case_count += 1
        
        return func_count, case_count

    def _set_rs_case(self, case_name: str, func_name: str, dir_flag: str, scale: float, damp: float) -> bool:
        """Configura un caso de espectro de respuesta.
        
        Returns:
            True si se creó exitosamente
        """
        try:
            self.SapModel.LoadCases.ResponseSpectrum.SetCase(case_name)
            
            # SetLoads (Name, N, LoadName, Func, SF, CSys, Ang)
            self.SapModel.LoadCases.ResponseSpectrum.SetLoads(
                case_name, 1, [dir_flag], [func_name], [scale], ["Global"], [0.0]
            )
            
            # SetDamping
            self.SapModel.LoadCases.ResponseSpectrum.SetDampingConstant(case_name, damp)
            
            return True
        except Exception:
            return False

    def _setup_combinations(self) -> int:
        """Crea Load Combinations (NCh, LRFD, ASD).
        
        Returns:
            Cantidad de combinaciones creadas
        """
        count = 0
        known_combos = set()
        
        # 1. Combos NCh (E1, E2, E3) - estos son SRSS de casos RS
        for combo_name, items in NCH_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)  # 0=Linear Add
            if ret == 0:
                count += 1
                known_combos.add(combo_name)
                for case_name, sf in items:
                    # Items de NCH_COMBOS (RS_EQX, etc) son Load Cases (type=0)
                    self.SapModel.RespCombo.SetCaseList(combo_name, 0, case_name, sf)
        
        # 2. Combos LRFD
        for combo_name, items in LRFD_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)
            if ret != 0:
                continue
            
            count += 1
            known_combos.add(combo_name)

            for cname, sf in items:
                # Determinar si es Load Case (0) o Combo (1)
                c_type = 1 if cname in known_combos else 0
                self.SapModel.RespCombo.SetCaseList(combo_name, c_type, cname, sf)
            
            # Set as Design Combo
            self.SapModel.DesignSteel.SetComboStrength(combo_name, True)
            self.SapModel.DesignConcrete.SetComboStrength(combo_name, True)
        
        # 3. Combos ASD
        for combo_name, items in ASD_COMBOS:
            ret = self.SapModel.RespCombo.Add(combo_name, 0)
            if ret != 0:
                continue
            
            count += 1
            known_combos.add(combo_name)

            for cname, sf in items:
                c_type = 1 if cname in known_combos else 0
                self.SapModel.RespCombo.SetCaseList(combo_name, c_type, cname, sf)
            
            # Set as ASD Design Combo
            self.SapModel.DesignSteel.SetComboStrength(combo_name, True)
            self.SapModel.DesignConcrete.SetComboStrength(combo_name, True)
        
        return count

    def _create_envelopes(self):
        """Crea envolventes de diseño (ENV_LRFD, ENV_ASD)."""
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

    def _compute_nch_spectrum(self, zone: int, soil: str, I: float, R: float, damp: float) -> Tuple[List[float], List[float]]:
        """Calcula Sa (g) vs T (s) basado en lógica NCh de referencia."""
        if zone not in AR_BY_ZONE or soil not in SOIL_PARAMS:
            return [], []

        ar = AR_BY_ZONE[zone]
        sp = SOIL_PARAMS[soil]
        
        # Parámetros (Reference logic adapted)
        # config.py has: S, r, T0, p, q, T1
        s, r, t0, p_exp, q_exp, t1 = sp.S, sp.r, sp.T0, sp.p, sp.q, sp.T1
        
        # Ticks (mayor resolución como en referencia)
        period_limit = 5.0
        period_step = 0.01
        count = int(period_limit / period_step)
        
        periods = []
        accels = []
        
        # Correction for damping
        damping_scale = (0.05 / damp) ** 0.4
        
        for i in range(count + 1):
            T = i * period_step
            periods.append(T)
            
            # Spectrum Shape
            ratio = (T / t0) if t0 > 0 else 0
            # From reference:
            # numerator = 1.0 + r * math.pow(ratio, p_exp)
            # denominator = 1.0 + math.pow(ratio, q_exp)
            # sah = ar * s * numerator / denominator
            
            if T == 0:
                 sah = ar * s # ratio=0 -> num=1, den=1
            else:
                 num = 1.0 + r * (ratio ** p_exp)
                 den = 1.0 + (ratio ** q_exp)
                 sah = ar * s * num / den
            
            # R* Calculation (Short period reduction)
            # If R given is the "Response Modification Factor" (e.g. 5, 7)
            
            # Reference:
            # cr = 0.16 * response_modification_factor
            # limit = cr * t1
            # ...
            
            # Using passed R as response_modification_factor
            cr = 0.16 * R
            limit = cr * t1
            
            if limit <= 0:
                r_star = R
            elif T >= limit:
                r_star = R
            else:
                # Linear interpolation ??
                # ratio_t = period / limit
                # r_star = 1.5 + (R - 1.5) * ratio_t
                ratio_t = T / limit
                r_star = 1.5 + (R - 1.5) * ratio_t
            
            # Final Accel
            accel = I * sah * damping_scale / r_star
            accels.append(accel)
            
        return periods, accels

    def _compute_vertical_spectrum(
        self, zone: int, soil: str, I: float, R_v: float, xi_v: float
    ) -> Tuple[List[float], List[float]]:
        """Calcula espectro vertical NCh2369.
        
        La fórmula del espectro vertical usa un período desplazado (1.7×T)
        y un factor de escala de 0.7 respecto al horizontal.
        
        Fórmula: Sa_v = 0.7 × Ar × S × (1 + r × (1.7T/T0)^p) / (1 + (1.7T/T0)^q)
        
        Args:
            zone: Zona sísmica (1, 2 o 3)
            soil: Tipo de suelo (A-E)
            I: Factor de importancia
            R_v: Factor de reducción vertical
            xi_v: Amortiguamiento vertical
            
        Returns:
            Tuple de (períodos, aceleraciones) en unidades g
        """
        if zone not in AR_BY_ZONE or soil not in SOIL_PARAMS:
            return [], []

        ar = AR_BY_ZONE[zone]
        sp = SOIL_PARAMS[soil]
        
        s, r, t0, p_exp, q_exp, t1 = sp.S, sp.r, sp.T0, sp.p, sp.q, sp.T1
        
        # Ticks (mayor resolución como en referencia)
        period_limit = 5.0
        period_step = 0.01
        count = int(period_limit / period_step)
        
        periods = []
        accels = []
        
        # Corrección por amortiguamiento
        damping_scale = (0.05 / xi_v) ** 0.4
        
        # Factor de escala vertical (NCh2369)
        vertical_factor = 0.7
        
        # Desplazamiento de período para espectro vertical
        period_shift = 1.7
        
        for i in range(count + 1):
            T = i * period_step
            periods.append(T)
            
            # Período desplazado para el espectro vertical
            T_shifted = period_shift * T
            
            # Spectrum Shape con período desplazado
            ratio = (T_shifted / t0) if t0 > 0 else 0
            
            if T == 0:
                sav = vertical_factor * ar * s
            else:
                num = 1.0 + r * (ratio ** p_exp)
                den = 1.0 + (ratio ** q_exp)
                sav = vertical_factor * ar * s * num / den
            
            # Espectro vertical NO aplica R* (usa R_v directo como en referencia)
            accel = I * sav * damping_scale / R_v
            accels.append(accel)
            
        return periods, accels
