# Step 3: Migración Módulos Fase 1 — Combinaciones de Carga y Modelo Base

## Goal
Refactorizar `Combinations_Carga` y `Modelo_Base` para usar la nueva infraestructura centralizada: `StyledButton`, `LogWidget`, `ProgressGroup`, `check_ret_code()`, y `AppLogger`.

## Prerequisites
- Steps 1 y 2 completados y commiteados
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 3.1: Migrar `Combinations_Carga/combos_backend.py` — Integrar check_ret_code y Logger

- [ ] Reemplazar el contenido completo de `Combinations_Carga/combos_backend.py` con el código siguiente:

```python
"""Backend de Combinaciones de Carga — Lógica pura para SAP2000 API."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_logger import AppLogger
from sap_utils_common import check_ret_code


class ComboBackend:
    def __init__(self, sap_model=None):
        """
        Inicializa el backend.

        Args:
            sap_model: Objeto SapModel opcional ya conectado.
        """
        self.SapModel = sap_model
        self.logger = AppLogger()

    def get_load_cases(self):
        """Retorna una lista con los nombres de todos los Load Cases."""
        if not self.SapModel:
            return []

        try:
            ret = self.SapModel.LoadCases.GetNameList()
            if check_ret_code(ret) and ret[0] > 0:
                names = ret[1]
                if not isinstance(names, (list, tuple)):
                    names = [names]
                return [str(n).strip() for n in names]
        except Exception as e:
            self.logger.error(f"Error obteniendo Load Cases: {e}")
        return []

    def get_combinations(self):
        """
        Retorna lista de dicts con la definición de cada combinación.
        Estructura: [{'name': 'COMB1', 'type': 0, 'items': {'DEAD': 1.2, 'LIVE': 1.6}}, ...]
        """
        if not self.SapModel:
            return []

        combos = []
        try:
            ret_names = self.SapModel.RespCombo.GetNameList()
            if not check_ret_code(ret_names):
                return []
            if ret_names[0] == 0:
                return []

            names = ret_names[1]
            if not isinstance(names, (list, tuple)):
                names = [names]

            for name in names:
                name = str(name).strip()
                # Obtener Tipo
                ret_type = self.SapModel.RespCombo.GetTypeOAPI(name)
                c_type = 0
                if check_ret_code(ret_type):
                    c_type = ret_type[0]

                # Obtener lista de casos dentro de esta combinación
                items = {}
                ret_list = self.SapModel.RespCombo.GetCaseList(name)

                if check_ret_code(ret_list) and ret_list[0] > 0:
                    c_types = ret_list[1]
                    c_names = ret_list[2]
                    sfs = ret_list[3]

                    if not isinstance(c_names, (list, tuple)):
                        c_names = [c_names]
                    if not isinstance(c_types, (list, tuple)):
                        c_types = [c_types]
                    if not isinstance(sfs, (list, tuple)):
                        sfs = [sfs]

                    count = min(len(c_names), len(c_types), len(sfs), ret_list[0])

                    for i in range(count):
                        try:
                            if int(c_types[i]) == 0:
                                name_key = str(c_names[i]).strip()
                                items[name_key] = sfs[i]
                        except Exception:
                            pass

                combos.append({
                    "name": name,
                    "type": c_type,
                    "items": items,
                })

        except Exception as e:
            self.logger.error(f"Error obteniendo combinaciones: {e}")
        return combos

    def _clear_combo_items(self, name):
        """Elimina todos los casos de carga de una combinación existente."""
        try:
            ret_list = self.SapModel.RespCombo.GetCaseList(name)

            if check_ret_code(ret_list) and ret_list[0] > 0:
                c_types = ret_list[1]
                c_names = ret_list[2]

                if not isinstance(c_names, (list, tuple)):
                    c_names = [c_names]
                if not isinstance(c_types, (list, tuple)):
                    c_types = [c_types]

                count = min(len(c_names), len(c_types), ret_list[0])

                for i in range(count):
                    try:
                        self.SapModel.RespCombo.DeleteCase(
                            name, int(c_types[i]), str(c_names[i]).strip()
                        )
                    except Exception:
                        pass
        except Exception as e:
            self.logger.warning(f"Aviso limpiando combinación {name}: {e}")

    def push_combinations(self, combos_data):
        """
        Envía las combinaciones a SAP2000.
        combos_data: lista de dicts {'name': str, 'type': int, 'items': {'CASE': factor}}
        Retorna el número de combinaciones procesadas.
        """
        if not self.SapModel:
            return 0

        success_count = 0

        try:
            self.SapModel.SetModelIsLocked(False)
        except Exception:
            pass

        for combo in combos_data:
            name = str(combo["name"]).strip()
            ctype = int(combo["type"])
            items = combo["items"]

            if not name:
                continue

            ret_add = self.SapModel.RespCombo.Add(name, ctype)
            if isinstance(ret_add, (list, tuple)):
                ret_add = ret_add[-1]

            if ret_add != 0:
                self.SapModel.RespCombo.SetTypeOAPI(name, ctype)
                self._clear_combo_items(name)

            for case_name, factor in items.items():
                try:
                    case_name_clean = str(case_name).strip()
                    val = float(factor)
                    if val != 0:
                        ret_case = self.SapModel.RespCombo.SetCaseList(
                            name, 0, case_name_clean, val
                        )
                        ret_code = ret_case
                        if isinstance(ret_case, (list, tuple)):
                            ret_code = ret_case[-1]
                        if ret_code != 0:
                            self.logger.warning(
                                f"No se pudo asignar '{case_name_clean}' a '{name}' (Código {ret_case})"
                            )
                except Exception as e:
                    self.logger.error(f"Error procesando factor para {case_name}: {e}")

            success_count += 1

        try:
            self.SapModel.View.RefreshView(0, False)
        except Exception:
            pass

        self.logger.success(f"Se procesaron {success_count} combinaciones")
        return success_count
```

