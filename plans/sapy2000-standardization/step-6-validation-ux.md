# Step 6: Mejoras UX — Validación y Feedback

## Goal
Agregar capa de validación de inputs, mejorar feedback al usuario con confirmaciones pre-ejecución, y conectar `ProgressGroup` a operaciones largas en todos los módulos.

## Prerequisites
- Steps 1–5 completados y commiteados
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 6.1: Agregar Validadores a `gui_components.py`

 - [x] Agregar la clase `InputValidator` al final de `gui_components.py`:

```python
# ======================================================================
# InputValidator
# ======================================================================

class InputValidator:
    """
    Validadores reutilizables para inputs de formularios.

    Uso:
        ok, msg = InputValidator.validate_numeric("12.5", min_val=0, max_val=100)
        ok, msg = InputValidator.validate_required("")
        ok, msg = InputValidator.validate_positive("0")
    """

    @staticmethod
    def validate_required(value: str, field_name: str = "Campo") -> tuple:
        """Valida que el valor no esté vacío."""
        if not value or not str(value).strip():
            return False, f"{field_name} es requerido."
        return True, ""

    @staticmethod
    def validate_numeric(
        value: str, field_name: str = "Valor",
        min_val: float = None, max_val: float = None,
    ) -> tuple:
        """Valida que el valor sea numérico y esté dentro del rango."""
        if not value or not str(value).strip():
            return False, f"{field_name} es requerido."
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False, f"{field_name} debe ser un número válido."

        if min_val is not None and num < min_val:
            return False, f"{field_name} debe ser ≥ {min_val}."
        if max_val is not None and num > max_val:
            return False, f"{field_name} debe ser ≤ {max_val}."
        return True, ""

    @staticmethod
    def validate_positive(value: str, field_name: str = "Valor") -> tuple:
        """Valida que el valor sea un número positivo (> 0)."""
        ok, msg = InputValidator.validate_numeric(value, field_name)
        if not ok:
            return ok, msg
        if float(value) <= 0:
            return False, f"{field_name} debe ser mayor que 0."
        return True, ""

    @staticmethod
    def validate_coordinates(x: str, y: str, z: str) -> tuple:
        """Valida que las tres coordenadas sean números válidos."""
        for label, val in [("X", x), ("Y", y), ("Z", z)]:
            ok, msg = InputValidator.validate_numeric(val, field_name=f"Coordenada {label}")
            if not ok:
                return False, msg
        return True, ""

    @staticmethod
    def validate_batch(validations: list) -> tuple:
        """
        Ejecuta múltiples validaciones y retorna el primer error.

        Args:
            validations: Lista de tuplas (ok: bool, msg: str)

        Returns:
            (True, "") si todo pasó, o (False, primer_error) si alguno falla.
        """
        for ok, msg in validations:
            if not ok:
                return False, msg
        return True, ""
```

##### Step 6.1 Verification Checklist
- [ ] Test rápido:
  ```bash
  python -c "from gui_components import InputValidator; print(InputValidator.validate_numeric('12.5', min_val=0)); print(InputValidator.validate_numeric('abc')); print(InputValidator.validate_required(''))"
  ```
  Debe imprimir:
  ```
  (True, '')
  (False, 'Valor debe ser un número válido.')
  (False, 'Campo es requerido.')
  ```

---

#### Step 6.2: Agregar Función Helper de Confirmación a `gui_components.py`

 - [x] Agregar al final de `gui_components.py`:

```python
# ======================================================================
# Helpers de Diálogo
# ======================================================================

from PySide6.QtWidgets import QMessageBox


def confirm_action(parent, title: str, message: str, detail: str = "") -> bool:
    """
    Muestra un diálogo de confirmación antes de una operación importante.

    Args:
        parent: Widget padre para el diálogo
        title: Título del diálogo
        message: Mensaje principal
        detail: Texto de detalle (opcional, aparece en área expandible)

    Returns:
        True si el usuario confirma, False si cancela.
    """
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    if detail:
        box.setDetailedText(detail)
    return box.exec() == QMessageBox.Yes


def show_validation_errors(parent, errors: list):
    """
    Muestra un diálogo con los errores de validación.

    Args:
        parent: Widget padre
        errors: Lista de strings con mensajes de error
    """
    if not errors:
        return
    msg = "Se encontraron los siguientes problemas:\n\n"
    msg += "\n".join(f"• {e}" for e in errors)
    QMessageBox.warning(parent, "Validación", msg)
```

##### Step 6.2 Verification Checklist
- [ ] Sin errores de importación: `python -c "from gui_components import confirm_action, show_validation_errors, InputValidator; print('OK')"`

---

#### Step 6.3: Agregar Validación Pre-Ejecución en `Modelo_Base/app_modelo_base_gui.py`

 - [x] En el método `on_create_model_click`, agregar validación con confirmación detallada:

Buscar (al inicio del método, después de la validación de conexión):
```python
        # Confirmación
        res = QMessageBox.warning(
            self, "Advertencia", 
            "Esto BORRARÁ el modelo actual y creará uno nuevo.\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if res != QMessageBox.Yes:
            return
```

