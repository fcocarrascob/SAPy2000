# Herramientas de Automatización para SAP2000

Este proyecto proporciona un conjunto de herramientas en Python para automatizar tareas en CSI SAP2000 utilizando la OAPI (Open Application Programming Interface) a través de la librería `comtypes`. La aplicación está estructurada en módulos independientes con interfaces gráficas de usuario (GUI) construidas con PySide6.

## Estructura del Proyecto

El proyecto está organizado en componentes modulares, cada uno abordando flujos de trabajo de ingeniería específicos:

### 1. Gestor de Combinaciones de Carga (`Combinations_Carga`)
Una interfaz tipo Excel para gestionar combinaciones de carga de manera eficiente.
- **Funcionalidad**:
    - Leer casos de carga y combinaciones existentes del modelo activo de SAP2000.
    - Agregar, modificar o eliminar combinaciones utilizando una vista de cuadrícula.
    - Soporte para diferentes tipos de combinación (Aditiva Lineal, Envolvente, etc.).
    - Selección del tipo de diseño (ASD/LRFD).
    - Lógica de actualización robusta ("Upsert") para modificar combinaciones sin romper dependencias del modelo.
- **Punto de Entrada**: `Combinations_Carga/app_combos_gui.py`

### 2. Utilidades de Mallado (`Utilidades_MOD`)
Herramientas para generar y modificar mallas de elementos finitos.
- **Funcionalidad**:
    - **Malla Rectangular**: Generar elementos de área rectangulares con subdivisiones específicas.
    - **Generación de Huecos**: Crear aberturas circulares dentro de elementos de área existentes.
    - **Vista Previa**: Visualización en tiempo real de la geometría antes de enviarla a SAP2000.
- **Punto de Entrada**: `Utilidades_MOD/app_utils_gui.py`

### 3. Análisis de Placa Base (`Placa_Base`)
Módulo dedicado al análisis y diseño de placas base.
- **Punto de Entrada**: `Placa_Base/app_placabase_gui.py`

## Requisitos

- **Software**: CSI SAP2000.
- **Python**: Versión 3.13 o compatible.
- **Librerías**:
    - `comtypes`: Para la comunicación de interfaz COM con SAP2000.
    - `PySide6`: Para la Interfaz Gráfica de Usuario.

## Uso

1. Abra SAP2000 y cargue su modelo.
2. Ejecute el script del módulo deseado usando Python.
3. La GUI intentará conectarse a la instancia activa de SAP2000.

Ejemplo:
```bash
python Combinations_Carga/app_combos_gui.py
```

## Arquitectura

El proyecto sigue un patrón modular separando la interfaz de la lógica:
- **GUI (*_gui.py)**: Maneja la interacción del usuario y la visualización usando PySide6.
- **Backend (*_backend.py)**: Gestiona la lógica y la comunicación directa con la API de SAP2000.

## Interacción con la API

- La interacción se basa en `comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")`.
- El manejo de parámetros está ajustado específicamente para el comportamiento de `comtypes` en Python, particularmente con respecto a los valores de retorno `ByRef` que se devuelven como tuplas.