##### Step 3.1 Verification Checklist
- [ ] Sin errores de importación: `python -c "from Combinations_Carga.combos_backend import ComboBackend; print('OK')"`
- [ ] La clase usa `check_ret_code()` en lugar de verificación manual `ret[-1] == 0`
- [ ] Los mensajes de error usan `self.logger` en lugar de `print()`

---

#### Step 3.2: Migrar `Combinations_Carga/app_combos_gui.py` — Integrar StyledButton y LogWidget

- [ ] Reemplazar el contenido completo de `Combinations_Carga/app_combos_gui.py` con el código siguiente:

```python
"""GUI de Combinaciones de Carga — Widget para gestionar combos en SAP2000."""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from .combos_backend import ComboBackend
except ImportError:
    try:
        from combos_backend import ComboBackend
    except ImportError:
        sys.path.append(os.path.dirname(__file__))
        from combos_backend import ComboBackend

from gui_components import StyledButton, LogWidget
from themes import COLORS


class CombosWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface

        model = self.sap_interface.SapModel if self.sap_interface else None
        self.backend = ComboBackend(sap_model=model)

        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)

        self.load_cases = []
        self.init_ui()

    def on_connection_changed(self, connected):
        """Actualizar el modelo del backend cuando la conexión global cambia."""
        if connected:
            self.backend.SapModel = self.sap_interface.SapModel
            self.log.log("Conexión global recibida", level="SUCCESS")
        else:
            self.backend.SapModel = None
            self.log.log("Conexión perdida", level="WARNING")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- Toolbar ---
        btn_layout = QHBoxLayout()

        self.btn_read = StyledButton("📥 Leer de SAP2000", variant="primary")
        self.btn_read.clicked.connect(self.load_from_sap)

        self.btn_send = StyledButton("📤 Enviar a SAP2000", variant="success")
        self.btn_send.clicked.connect(self.send_to_sap)

        self.btn_add_row = StyledButton("➕ Agregar Fila", variant="secondary")
        self.btn_add_row.clicked.connect(self.add_row)

        self.btn_del_row = StyledButton("➖ Eliminar Fila", variant="secondary")
        self.btn_del_row.clicked.connect(self.delete_row)

        btn_layout.addWidget(self.btn_read)
        btn_layout.addWidget(self.btn_send)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_del_row)

        layout.addLayout(btn_layout)

        # --- Info Label ---
        self.lbl_info = QLabel("Conecta con SAP2000 para cargar los Load Cases y Combinaciones.")
        self.lbl_info.setProperty("role", "info")
        layout.addWidget(self.lbl_info)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre Combinación", "Tipo", "ASD/LRFD"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # --- Log ---
        self.log = LogWidget()
        layout.addWidget(self.log)

        self.setLayout(layout)

    def load_from_sap(self):
        self.lbl_info.setText("Conectando...")
        QApplication.processEvents()

        cases = self.backend.get_load_cases()
        if not cases:
            self.lbl_info.setText("No se encontraron Load Cases o no hay conexión.")
            self.log.log("No se encontraron Load Cases", level="WARNING")
            return

        self.load_cases = cases

        headers = ["Nombre Combinación", "Tipo", "ASD/LRFD"] + cases
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        combos = self.backend.get_combinations()
        self.table.setRowCount(0)

        for c in combos:
            self.add_row_data(c["name"], c["type"], c["items"])

        msg = f"Cargados {len(cases)} Load Cases y {len(combos)} Combinaciones."
        self.lbl_info.setText(msg)
        self.log.log(msg, level="SUCCESS")

    def add_row(self):
        self.add_row_data("COMB_N", 0, {})

    def delete_row(self):
        rows = sorted(
            set(index.row() for index in self.table.selectedIndexes()), reverse=True
        )
        for row in rows:
            self.table.removeRow(row)

    def add_row_data(self, name, c_type, items):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Col 0: Nombre
        self.table.setItem(row, 0, QTableWidgetItem(str(name)))

        # Col 1: Tipo (ComboBox)
        combo_type = QComboBox()
        types = [
            "Linear Additive",
            "Envelope",
            "Absolute Additive",
            "SRSS",
            "Range Additive",
        ]
        combo_type.addItems(types)
        if 0 <= c_type < len(types):
            combo_type.setCurrentIndex(c_type)
        self.table.setCellWidget(row, 1, combo_type)

        # Col 2: ASD/LRFD (ComboBox)
        combo_design = QComboBox()
        design_opts = ["ASD", "LRFD", ""]
        combo_design.addItems(design_opts)
        combo_design.setCurrentIndex(2)
        self.table.setCellWidget(row, 2, combo_design)

        # Col 3+: Factores
        for i, case_name in enumerate(self.load_cases):
            col_idx = 3 + i
            factor = items.get(case_name, "")
            if factor != "":
                factor = str(factor)

            item = QTableWidgetItem(factor)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col_idx, item)

    def send_to_sap(self):
        if not self.load_cases:
            QMessageBox.warning(
                self, "Error", "Primero debes leer los Load Cases de SAP2000."
            )
            return

        data_to_send = []
        rows = self.table.rowCount()

        for r in range(rows):
            item_name = self.table.item(r, 0)
            name = item_name.text() if item_name else ""
            if not name:
                continue

            widget_type = self.table.cellWidget(r, 1)
            c_type = widget_type.currentIndex() if widget_type else 0

            items = {}
            for i, case_name in enumerate(self.load_cases):
                col_idx = 3 + i
                item_factor = self.table.item(r, col_idx)
                text = item_factor.text() if item_factor else ""

                if text.strip():
                    try:
                        val = float(text)
                        if val != 0:
                            items[case_name] = val
                    except ValueError:
                        pass

            data_to_send.append({"name": name, "type": c_type, "items": items})

        if not data_to_send:
            QMessageBox.information(self, "Info", "No hay datos válidos para enviar.")
            return

        count = self.backend.push_combinations(data_to_send)
        self.log.log(f"Se procesaron {count} combinaciones en SAP2000", level="SUCCESS")
        QMessageBox.information(
            self, "Éxito", f"Se procesaron {count} combinaciones en SAP2000."
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Combinaciones de Carga")
        self.resize(800, 500)
        self.setCentralWidget(CombosWidget())


if __name__ == "__main__":
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

##### Step 3.2 Verification Checklist
- [ ] Sin errores: `python -m Combinations_Carga.app_combos_gui` (la ventana se abre con el tema)
- [ ] Botones "📥 Leer de SAP2000" (azul primary) y "📤 Enviar a SAP2000" (verde success) con estilo correcto
- [ ] LogWidget visible en la parte inferior del widget
- [ ] Label informativo usa property `role=info` (estilo del tema)

---

#### Step 3.3: Migrar `Modelo_Base/app_modelo_base_gui.py` — Integrar Componentes Estandarizados

- [ ] Aplicar las siguientes modificaciones en `Modelo_Base/app_modelo_base_gui.py`:

**Cambio 1 — Agregar imports de infraestructura** (al inicio del archivo, después de los imports existentes de PySide6):

Agregar después de la línea `from .notas_widget import NotasWidget`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget, ProgressGroup
from app_logger import AppLogger
```

