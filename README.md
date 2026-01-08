# SAP2000 Automation Tools

This project provides a set of Python tools to automate tasks in CSI SAP2000 using the OAPI (Open Application Programming Interface) via the `comtypes` library. The application is structured in independent modules with graphical user interfaces (GUI) built with PySide6.

## Project Structure

The project is organized into modular components, each addressing specific engineering workflows:

### 1. Load Combinations Manager (`Combinations_Carga`)
An Excel-like interface to manage load combinations efficiently.
- **Functionality**:
    - Read existing load cases and combinations from the active SAP2000 model.
    - Add, modify, or delete combinations using a grid view.
    - Support for different combination types (Linear Additive, Envelope, etc.).
    - Design type selection (ASD/LRFD).
    - Robust update logic ("Upsert") to modify combinations without breaking model dependencies.
- **Entry Point**: `Combinations_Carga/app_combos_gui.py`

### 2. Mesh Utilities (`Utilidades_MOD`)
Tools for generating and modifying finite element meshes.
- **Functionality**:
    - **Rectangular Mesh**: Generate rectangular area elements with specific subdivisions.
    - **Hole Generation**: Create circular openings within existing area elements.
    - **Preview**: Real-time visual preview of the geometry before sending it to SAP2000.
- **Entry Point**: `Utilidades_MOD/app_utils_gui.py`

### 3. Base Plate Analysis (`Placa_Base`)
Module dedicated to the analysis and design of base plates.
- **Entry Point**: `Placa_Base/app_placabase_gui.py`

## Requirements

- **Software**: CSI SAP2000.
- **Python**: Version 3.13 or compatible.
- **Libraries**:
    - `comtypes`: For COM interface communication with SAP2000.
    - `PySide6`: For the Graphical User Interface.

## Usage

1. Open SAP2000 and load your model.
2. Run the desired module script using Python.
3. The GUI will attempt to connect to the active SAP2000 instance.

Example:
```bash
python Combinations_Carga/app_combos_gui.py
```

## Architecture

The project follows a modular pattern separating the interface from the logic:
- **GUI (*_gui.py)**: Handles user interaction and display using PySide6.
- **Backend (*_backend.py)**: Manages the logic and direct communication with the SAP2000 API.

## API Interaction

- The interaction relies on `comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")`.
- Parameter handling is specifically adjusted for Python's `comtypes` behavior, particularly regarding `ByRef` return values which are returned as tuples.