Reemplazar con:
```python
        # Confirmación con resumen de parámetros
        from gui_components import confirm_action
        zone = int(self.combo_zone.currentText())
        soil = self.combo_soil.currentText()
        summary = (
            f"Zona Sísmica: {zone}\n"
            f"Tipo de Suelo: {soil}\n"
            f"Factor I: {self.spin_importance.value()}\n"
            f"Rx: {self.spin_R_x.value()}, Ry: {self.spin_R_y.value()}\n"
            f"Rv: {self.spin_vert_R.value()}\n"
            f"ξx: {self.spin_damp_x.value()}, ξy: {self.spin_damp_y.value()}, ξv: {self.spin_vert_damp.value()}"
        )
        if not confirm_action(
            self,
            "Crear Modelo Base",
            "Esto BORRARÁ el modelo actual y creará uno nuevo con los siguientes parámetros.\n¿Continuar?",
            detail=summary,
        ):
            return
```

##### Step 6.3 Verification Checklist
- [ ] Al hacer clic en "Crear Modelo Base", el diálogo muestra los parámetros como detalle expandible
- [ ] Al cancelar, no se ejecuta ninguna acción

---

#### Step 6.4: Agregar Validación Pre-Ejecución en `Fundaciones/fundaciones_gui.py`

 - [x] En el método `create_pedestal_section`, agregar validación de inputs antes de llamar al backend:

Agregar al inicio del método (después de verificar conexión):
```python
        from gui_components import InputValidator, show_validation_errors

        errors = []
        ok, msg = InputValidator.validate_required(self.input_section_name.text(), "Nombre de sección")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_positive(self.input_width.text(), "Ancho")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_positive(self.input_height.text(), "Alto")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_positive(self.input_spacing.text(), "Espaciamiento")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_positive(self.input_cover.text(), "Recubrimiento")
        if not ok:
            errors.append(msg)

        if errors:
            show_validation_errors(self, errors)
            return
```

- [ ] En el método `model_foundation`, agregar confirmación:

Agregar antes de llamar al backend:
```python
        from gui_components import confirm_action
        if not confirm_action(
            self,
            "Modelar Fundación",
            "Se creará la fundación completa con los parámetros definidos.\n¿Continuar?",
        ):
            return
```

##### Step 6.4 Verification Checklist
- [ ] Al intentar crear sección con campos vacíos, aparece diálogo de validación
- [ ] Al modelar fundación, aparece confirmación antes de ejecutar

---

#### Step 6.5: Agregar Validación Pre-Ejecución en `Utilidades_MOD/app_utils_gui.py`

 - [x] En el método de generar malla rectangular, agregar validación:

Agregar antes de llamar al backend:
```python
        from gui_components import InputValidator, show_validation_errors

        errors = []
        ok, msg = InputValidator.validate_positive(self.input_width.text(), "Ancho")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_positive(self.input_length.text(), "Largo")
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_numeric(
            self.input_nx.text(), "Divisiones X", min_val=1, max_val=200
        )
        if not ok:
            errors.append(msg)
        ok, msg = InputValidator.validate_numeric(
            self.input_ny.text(), "Divisiones Y", min_val=1, max_val=200
        )
        if not ok:
            errors.append(msg)

        if errors:
            show_validation_errors(self, errors)
            return
```

##### Step 6.5 Verification Checklist
- [ ] Al intentar generar malla con dimensiones vacías o inválidas, aparece diálogo de validación
- [ ] Valores fuera de rango (ej: Nx > 200) son rechazados

---

#### Step 6.6: Agregar Validación en `Combinations_Carga/app_combos_gui.py`

 - [x] En `send_to_sap`, agregar validación de conexión antes de enviar:

Buscar (al inicio de `send_to_sap`):
```python
    def send_to_sap(self):
        if not self.load_cases:
            QMessageBox.warning(
                self, "Error", "Primero debes leer los Load Cases de SAP2000."
            )
            return
```

Agregar después de esa validación:
```python
        # Verificar conexión activa
        if not self.sap_interface or not self.sap_interface.is_connected():
            QMessageBox.warning(self, "Desconectado", "No hay conexión activa con SAP2000.")
            return

        from gui_components import confirm_action
        rows = self.table.rowCount()
        if not confirm_action(
            self,
            "Enviar Combinaciones",
            f"Se enviarán {rows} combinaciones a SAP2000.\n¿Continuar?",
        ):
            return
```

##### Step 6.6 Verification Checklist
- [ ] Al enviar combinaciones, aparece confirmación con el número de combos
- [ ] Si no hay conexión, muestra diálogo de desconexión

---

#### Step 6 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: add input validation, confirmation dialogs and UX feedback across all modules
```

Archivos modificados:
- `gui_components.py` (agregar InputValidator, confirm_action, show_validation_errors)
- `Modelo_Base/app_modelo_base_gui.py` (confirmación con detalle)
- `Fundaciones/fundaciones_gui.py` (validación de inputs)
- `Utilidades_MOD/app_utils_gui.py` (validación de inputs)
- `Combinations_Carga/app_combos_gui.py` (confirmación de envío)
