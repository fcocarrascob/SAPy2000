# Herramientas de Automatización para SAP2000

Este proyecto proporciona un conjunto de herramientas en Python para automatizar tareas en CSI SAP2000 utilizando la OAPI (Open Application Programming Interface) a través de la librería `comtypes`. La aplicación sigue una arquitectura modular y unificada, integrando múltiples herramientas en una sola interfaz gráfica con pestañas.

## Características Principales

*   **Aplicación Unificada**: Una sola ventana (`main_app.py`) que gestiona todas las herramientas.
*   **Conexión Centralizada**: Gestión eficiente de la conexión a SAP2000 (OAPI) compartida entre todos los módulos.
*   **Arquitectura Modular**: Fácil escalabilidad para añadir nuevas funcionalidades sin afectar las existentes.

## Componentes del Sistema

### 1. Aplicación Principal (`main_app.py`)
El punto de entrada de la aplicación. Gestiona la barra de herramientas, la conexión global a SAP2000 y aloja las interfaces de los módulos en pestañas.

### 2. Gestor de Combinaciones de Carga (`Combinations_Carga`)
Interfaz tipo Excel para gestionar combinaciones de carga.
- Lectura y escritura de combinaciones ("Upsert").
- Soporte para ASD/LRFD y tipos de combinación (Lineal, Envolvente).
- Visualización en cuadrícula.

### 3. Utilidades de Mallado (`Utilidades_MOD`)
Herramientas avanzadas de geometría y mallado.
- Generación de mallas rectangulares.
- Creación de huecos circulares en elementos de área.
- Vista previa en tiempo real.

### 4. Diseño de Placa Base (`Placa_Base`)
Módulo específico para el modelado y generación de geometrías de placas base, pernos y rigidizadores.

### 5. Generador de Memorias y Reportes (`Reportes`)
Sistema avanzado para la generación automática de memorias de cálculo en Microsoft Word.
- **Asistente en Vivo**: Inyecta tablas de datos de SAP2000 (Materiales, Cargas, Secciones) directamente en la posición del cursor de Word.
- **Generación por Templates**: Crea documentos completos basándose en plantillas JSON personalizables.
- **Librería de Contenido**: Inserción rápida de bloques de texto estándar (e.g., descripciones de carga) y **ecuaciones matemáticas** renderizadas nativamente en Word.

## Requisitos

- **Software**: CSI SAP2000 (v20+ recomendado) y **Microsoft Word**.
- **Python**: 3.13+.
- **Librerías**:
    - `comtypes`: Interfaz COM (SAP2000 y Word).
    - `PySide6`: Interfaz Gráfica (Qt).

Instalación de dependencias:
```bash
pip install comtypes PySide6
```

## Uso

1. Abra SAP2000 y cargue un modelo (o inicie uno nuevo).
2. Ejecute la aplicación principal:

```bash
python main_app.py
```
3. Navegue por las pestañas para usar las distintas herramientas.

## Personalización de Reportes

El módulo de Reportes es altamente personalizable mediante archivos JSON.

### Templates de Documento
Ubicación: `Reportes/templates/`
Cree un archivo `.json` con la siguiente estructura:
```json
{
  "template_name": "Mi Reporte",
  "sections": [
    { "type": "heading", "content": "Título 1", "parameters": { "level": 1 } },
    { "type": "text", "content": "Párrafo de texto...", "parameters": { "style": "Normal" } },
    { "type": "page_break" }
  ]
}
```

### Librería y Ecuaciones
Ubicación: `Reportes/library/`
Agregue archivos `.json` para categorizar sus snippets. Para las ecuaciones, utilice formato lineal (similar a LaTeX simplificado):

```json
{
  "type": "equation",
  "content": "x = (-b + \\sqrt(b^2 - 4ac))/(2a)"
}
```
**Sintaxis Soportada:**
*   `\sqrt(x)`: Raíz cuadrada
*   `a^2`, `a_b`: Potencias y subíndices
*   `\sigma`, `\alpha`, `\Delta`: Caracteres griegos
*   `\int`, `\sum`: Integrales y sumatorias
*   Las fracciones se detectan con `/` (ej: `a/b`).

## Arquitectura Técnica

El proyecto utiliza una arquitectura de **Inyección de Dependencias** para compartir la instancia de SAP2000:

1.  **`SapInterface` (Singleton-like)**:
    - Ubicado en `sap_interface.py`.
    - Mantiene una única referencia activa al objeto COM de SAP2000 (`SapModel`).
    - Emite señales (`connectionChanged`) cuando el estado de la conexión varía.

2.  **Módulos (Paquetes)**:
    - Cada herramienta es un paquete de Python con su propio `__init__.py`.
    - **Backend**: Clases agnósticas de la GUI (ej. `CombosBackend`) que reciben `sap_model` en su constructor.
    - **Frontend**: Widgets de PySide6 que reciben `sap_interface` para coordinar la conexión.

3.  **Patrón de Desarrollo**:
    - **Backend Unitario**: Permite probar la lógica sin GUI instanciando el backend y pasándole un modelo.
    - **GUI Decoplada**: La interfaz gráfica no contiene lógica de negocio compleja, solo presentación.