**Cambio 2 — Reemplazar botón de crear modelo** (dentro de `init_ui`, sección de botones):

Buscar:
```python
        self.btn_create_model = QPushButton("Crear Modelo Base")
        self.btn_create_model.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px;")
        self.btn_create_model.clicked.connect(self.on_create_model_click)
```

Reemplazar con:
```python
        self.btn_create_model = StyledButton("🏗️ Crear Modelo Base", variant="primary")
        self.btn_create_model.clicked.connect(self.on_create_model_click)
```

**Cambio 3 — Reemplazar ProgressBar y Label de Estado** (dentro de `init_ui`):

Buscar:
```python
        # 3. Barra de Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        group_layout.addWidget(self.progress_bar)
        
        # 4. Label de Estado
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #666; font-style: italic;")
        group_layout.addWidget(self.lbl_status)
```

Reemplazar con:
```python
        # 3. Progreso estandarizado
        self.progress_group = ProgressGroup("Progreso de Creación")
        group_layout.addWidget(self.progress_group)

        # 4. Log de operaciones
        self.log = LogWidget()
        group_layout.addWidget(self.log)
```

**Cambio 4 — Actualizar `on_create_model_click`** para usar los nuevos componentes:

Buscar (bloque de preparación de UI):
```python
            # Preparar UI para ejecución
            self.btn_create_model.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.lbl_status.setText("Iniciando...")
```

