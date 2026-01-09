"""Configuración para el módulo de creación de Modelo Base.

Contiene constantes de materiales, patrones de carga, combinaciones
y parámetros sísmicos (NCh433/NCh2369).
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

# --- Constantes Físicas ---
TON_M_UNITS: int = 12  # Unidades Tonf-m-C
GRAVITY: float = 9.81

# --- Parámetros Sísmicos (NCh2369) ---
SeismicZone = Literal[1, 2, 3]
SoilType = Literal["A", "B", "C", "D", "E"]

@dataclass(frozen=True)
class SoilParameters:
    S: float
    r: float
    T0: float
    p: float
    q: float
    T1: float

# Aceleración efectiva (A0) referencia
AR_BY_ZONE: Dict[SeismicZone, float] = {
    1: 0.28,
    2: 0.42,
    3: 0.56,
}

# Parámetros de Suelo (Referencia)
SOIL_PARAMS: Dict[SoilType, SoilParameters] = {
    "A": SoilParameters(S=0.90, r=4.50, T0=0.15, p=1.85, q=3.00, T1=0.15),
    "B": SoilParameters(S=1.00, r=4.50, T0=0.30, p=1.60, q=3.00, T1=0.27),
    "C": SoilParameters(S=1.05, r=4.50, T0=0.40, p=1.50, q=3.00, T1=0.35),
    "D": SoilParameters(S=1.00, r=3.50, T0=0.60, p=1.00, q=2.50, T1=0.41),
    "E": SoilParameters(S=1.00, r=3.00, T0=1.20, p=1.00, q=2.70, T1=0.79),
}

# --- Patrones de Carga ---
# ELoadPatternType
ELOADTYPE: Dict[str, int] = {
    "DEAD": 1,
    "SUPERDEAD": 2,
    "LIVE": 3,
    "QUAKE": 5,
    "WIND": 6,
    "SNOW": 7,
    "OTHER": 8,
    "TEMP": 10,
    "ROOF": 11,
}

# --- Patrones de Carga ---
# ELoadPatternType: LTYPE_DEAD=1, LTYPE_SUPERDEAD=2, LTYPE_LIVE=3, LTYPE_REDUCELIVE=4, LTYPE_QUAKE=5, LTYPE_WIND=6
# LTYPE_SNOW=7, LTYPE_OTHER=8, LTYPE_MOVE=9, LTYPE_TEMP=10, LTYPE_ROOF=11
LOAD_PATTERNS = [
    {"name": "DEAD", "type": ELOADTYPE["DEAD"], "self_wt": 1.2},
    {"name": "LIVE", "type": ELOADTYPE["LIVE"], "self_wt": 0.0},
    {"name": "ROOF", "type": ELOADTYPE["ROOF"], "self_wt": 0.0},
    {"name": "SNOW", "type": ELOADTYPE["SNOW"], "self_wt": 0.0},
    {"name": "EQX", "type": ELOADTYPE["QUAKE"], "self_wt": 0.0},
    {"name": "EQY", "type": ELOADTYPE["QUAKE"], "self_wt": 0.0},
    {"name": "EQZ", "type": ELOADTYPE["QUAKE"], "self_wt": 0.0},
    {"name": "WINDX", "type": ELOADTYPE["WIND"], "self_wt": 0.0},
    {"name": "WINDY", "type": ELOADTYPE["WIND"], "self_wt": 0.0},
    {"name": "TEMP", "type": ELOADTYPE["TEMP"], "self_wt": 0.0},
    {"name": "SO", "type": ELOADTYPE["OTHER"], "self_wt": 0.0},  # Sobrecargas de operación
    {"name": "SA", "type": ELOADTYPE["OTHER"], "self_wt": 0.0},  # Sobrecargas de almacenamiento
]

# --- Materiales ---
# Copiados de _REFERENCIA con propiedades reales
DEFAULT_MATERIALS = [
    # A36
    {
        "name": "A36",
        "type": "Steel", "mat_type_enum": 1, 
        "isotropic": {"E": 20389019.0, "U": 0.30, "A": 1.17e-5},
        "w": 7.85, "m": 7.85 / GRAVITY,
        "steel": {
            "fy": 25310.0, "fu": 40778.0, "efy": 37965.0, "efu": 44855.0,
            "sstype": 1, "shys": 0, "sh": 0.015, "smax": 0.08, "srup": 0.20
        }
    },
    # A500 GrB
    {
        "name": "A500_GrB",
        "type": "Steel", "mat_type_enum": 1,
        "isotropic": {"E": 20389019.0, "U": 0.30, "A": 1.17e-5},
        "w": 7.85, "m": 7.85 / GRAVITY,
        "steel": {
            "fy": 32341.0, "fu": 40778.0, "efy": 35575.0, "efu": 44855.0,
            "sstype": 1, "shys": 0, "sh": 0.015, "smax": 0.08, "srup": 0.20
        }
    },
    # G30
    {
        "name": "G30",
        "type": "Concrete", "mat_type_enum": 2,
        "isotropic": {"E": 2641100.0, "U": 0.20, "A": 1.0e-5},
        "w": 2.50, "m": 2.40 / GRAVITY,
        "concrete": {
            "fc": 3059.0, "is_light": False, "fcs": 0.0,
            "sstype": 1, "shys": 0, "sfc": 0.002, "sult": 0.005
        }
    },
     # G25
    {
        "name": "G25",
        "type": "Concrete", "mat_type_enum": 2,
        "isotropic": {"E": 2410900.0, "U": 0.20, "A": 1.0e-5},
        "w": 2.50, "m": 2.40 / GRAVITY,
        "concrete": {
            "fc": 2549.3, "is_light": False, "fcs": 0.0,
            "sstype": 1, "shys": 0, "sfc": 0.002, "sult": 0.005
        }
    }
]

# --- Combinaciones LRFD ---
LRFD_COMBOS = [
    # Caso 1: 1.4D
    ("LRFD_1_+1.4D_+1.4T", [("DEAD", 1.4), ("TEMP", 1.4)]),
    ("LRFD_1_+1.4D_-1.4T", [("DEAD", 1.4), ("TEMP", -1.4)]),

    # Caso 2: 1.2D + 1.6L + 0.5(Lr o S o R)
    # Opcion Techo (R) domina
    ("LRFD_2_+1.2D_+1.6L_+0.5R_+1.2T", [("DEAD", 1.2), ("LIVE", 1.6), ("ROOF", 0.5), ("TEMP", 1.2)]),
    ("LRFD_2_+1.2D_+1.6L_+0.5R_-1.2T", [("DEAD", 1.2), ("LIVE", 1.6), ("ROOF", 0.5), ("TEMP", -1.2)]),
    # Opción Nieve (S) domina
    ("LRFD_2_+1.2D_+1.6L_+0.5S_+1.2T", [("DEAD", 1.2), ("LIVE", 1.6), ("SNOW", 0.5), ("TEMP", 1.2)]),
    ("LRFD_2_+1.2D_+1.6L_+0.5S_-1.2T", [("DEAD", 1.2), ("LIVE", 1.6), ("SNOW", 0.5), ("TEMP", -1.2)]),

    # Caso 3a: 1.2D + 1.6(Lr o S o R) + L
    # Opción Techo (R) domina
    ("LRFD_3R_+1.2D_+1.6R_+1.0L_+1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("LIVE", 1.0), ("TEMP", 1.2)]),
    ("LRFD_3R_+1.2D_+1.6R_+1.0L_-1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("LIVE", 1.0), ("TEMP", -1.2)]),
    # Opción Nieve (S) domina
    ("LRFD_3S_+1.2D_+1.6S_+1.0L_+1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("LIVE", 1.0), ("TEMP", 1.2)]),
    ("LRFD_3S_+1.2D_+1.6S_+1.0L_-1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("LIVE", 1.0), ("TEMP", -1.2)]),

    # Caso 3b: 1.2D + 1.6(Lr o S o R) + 0.8W
    # Opción Techo (R) domina
    ("LRFD_4R_+1.2D_+1.6R_+0.8WX_+1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("WINDX", 0.8), ("TEMP", 1.2)]),
    ("LRFD_4R_+1.2D_+1.6R_+0.8WX_-1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("WINDX", 0.8), ("TEMP", -1.2)]),
    ("LRFD_5R_+1.2D_+1.6R_+0.8WY_+1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("WINDY", 0.8), ("TEMP", 1.2)]),
    ("LRFD_5R_+1.2D_+1.6R_+0.8WY_-1.2T", [("DEAD", 1.2), ("ROOF", 1.6), ("WINDY", 0.8), ("TEMP", -1.2)]),
    # Opción Nieve (S) domina
    ("LRFD_4S_+1.2D_+1.6S_+0.8WX_+1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("WINDX", 0.8), ("TEMP", 1.2)]),
    ("LRFD_4S_+1.2D_+1.6S_+0.8WX_-1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("WINDX", 0.8), ("TEMP", -1.2)]),
    ("LRFD_5S_+1.2D_+1.6S_+0.8WY_+1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("WINDY", 0.8), ("TEMP", 1.2)]),
    ("LRFD_5S_+1.2D_+1.6S_+0.8WY_-1.2T", [("DEAD", 1.2), ("SNOW", 1.6), ("WINDY", 0.8), ("TEMP", -1.2)]),

    # Caso 4: 1.2D + 1.6W + L + 0.5(Lr o S o R)
    # Opción Techo (R) domina
    ("LRFD_6R_+1.2D_+1.6WX_+1.0L_+0.5R_+1.2T", [("DEAD", 1.2), ("WINDX", 1.6), ("LIVE", 1.0), ("ROOF", 0.5), ("TEMP", 1.2)]),
    ("LRFD_6R_+1.2D_+1.6WX_+1.0L_+0.5R_-1.2T", [("DEAD", 1.2), ("WINDX", 1.6), ("LIVE", 1.0), ("ROOF", 0.5), ("TEMP", -1.2)]),
    ("LRFD_7R_+1.2D_+1.6WY_+1.0L_+0.5R_+1.2T", [("DEAD", 1.2), ("WINDY", 1.6), ("LIVE", 1.0), ("ROOF", 0.5), ("TEMP", 1.2)]),
    ("LRFD_7R_+1.2D_+1.6WY_+1.0L_+0.5R_-1.2T", [("DEAD", 1.2), ("WINDY", 1.6), ("LIVE", 1.0), ("ROOF", 0.5), ("TEMP", -1.2)]),
    # Opción Nieve (S) domina
    ("LRFD_6S_+1.2D_+1.6WX_+1.0L_+0.5S_+1.2T", [("DEAD", 1.2), ("WINDX", 1.6), ("LIVE", 1.0), ("SNOW", 0.5), ("TEMP", 1.2)]),
    ("LRFD_6S_+1.2D_+1.6WX_+1.0L_+0.5S_-1.2T", [("DEAD", 1.2), ("WINDX", 1.6), ("LIVE", 1.0), ("SNOW", 0.5), ("TEMP", -1.2)]),
    ("LRFD_7S_+1.2D_+1.6WY_+1.0L_+0.5S_+1.2T", [("DEAD", 1.2), ("WINDY", 1.6), ("LIVE", 1.0), ("SNOW", 0.5), ("TEMP", 1.2)]),
    ("LRFD_7S_+1.2D_+1.6WY_+1.0L_+0.5S_-1.2T", [("DEAD", 1.2), ("WINDY", 1.6), ("LIVE", 1.0), ("SNOW", 0.5), ("TEMP", -1.2)]),

    # Caso 5: 1.2D + 1.4E + L + 0.2S
    ("LRFD_8_+1.2D_+1.4E1_+1.0L_+0.2S_+1.2T", [("DEAD", 1.2), ("E1", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", 1.2)]),
    ("LRFD_8_+1.2D_+1.4E1_+1.0L_+0.2S_-1.2T", [("DEAD", 1.2), ("E1", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", -1.2)]),
    ("LRFD_9_+1.2D_+1.4E2_+1.0L_+0.2S_+1.2T", [("DEAD", 1.2), ("E2", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", 1.2)]),
    ("LRFD_9_+1.2D_+1.4E2_+1.0L_+0.2S_-1.2T", [("DEAD", 1.2), ("E2", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", -1.2)]),
    ("LRFD_10_+1.2D_+1.4E3_+1.0L_+0.2S_+1.2T", [("DEAD", 1.2), ("E3", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", 1.2)]),
    ("LRFD_10_+1.2D_+1.4E3_+1.0L_+0.2S_-1.2T", [("DEAD", 1.2), ("E3", 1.4), ("LIVE", 1.0), ("SNOW", 0.2), ("TEMP", -1.2)]),

    # Caso 6: 0.9D + 1.6W
    # +WX
    ("LRFD_11+_+0.9D_+1.6WX_+0.9T", [("DEAD", 0.9), ("WINDX", 1.6), ("TEMP", 0.9)]),
    ("LRFD_11+_+0.9D_+1.6WX_-0.9T", [("DEAD", 0.9), ("WINDX", 1.6), ("TEMP", -0.9)]),
    # -WX
    ("LRFD_11-_+0.9D_-1.6WX_+0.9T", [("DEAD", 0.9), ("WINDX", -1.6), ("TEMP", 0.9)]),
    ("LRFD_11-_+0.9D_-1.6WX_-0.9T", [("DEAD", 0.9), ("WINDX", -1.6), ("TEMP", -0.9)]),
    # +WY
    ("LRFD_12+_+0.9D_+1.6WY_+0.9T", [("DEAD", 0.9), ("WINDY", 1.6), ("TEMP", 0.9)]),
    ("LRFD_12+_+0.9D_+1.6WY_-0.9T", [("DEAD", 0.9), ("WINDY", 1.6), ("TEMP", -0.9)]),
    # -WY
    ("LRFD_12-_+0.9D_-1.6WY_+0.9T", [("DEAD", 0.9), ("WINDY", -1.6), ("TEMP", 0.9)]),
    ("LRFD_12-_+0.9D_-1.6WY_-0.9T", [("DEAD", 0.9), ("WINDY", -1.6), ("TEMP", -0.9)]),

    # Caso 7: 0.9D + 1.4E
    ("LRFD_13_+0.9D_+1.4E1_+0.9T", [("DEAD", 0.9), ("E1", 1.4), ("TEMP", 0.9)]),
    ("LRFD_13_+0.9D_+1.4E1_-0.9T", [("DEAD", 0.9), ("E1", 1.4), ("TEMP", -0.9)]),
    ("LRFD_14_+0.9D_+1.4E2_+0.9T", [("DEAD", 0.9), ("E2", 1.4), ("TEMP", 0.9)]),
    ("LRFD_14_+0.9D_+1.4E2_-0.9T", [("DEAD", 0.9), ("E2", 1.4), ("TEMP", -0.9)]),
    ("LRFD_15_+0.9D_+1.4E3_+0.9T", [("DEAD", 0.9), ("E3", 1.4), ("TEMP", 0.9)]),
    ("LRFD_15_+0.9D_+1.4E3_-0.9T", [("DEAD", 0.9), ("E3", 1.4), ("TEMP", -0.9)]),

    # LRFD NCh2369:2025 Industrial con SO/SA
    # 1.2D + 0.25L + SO + SA + E
    ("LRFD_16_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E1_+1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E1", 1.0), ("TEMP", 1.2)]),
    ("LRFD_16_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E1_-1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E1", 1.0), ("TEMP", -1.2)]),
    ("LRFD_17_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E2_+1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E2", 1.0), ("TEMP", 1.2)]),
    ("LRFD_17_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E2_-1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E2", 1.0), ("TEMP", -1.2)]),
    ("LRFD_18_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E3_+1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E3", 1.0), ("TEMP", 1.2)]),
    ("LRFD_18_+1.2D_+0.25L_+1.0SO_+1.0SA_+1.0E3_-1.2T", [("DEAD", 1.2), ("LIVE", 0.25), ("SO", 1.0), ("SA", 1.0), ("E3", 1.0), ("TEMP", -1.2)]),
    # 0.9D + SA + E
    ("LRFD_19_+0.9D_+1.0SA_+1.0E1_+0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E1", 1.0), ("TEMP", 0.9)]),
    ("LRFD_19_+0.9D_+1.0SA_+1.0E1_-0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E1", 1.0), ("TEMP", -0.9)]),
    ("LRFD_20_+0.9D_+1.0SA_+1.0E2_+0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E2", 1.0), ("TEMP", 0.9)]),
    ("LRFD_20_+0.9D_+1.0SA_+1.0E2_-0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E2", 1.0), ("TEMP", -0.9)]),
    ("LRFD_21_+0.9D_+1.0SA_+1.0E3_+0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E3", 1.0), ("TEMP", 0.9)]),
    ("LRFD_21_+0.9D_+1.0SA_+1.0E3_-0.9T", [("DEAD", 0.9), ("SA", 1.0), ("E3", 1.0), ("TEMP", -0.9)]),
]

# --- Combinaciones ASD ---
ASD_COMBOS = [
    # Caso 1: 1.0D
    ("ASD_1_+1.0D_+1.0T", [("DEAD", 1.0), ("TEMP", 1.0)]),
    ("ASD_1_+1.0D_-1.0T", [("DEAD", 1.0), ("TEMP", -1.0)]),

    # Caso 2: 1.0D + 1.0L
    ("ASD_2_+1.0D_+1.0L_+1.0T", [("DEAD", 1.0), ("LIVE", 1.0), ("TEMP", 1.0)]),
    ("ASD_2_+1.0D_+1.0L_-1.0T", [("DEAD", 1.0), ("LIVE", 1.0), ("TEMP", -1.0)]),

    #Caso 3: 1.0D + (Lr o S o R)
    # Opción Techo (R) domina
    ("ASD_3R_+1.0D_+1.0R_+1.0T", [("DEAD", 1.0), ("ROOF", 1.0), ("TEMP", 1.0)]),
    ("ASD_3R_+1.0D_+1.0R_-1.0T", [("DEAD", 1.0), ("ROOF", 1.0), ("TEMP", -1.0)]),
    # Opción Nieve (S) domina
    ("ASD_3S_+1.0D_+1.0S_+1.0T", [("DEAD", 1.0), ("SNOW", 1.0), ("TEMP", 1.0)]),
    ("ASD_3S_+1.0D_+1.0S_-1.0T", [("DEAD", 1.0), ("SNOW", 1.0), ("TEMP", -1.0)]),

    # Caso 4: 1.0D + 0.75L + 0.75(Lr o S o R)
    # Opción Techo (R) domina
    ("ASD_4R_+1.0D_+0.75L_+0.75R_+1.0T", [("DEAD", 1.0), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", 1.0)]),
    ("ASD_4R_+1.0D_+0.75L_+0.75R_-1.0T", [("DEAD", 1.0), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", -1.0)]),
    # Opción Nieve (S) domina
    ("ASD_4S_+1.0D_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_4S_+1.0D_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),

    # Caso 5a: 1.0D + 1.0W
    # +WX
    ("ASD_5+_+1.0D_+1.0WX_+1.0T", [("DEAD", 1.0), ("WINDX", 1.0), ("TEMP", 1.0)]),
    ("ASD_5+_+1.0D_+1.0WX_-1.0T", [("DEAD", 1.0), ("WINDX", 1.0), ("TEMP", -1.0)]),
    # -WX
    ("ASD_5-_+1.0D_-1.0WX_+1.0T", [("DEAD", 1.0), ("WINDX", -1.0), ("TEMP", 1.0)]),
    ("ASD_5-_+1.0D_-1.0WX_-1.0T", [("DEAD", 1.0), ("WINDX", -1.0), ("TEMP", -1.0)]),
    # +WY
    ("ASD_6+_+1.0D_+1.0WY_+1.0T", [("DEAD", 1.0), ("WINDY", 1.0), ("TEMP", 1.0)]),
    ("ASD_6+_+1.0D_+1.0WY_-1.0T", [("DEAD", 1.0), ("WINDY", 1.0), ("TEMP", -1.0)]),
    # -WY
    ("ASD_6-_+1.0D_-1.0WY_+1.0T", [("DEAD", 1.0), ("WINDY", -1.0), ("TEMP", 1.0)]),
    ("ASD_6-_+1.0D_-1.0WY_-1.0T", [("DEAD", 1.0), ("WINDY", -1.0), ("TEMP", -1.0)]),

    # Caso 5b: 1.0D + 1.0E
    ("ASD_7_+1.0D_+1.0E1_+1.0T", [("DEAD", 1.0), ("E1", 1.0), ("TEMP", 1.0)]),
    ("ASD_7_+1.0D_+1.0E1_-1.0T", [("DEAD", 1.0), ("E1", 1.0), ("TEMP", -1.0)]),
    ("ASD_8_+1.0D_+1.0E2_+1.0T", [("DEAD", 1.0), ("E2", 1.0), ("TEMP", 1.0)]),
    ("ASD_8_+1.0D_+1.0E2_-1.0T", [("DEAD", 1.0), ("E2", 1.0), ("TEMP", -1.0)]),
    ("ASD_9_+1.0D_+1.0E3_+1.0T", [("DEAD", 1.0), ("E3", 1.0), ("TEMP", 1.0)]),
    ("ASD_9_+1.0D_+1.0E3_-1.0T", [("DEAD", 1.0), ("E3", 1.0), ("TEMP", -1.0)]),

    # Caso 6a: 1.0D + 0.75W + 0.75L + 0.75(Lr o S o R)
    # Opción Techo (R) domina
    # +WX
    ("ASD_10R+_+1.0D_+0.75WX_+0.75L_+0.75R_+1.0T", [("DEAD", 1.0), ("WINDX", 0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", 1.0)]),
    ("ASD_10R+_+1.0D_+0.75WX_+0.75L_+0.75R_-1.0T", [("DEAD", 1.0), ("WINDX", 0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", -1.0)]),
    # -WX
    ("ASD_10R-_+1.0D_-0.75WX_+0.75L_+0.75R_+1.0T", [("DEAD", 1.0), ("WINDX", -0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", 1.0)]),
    ("ASD_10R-_+1.0D_-0.75WX_+0.75L_+0.75R_-1.0T", [("DEAD", 1.0), ("WINDX", -0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", -1.0)]),
    # +WY
    ("ASD_11R+_+1.0D_+0.75WY_+0.75L_+0.75R_+1.0T", [("DEAD", 1.0), ("WINDY", 0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", 1.0)]),
    ("ASD_11R+_+1.0D_+0.75WY_+0.75L_+0.75R_-1.0T", [("DEAD", 1.0), ("WINDY", 0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", -1.0)]),
    # -WY
    ("ASD_11R-_+1.0D_-0.75WY_+0.75L_+0.75R_+1.0T", [("DEAD", 1.0), ("WINDY", -0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", 1.0)]),
    ("ASD_11R-_+1.0D_-0.75WY_+0.75L_+0.75R_-1.0T", [("DEAD", 1.0), ("WINDY", -0.75), ("LIVE", 0.75), ("ROOF", 0.75), ("TEMP", -1.0)]),

    # Opción Nieve (S) domina
    # +WX
    ("ASD_10S+_+1.0D_+0.75WX_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("WINDX", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_10S+_+1.0D_+0.75WX_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("WINDX", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    # -WX
    ("ASD_10S-_+1.0D_-0.75WX_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("WINDX", -0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_10S-_+1.0D_-0.75WX_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("WINDX", -0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    # +WY
    ("ASD_11S+_+1.0D_+0.75WY_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("WINDY", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_11S+_+1.0D_+0.75WY_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("WINDY", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    # -WY
    ("ASD_11S-_+1.0D_-0.75WY_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("WINDY", -0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_11S-_+1.0D_-0.75WY_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("WINDY", -0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),

    # Caso 6b: 1.0D + 0.75E + 0.75L + 0.75S
    ("ASD_12_+1.0D_+0.75E1_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("E1", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_12_+1.0D_+0.75E1_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("E1", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    ("ASD_13_+1.0D_+0.75E2_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("E2", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_13_+1.0D_+0.75E2_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("E2", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    ("ASD_14_+1.0D_+0.75E3_+0.75L_+0.75S_+1.0T", [("DEAD", 1.0), ("E3", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", 1.0)]),
    ("ASD_14_+1.0D_+0.75E3_+0.75L_+0.75S_-1.0T", [("DEAD", 1.0), ("E3", 0.75), ("LIVE", 0.75), ("SNOW", 0.75), ("TEMP", -1.0)]),
    
    # Caso 7: 0.6D + 1.0W
    # +WX
    ("ASD_15+_+0.6D_+1.0WX_+0.6T", [("DEAD", 0.6), ("WINDX", 1.0), ("TEMP", 0.6)]),
    ("ASD_15+_+0.6D_+1.0WX_-0.6T", [("DEAD", 0.6), ("WINDX", 1.0), ("TEMP", -0.6)]),
    # -WX
    ("ASD_15-_+0.6D_-1.0WX_+0.6T", [("DEAD", 0.6), ("WINDX", -1.0), ("TEMP", 0.6)]),
    ("ASD_15-_+0.6D_-1.0WX_-0.6T", [("DEAD", 0.6), ("WINDX", -1.0), ("TEMP", -0.6)]),
    # +WY
    ("ASD_16+_+0.6D_+1.0WY_+0.6T", [("DEAD", 0.6), ("WINDY", 1.0), ("TEMP", 0.6)]),
    ("ASD_16+_+0.6D_+1.0WY_-0.6T", [("DEAD", 0.6), ("WINDY", 1.0), ("TEMP", -0.6)]),
    # -WY
    ("ASD_16-_+0.6D_-1.0WY_+0.6T", [("DEAD", 0.6), ("WINDY", -1.0), ("TEMP", 0.6)]),
    ("ASD_16-_+0.6D_-1.0WY_-0.6T", [("DEAD", 0.6), ("WINDY", -1.0), ("TEMP", -0.6)]),

    # Caso 8: 0.6D + 1.0E
    ("ASD_17_+0.6D_+1.0E1_+0.6T", [("DEAD", 0.6), ("E1", 1.0), ("TEMP", 0.6)]),
    ("ASD_17_+0.6D_+1.0E1_-0.6T", [("DEAD", 0.6), ("E1", 1.0), ("TEMP", -0.6)]),
    ("ASD_18_+0.6D_+1.0E2_+0.6T", [("DEAD", 0.6), ("E2", 1.0), ("TEMP", 0.6)]),
    ("ASD_18_+0.6D_+1.0E2_-0.6T", [("DEAD", 0.6), ("E2", 1.0), ("TEMP", -0.6)]),
    ("ASD_19_+0.6D_+1.0E3_+0.6T", [("DEAD", 0.6), ("E3", 1.0), ("TEMP", 0.6)]),
    ("ASD_19_+0.6D_+1.0E3_-0.6T", [("DEAD", 0.6), ("E3", 1.0), ("TEMP", -0.6)]),

    # ASD NCh2369:2025 Industrial con SO/SA
    # D + 0.25*0.75L + 0.75SO + 0.75SA + 0.7E
    ("ASD_20_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E1_+1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E1", 0.7), ("TEMP", 1.0)]),
    ("ASD_20_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E1_-1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E1", 0.7), ("TEMP", -1.0)]),
    ("ASD_21_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E2_+1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E2", 0.7), ("TEMP", 1.0)]),
    ("ASD_21_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E2_-1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E2", 0.7), ("TEMP", -1.0)]),
    ("ASD_22_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E3_+1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E3", 0.7), ("TEMP", 1.0)]),
    ("ASD_22_+1.0D_+0.25*0.75L_+0.75SO_+0.75SA_+0.7E3_-1.0T", [("DEAD", 1.0), ("LIVE", 0.25*0.75), ("SO", 0.75), ("SA", 0.75), ("E3", 0.7), ("TEMP", -1.0)]),
    # 1.0D + 0.75SA + 0.7E
    ("ASD_23_+1.0D_+0.75SA_+0.7E1_+1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E1", 0.7), ("TEMP", 1.0)]),
    ("ASD_23_+1.0D_+0.75SA_+0.7E1_-1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E1", 0.7), ("TEMP", -1.0)]),
    ("ASD_24_+1.0D_+0.75SA_+0.7E2_+1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E2", 0.7), ("TEMP", 1.0)]),
    ("ASD_24_+1.0D_+0.75SA_+0.7E2_-1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E2", 0.7), ("TEMP", -1.0)]),
    ("ASD_25_+1.0D_+0.75SA_+0.7E3_+1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E3", 0.7), ("TEMP", 1.0)]),
    ("ASD_25_+1.0D_+0.75SA_+0.7E3_-1.0T", [("DEAD", 1.0), ("SA", 0.75), ("E3", 0.7), ("TEMP", -1.0)]),
]

NCH_COMBOS = [
    ("E1", [("EQX", 1.0), ("EQY", 0.3), ("EQZ", 0.3)]),
    ("E2", [("EQX", 0.3), ("EQY", 1.0), ("EQZ", 0.3)]),
    ("E3", [("EQX", 0.3), ("EQY", 0.3), ("EQZ", 1.0)]),
]

# --- Secciones de Frame ---
# Armaduras de refuerzo (barras de acero)
DEFAULT_REBARS = [
    {"name": "Rebar_φ6", "area": 0.000028, "diameter": 0.006, "material": "A36"},
    {"name": "Rebar_φ8", "area": 0.000050, "diameter": 0.008, "material": "A36"},
    {"name": "Rebar_φ10", "area": 0.000079, "diameter": 0.010, "material": "A36"},
    {"name": "Rebar_φ12", "area": 0.000113, "diameter": 0.012, "material": "A36"},
]

# Perfiles I (W shapes)
DEFAULT_I_SECTIONS = [
    {"name": "W200x46", "t3": 0.203, "t2": 0.203, "tf": 0.011, "tw": 0.007, "material": "A36"},
    {"name": "W310x97", "t3": 0.308, "t2": 0.305, "tf": 0.015, "tw": 0.009, "material": "A36"},
]

# Tubos rectangulares (HSS)
DEFAULT_TUBE_SECTIONS = [
    {"name": "HSS100x100x6", "t3": 0.100, "t2": 0.100, "t": 0.006, "material": "A500_GrB"},
    {"name": "HSS150x150x8", "t3": 0.150, "t2": 0.150, "t": 0.008, "material": "A500_GrB"},
]

# Ángulos
DEFAULT_ANGLE_SECTIONS = [
    {"name": "L50x50x5", "t3": 0.050, "t2": 0.050, "t": 0.005, "material": "A36"},
    {"name": "L75x75x6", "t3": 0.075, "t2": 0.075, "t": 0.006, "material": "A36"},
]

# Canales
DEFAULT_CHANNEL_SECTIONS = [
    {"name": "C100x10", "t3": 0.100, "t2": 0.050, "tf": 0.009, "tw": 0.006, "material": "A36"},
    {"name": "C150x15", "t3": 0.150, "t2": 0.075, "tf": 0.011, "tw": 0.007, "material": "A36"},
]
