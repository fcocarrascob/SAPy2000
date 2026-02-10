# Modelo Base

Módulo para crear un modelo SAP2000 en blanco preconfigurado con parámetros de la norma sísmica chilena **/ NCh2369**, materiales estándar, load patterns, secciones de marco, espectros de respuesta y combinaciones de diseño LRFD/ASD.

## Descripción

Automatiza los ~200+ pasos repetitivos de configuración inicial de un modelo estructural de acero. En un solo clic genera:

- **4 materiales** (A36, A500 Gr.B, G30, G25) con propiedades completas
- **12 load patterns** (DEAD, LIVE, ROOF, SNOW, EQ X/Y/Z, WIND X/Y, TEMP, SO, SA)
- **Secciones frame** (W shapes, HSS tubes, ángulos, canales)
- **Espectros NCh** horizontales (X, Y) y vertical (Z) con fórmula normativa
- **~70+ combinaciones** NCh (E1, E2, E3) + LRFD + ASD con variantes de temperatura
- **Envolventes** ENV_LRFD y ENV_ASD

## Arquitectura

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `config.py` | `SoilParameters`, constantes | Parámetros normativos NCh: suelos A–E, zonas sísmicas, materiales, combos, secciones |
| `modelo_base_backend.py` | `BaseModelBackend` | Orquestación de 7 etapas de creación vía API SAP2000 |
| `modelo_base_backend.py` | `BaseModelResult` | Dataclass con resultado: success, message, conteos, errores |
| `app_modelo_base_gui.py` | `ModeloBaseWidget` | Formulario de entrada (zona, suelo, R, ξ) + botón crear |
| `app_modelo_base_gui.py` | `SpectrumPreviewDialog` | Diálogo matplotlib con gráficos de espectros H/V |
| `app_modelo_base_gui.py` | `CreateModelWorker` | `QThread` para ejecución COM en hilo separado (`pythoncom.CoInitialize`) |

## Diagrama de Procedimiento

```mermaid
flowchart TD
    subgraph GUI["ModeloBaseWidget (PySide6)"]
        A["Usuario configura:<br/>• Zona sísmica (1/2/3)<br/>• Tipo suelo (A–E)<br/>• R_x, R_y, ξ_x, ξ_y<br/>• Parámetros verticales"]
        A2["<b>Preview Spectrum</b><br/>SpectrumPreviewDialog<br/>(matplotlib)"]
        A3["<b>Create Base Model</b><br/>→ Diálogo confirmación"]
        A4["CreateModelWorker<br/>(QThread)<br/>pythoncom.CoInitialize()"]
        A5["Barra de progreso<br/>+ resumen final"]
    end

    subgraph Backend["BaseModelBackend.create_base_model()"]
        S1["<b>Step 1:</b> Inicializar modelo"]
        S2["<b>Step 2:</b> _setup_materials()"]
        S3["<b>Step 3:</b> _setup_load_patterns()"]
        S4["<b>Step 4:</b> _setup_frame_sections()"]
        S5["<b>Step 5:</b> _setup_seismic_definitions()"]
        S6["<b>Step 6:</b> _setup_combinations()"]
        S7["<b>Step 7:</b> _create_envelopes()"]
        RES["BaseModelResult<br/>(success, message,<br/>counts, errors)"]
    end

    subgraph SAP["SAP2000 API (comtypes)"]
        S1A["InitializeNewModel()<br/>File.NewBlank()"]
        S2A["PropMaterial.SetMaterial()<br/>SetMPIsotropic()<br/>SetWeightAndMass()<br/>SetOSteel_1() / SetOConcrete_1()<br/><i>× 4 materiales</i>"]
        S3A["LoadPatterns.Add()<br/><i>× 12 patrones</i>"]
        S4A["PropFrame.SetISection()<br/>SetTube() / SetAngle()<br/>SetChannel()<br/><i>× N secciones</i>"]
        S5A["_compute_nch_spectrum()<br/>_compute_vertical_spectrum()"]
        S5B["Func.FuncRS.SetUser()<br/><i>× 3 funciones RS</i>"]
        S5C["LoadCases.ResponseSpectrum<br/>.SetCase() + .SetLoads()<br/><i>EQX, EQY, EQZ</i>"]
        S6A["RespCombo.Add()<br/>+ SetCaseList()<br/><i>NCh + LRFD + ASD</i><br/><i>~70+ combos</i>"]
        S7A["RespCombo.Add()<br/>tipo Envelope<br/>ENV_LRFD, ENV_ASD"]
    end

    A --> A2
    A --> A3 --> A4

    A4 --> S1 --> S1A
    S1A --> S2 --> S2A
    S2A --> S3 --> S3A
    S3A --> S4 --> S4A
    S4A --> S5

    S5 --> S5A
    S5A -->|"Sa = I·Ar·S·(1+r(T/T₀)ᵖ) /<br/>(1+(T/T₀)^q)·R*·(0.05/ξ)^0.4"| S5B
    S5B --> S5C
    S5C --> S6 --> S6A
    S6A --> S7 --> S7A
    S7A --> RES --> A5

    style GUI fill:#e8f4f8,stroke:#2196F3
    style Backend fill:#fff3e0,stroke:#FF9800
    style SAP fill:#fce4ec,stroke:#E91E63
```