Reemplazar con:
```python
            # Preparar UI para ejecución
            self.btn_create_model.setEnabled(False)
            self.progress_group.set_visible(True)
            self.progress_group.set_progress(0, "Iniciando...")
            self.log.log("Iniciando creación de modelo base...", level="INFO")
```

**Cambio 5 — Actualizar `_on_progress`**:

Buscar:
```python
    def _on_progress(self, pct: int, msg: str):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)
```

Reemplazar con:
```python
    def _on_progress(self, pct: int, msg: str):
        """Actualiza la barra de progreso."""
        self.progress_group.set_progress(pct, msg)
        self.log.log(msg, level="INFO")
```

**Cambio 6 — Actualizar `_on_finished`**:

Buscar:
```python
    def _on_finished(self, result: BaseModelResult):
        """Maneja la finalización de la creación."""
        self._reset_ui()
        
        if result.success:
            QMessageBox.information(self, "Éxito", result.message)
        else:
            error_detail = "\n".join(result.errors) if result.errors else result.message
            QMessageBox.critical(self, "Error", f"Falló la creación:\n{error_detail}")
```

Reemplazar con:
```python
    def _on_finished(self, result: BaseModelResult):
        """Maneja la finalización de la creación."""
        self._reset_ui()

        if result.success:
            self.log.log(result.message, level="SUCCESS")
            QMessageBox.information(self, "Éxito", result.message)
        else:
            error_detail = "\n".join(result.errors) if result.errors else result.message
            self.log.log(f"Error: {error_detail}", level="ERROR")
            QMessageBox.critical(self, "Error", f"Falló la creación:\n{error_detail}")
```

**Cambio 7 — Actualizar `_reset_ui`**:

Buscar:
```python
    def _reset_ui(self):
        """Restaura la UI tras la ejecución."""
        self.btn_create_model.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("")
```

Reemplazar con:
```python
    def _reset_ui(self):
        """Restaura la UI tras la ejecución."""
        self.btn_create_model.setEnabled(True)
        self.progress_group.reset()
```

**Cambio 8 — Actualizar bloque `if __name__`** para aplicar tema:

Buscar el bloque `if __name__ == "__main__":` al final del archivo y reemplazar con:

```python
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = ModeloBaseWidget()
    window.show()
    sys.exit(app.exec())
```

##### Step 3.3 Verification Checklist
- [ ] Sin errores al ejecutar `python -m Modelo_Base.app_modelo_base_gui`
- [ ] El botón "🏗️ Crear Modelo Base" tiene estilo primary (azul)
- [ ] El `ProgressGroup` aparece durante la creación del modelo
- [ ] El `LogWidget` registra los mensajes de progreso y resultado
- [ ] Los demás controles (ComboBox, SpinBox, etc.) heredan el estilo del tema global

---

#### Step 3.4: Migrar `Modelo_Base/modelo_base_backend.py` — Integrar check_ret_code y Logger

- [ ] Aplicar las siguientes modificaciones en `Modelo_Base/modelo_base_backend.py`:

**Cambio 1 — Agregar imports de infraestructura** (al inicio del archivo, después de los imports existentes):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code
```

**Cambio 2 — Agregar logger al constructor de `BaseModelBackend`**:

En el `__init__` de la clase, agregar:
```python
        self.logger = AppLogger()
```

**Cambio 3 — Reemplazar el método helper `_ret_ok`**:

Buscar la definición del método `_ret_ok` y reemplazar con:
```python
    def _ret_ok(self, ret) -> bool:
        """Wrapper sobre check_ret_code centralizado."""
        return check_ret_code(ret)
```

Esto mantiene compatibilidad con todo el código existente que llama `self._ret_ok(ret)`.

##### Step 3.4 Verification Checklist
- [ ] Sin errores: `python -c "from Modelo_Base.modelo_base_backend import BaseModelBackend; print('OK')"`
- [ ] El método `_ret_ok` ahora delega a `check_ret_code` centralizado

---

#### Step 3 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: migrate Combinations_Carga and Modelo_Base to centralized infrastructure
```

Archivos modificados:
- `Combinations_Carga/combos_backend.py`
- `Combinations_Carga/app_combos_gui.py`
- `Modelo_Base/app_modelo_base_gui.py`
- `Modelo_Base/modelo_base_backend.py`