### Detalle de las 7 etapas

| Etapa | Método | Descripción |
|---|---|---|
| 1 | `InitializeNewModel` + `NewBlank` | Crea modelo vacío en SAP2000 |
| 2 | `_setup_materials()` | A36, A500 Gr.B (acero), G30, G25 (hormigón) con E, ν, ρ, Fy/f'c |
| 3 | `_setup_load_patterns()` | 12 patrones estándar con tipo (Dead, Live, Quake, Wind, etc.) |
| 4 | `_setup_frame_sections()` | Perfiles W, HSS, ángulos y canales predefinidos |
| 5 | `_setup_seismic_definitions()` | Espectros NCh horizontales y vertical → funciones RS → load cases RS con CQC |
| 6 | `_setup_combinations()` | NCh (E1–E3 con 100/30/30%), LRFD (21 base × temp), ASD (25 base × temp) |
| 7 | `_create_envelopes()` | Envolventes finales ENV_LRFD y ENV_ASD |

### Fórmula espectral NCh2369:2025

$$S_a = \frac{I \cdot A_r \cdot S \cdot \left(1 + r\left(\frac{T}{T_0}\right)^p\right)}{\left(1 + \left(\frac{T}{T_0}\right)^q\right) \cdot R^*} \cdot \left(\frac{0.05}{\xi}\right)^{0.4}$$

El espectro vertical aplica un factor de 0.7 y un desplazamiento de período ×1.7.

## Uso en la GUI

La pestaña **"Modelo Base"** en `main_app.py` presenta:

1. **Formulario** — Zona sísmica, tipo de suelo, factores R, amortiguamientos ξ, parámetros verticales
2. **Preview Spectrum** — Diálogo con gráficos matplotlib mostrando espectros H(X), H(Y) y V + tabla de valores
3. **Create Base Model** — Confirmar → barra de progreso → resumen con conteo de elementos creados

> ⚠️ **Advertencia**: Crear un modelo base reemplaza completamente el modelo activo en SAP2000.

## Ejecución Standalone

Este módulo **no tiene** bloque `if __name__ == "__main__"` — solo es accesible vía la aplicación principal:

```bash
python main_app.py
# → Pestaña "Modelo Base"
```

## Dependencias

- `comtypes` (API SAP2000)
- `PySide6` (GUI)
- `pythoncom` (inicialización COM en thread)
- `matplotlib` + `numpy` (preview de espectros, opcional)
- `math`, `dataclasses` (cálculos y estructuras)
