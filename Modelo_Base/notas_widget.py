"""
Widget de notas con soporte Markdown para guiar al usuario
en la creación del modelo base.

Características:
    - Carga archivos .md desde la carpeta notas/
    - Alterna entre vista renderizada y edición lado a lado
    - Vista previa Markdown en tiempo real
    - Guarda notas personalizadas del usuario
    - Exporta notas a ubicación elegida
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QTextBrowser, QTextEdit, QPushButton, QLabel,
    QSplitter, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# markdown es opcional — si no está, se muestra texto plano
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


NOTAS_DIR = os.path.join(os.path.dirname(__file__), "notas")

# ============================================================
# Estilos CSS para el renderizado HTML
# ============================================================
_HTML_STYLE = """
<style>
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.55;
        color: #222;
    }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 4px; font-size: 17px; }
    h2 { color: #2980b9; font-size: 14px; }
    h3 { color: #8e44ad; font-size: 13px; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; }
    th, td { border: 1px solid #bdc3c7; padding: 5px 8px; text-align: left; font-size: 12px; }
    th { background-color: #3498db; color: white; }
    tr:nth-child(even) { background-color: #ecf0f1; }
    code {
        background: #f0f0f0; padding: 2px 5px; border-radius: 3px;
        font-family: Consolas, monospace; font-size: 11px;
    }
    pre {
        background: #2d2d2d; color: #f8f8f2; padding: 10px;
        border-radius: 4px; overflow-x: auto; font-size: 11px;
    }
    blockquote {
        border-left: 4px solid #3498db; margin: 8px 0;
        padding: 6px 14px; background: #eaf2f8; font-size: 12px;
    }
    ul, ol { padding-left: 22px; }
    li { margin-bottom: 2px; }
</style>
"""


class NotasWidget(QWidget):
    """Panel de notas Markdown con vista previa y edición."""

    notaGuardada = Signal(str)  # Emite la ruta del archivo guardado

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = None
        self._is_editing = False
        self._init_ui()
        self._load_nota_list()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Barra superior ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.lbl_titulo = QLabel("📝 Notas")
        self.lbl_titulo.setStyleSheet("font-weight: bold; font-size: 13px;")
        toolbar.addWidget(self.lbl_titulo)

        toolbar.addStretch()

        self.cmb_notas = QComboBox()
        self.cmb_notas.setMinimumWidth(180)
        self.cmb_notas.setToolTip("Seleccionar nota")
        self.cmb_notas.currentIndexChanged.connect(self._on_nota_selected)
        toolbar.addWidget(self.cmb_notas)

        layout.addLayout(toolbar)

        # --- Botones de acción ---
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(4)

        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.setCheckable(True)
        self.btn_editar.setToolTip("Alternar entre vista y edición")
        self.btn_editar.toggled.connect(self._toggle_edit_mode)
        btn_bar.addWidget(self.btn_editar)

        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.setToolTip("Guardar cambios en la nota")
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self._save_nota)
        btn_bar.addWidget(self.btn_guardar)

        self.btn_exportar = QPushButton("📤 Exportar")
        self.btn_exportar.setToolTip("Exportar nota como archivo .md")
        self.btn_exportar.clicked.connect(self._export_nota)
        btn_bar.addWidget(self.btn_exportar)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip("Recargar lista de notas")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self._load_nota_list)
        btn_bar.addWidget(self.btn_refresh)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        # --- Área de contenido ---
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #fefefe;
                border: 1px solid #ccc;
                padding: 6px;
                font-size: 12px;
            }
        """)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                padding: 6px;
            }
        """)
        self.editor.setVisible(False)
        self.editor.textChanged.connect(self._on_text_changed)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.browser)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([1, 0])

        layout.addWidget(self.splitter)

        # --- Indicador de estado ---
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.lbl_status)

    # --------------------------------------------------------- Carga notas
    def _load_nota_list(self):
        """Carga la lista de archivos .md disponibles en la carpeta notas/."""
        self.cmb_notas.blockSignals(True)
        self.cmb_notas.clear()

        if not os.path.isdir(NOTAS_DIR):
            os.makedirs(NOTAS_DIR, exist_ok=True)

        # Crear notas por defecto si la carpeta está vacía
        md_files = sorted(f for f in os.listdir(NOTAS_DIR) if f.endswith(".md"))
        if not md_files:
            self._create_default_notas()
            md_files = sorted(f for f in os.listdir(NOTAS_DIR) if f.endswith(".md"))

        for f in md_files:
            # Nombre legible: quitar .md, reemplazar _ por espacios, capitalizar
            display_name = f.replace(".md", "").replace("_", " ").title()
            self.cmb_notas.addItem(display_name, userData=f)

        self.cmb_notas.blockSignals(False)

        if md_files:
            self.cmb_notas.setCurrentIndex(0)
            self._on_nota_selected(0)

        self.lbl_status.setText(f"{len(md_files)} nota(s) disponibles")

    def _on_nota_selected(self, index):
        """Carga y renderiza el archivo .md seleccionado."""
        if index < 0:
            return
        filename = self.cmb_notas.itemData(index)
        if not filename:
            return
        filepath = os.path.join(NOTAS_DIR, filename)
        self._current_file = filepath

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                md_text = f.read()
        except OSError:
            md_text = f"*Error al leer {filename}*"

        self._render_markdown(md_text)
        self.editor.blockSignals(True)
        self.editor.setPlainText(md_text)
        self.editor.blockSignals(False)
        self.btn_guardar.setEnabled(False)

    def _render_markdown(self, md_text: str):
        """Convierte Markdown a HTML y lo muestra en el browser."""
        if MARKDOWN_AVAILABLE:
            html_body = markdown.markdown(
                md_text,
                extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
            )
        else:
            # Fallback: mostrar como texto plano con saltos de línea
            escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_body = f"<pre>{escaped}</pre>"

        styled_html = f"{_HTML_STYLE}\n{html_body}"
        self.browser.setHtml(styled_html)

    # ------------------------------------------------------------ Edición
    def _toggle_edit_mode(self, editing: bool):
        """Alterna entre modo vista y modo edición (vertical: browser arriba, editor abajo)."""
        self._is_editing = editing
        self.editor.setVisible(editing)
        self.btn_editar.setText("👁️ Vista" if editing else "✏️ Editar")

        if editing:
            self.splitter.setSizes([1, 1])
            self.lbl_status.setText("Modo edición — los cambios se previsualizan arriba")
        else:
            self.splitter.setSizes([1, 0])
            self.lbl_status.setText("")

    def _on_text_changed(self):
        """Actualiza la vista previa en tiempo real mientras se edita."""
        self.btn_guardar.setEnabled(True)
        md_text = self.editor.toPlainText()
        self._render_markdown(md_text)

    def _save_nota(self):
        """Guarda los cambios en el archivo .md actual."""
        if not self._current_file:
            return
        try:
            with open(self._current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.btn_guardar.setEnabled(False)
            self.lbl_status.setText(f"✅ Guardado: {os.path.basename(self._current_file)}")
            self.notaGuardada.emit(self._current_file)
        except OSError as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")

    def _export_nota(self):
        """Exporta la nota actual a una ubicación elegida por el usuario."""
        if not self._current_file:
            return
        default_name = os.path.basename(self._current_file)
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar nota", default_name,
            "Markdown (*.md);;Todos (*.*)"
        )
        if path:
            try:
                content = self.editor.toPlainText() if self._is_editing else ""
                if not content and self._current_file:
                    with open(self._current_file, "r", encoding="utf-8") as f:
                        content = f.read()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.lbl_status.setText(f"📤 Exportado: {os.path.basename(path)}")
            except OSError as e:
                QMessageBox.warning(self, "Error", f"No se pudo exportar:\n{e}")

    # ------------------------------------------------ Notas por defecto
    def _create_default_notas(self):
        """Crea archivos .md de ejemplo en la carpeta notas/."""
        defaults = {
            "01_general.md": _NOTA_GENERAL,
            "04_mis_notas.md": _NOTA_CUSTOM,
        }
        for filename, content in defaults.items():
            filepath = os.path.join(NOTAS_DIR, filename)
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)


# ============================================================
# Contenido por defecto de las notas
# ============================================================

_NOTA_GENERAL = """\
# Modelo Base — Descripción General

Este módulo genera automáticamente un modelo base en SAP2000 con materiales,
patrones de carga, espectros sísmicos NCh2369:2025, combinaciones de carga
y secciones de frame predefinidas.

---

## 1. Unidades

El modelo se inicializa en **Tonf, m, °C** (código SAP2000 = 12).

---

## 2. Materiales

Se crean 4 materiales con propiedades completas (isotrópicas, peso/masa y diseño):

| Material   | Tipo      | E [tonf/m²]  | Fy / f'c       | Uso típico                    |
|------------|-----------|-------------- |----------------|-------------------------------|
| A36        | Acero     | 20,389,019    | Fy = 25,310    | Perfiles estructurales        |
| A500_GrB   | Acero     | 20,389,019    | Fy = 32,341    | Tubos HSS                     |
| G30        | Hormigón  | 2,641,100     | f'c = 3,059    | Fundaciones, elementos mayores|
| G25        | Hormigón  | 2,410,900     | f'c = 2,549    | Pedestales, elementos menores |

> Los valores de E, Fy, f'c están en Tonf/m² (consistente con las unidades del modelo).

---

## 3. Patrones de Carga

Se crean 12 patrones de carga:

| Patrón  | Tipo SAP2000   | Peso Propio | Descripción                      |
|---------|----------------|-------------|----------------------------------|
| DEAD    | Dead (1)       | 1.2         | Carga muerta (incluye peso propio) |
| LIVE    | Live (3)       | 0.0         | Sobrecarga de uso                |
| ROOF    | Roof (11)      | 0.0         | Sobrecarga de techo              |
| SNOW    | Snow (7)       | 0.0         | Carga de nieve                   |
| EQX     | Quake (5)      | 0.0         | Sismo dirección X                |
| EQY     | Quake (5)      | 0.0         | Sismo dirección Y                |
| EQZ     | Quake (5)      | 0.0         | Sismo dirección vertical         |
| WINDX   | Wind (6)       | 0.0         | Viento dirección X               |
| WINDY   | Wind (6)       | 0.0         | Viento dirección Y               |
| TEMP    | Temperature (10)| 0.0        | Carga de temperatura             |
| SO      | Other (8)      | 0.0         | Sobrecarga de operación (industrial) |
| SA      | Other (8)      | 0.0         | Sobrecarga de almacenamiento     |

> **Nota**: El patrón DEAD tiene `self_wt = 1.2`. Esto es solo el multiplicador
> de peso propio del patrón; no confundir con el factor de carga LRFD.

---

## 4. Secciones de Frame

Se definen secciones de ejemplo en cada categoría:

**Perfiles I (W shapes)**

| Sección   | h [m]  | b [m]  | tf [m] | tw [m] | Material |
|-----------|--------|--------|--------|--------|----------|
| W200x46   | 0.203  | 0.203  | 0.011  | 0.007  | A36      |
| W310x97   | 0.308  | 0.305  | 0.015  | 0.009  | A36      |

**Tubos HSS (rectangulares)**

| Sección        | h [m]  | b [m]  | t [m]  | Material  |
|----------------|--------|--------|--------|-----------|
| HSS100x100x6   | 0.100  | 0.100  | 0.006  | A500_GrB  |
| HSS150x150x8   | 0.150  | 0.150  | 0.008  | A500_GrB  |

**Ángulos**

| Sección    | h [m]  | b [m]  | t [m]  | Material |
|------------|--------|--------|--------|----------|
| L50x50x5   | 0.050  | 0.050  | 0.005  | A36      |
| L75x75x6   | 0.075  | 0.075  | 0.006  | A36      |

**Canales**

| Sección    | h [m]  | b [m]  | tf [m] | tw [m] | Material |
|------------|--------|--------|--------|--------|----------|
| C100x10    | 0.100  | 0.050  | 0.009  | 0.006  | A36      |
| C150x15    | 0.150  | 0.075  | 0.011  | 0.007  | A36      |

> Estas secciones son de referencia. Se deben agregar las secciones
> reales del proyecto antes del análisis.

---

## 5. Espectros Sísmicos (NCh2369:2025)

### Parámetros de entrada (definidos en la GUI)

- **Zona sísmica** (1, 2, 3) → determina A₀ (0.28, 0.42, 0.56 g)
- **Tipo de suelo** (A-E) → determina S, r, T₀, p, q, T₁
- **Factor de importancia** (I)
- **Factores R** (Rx, Ry, Rv) y amortiguamientos (ξx, ξy, ξv)

### Espectros generados

| Función           | Dirección    | Factor escala | Desplaz. período | R*             |
|-------------------|--------------|---------------|-------------------|----------------|
| SaH_{zona}{suelo} | Horizontal X | 1.0           | 1.0×T             | Sí             |
| SaH_{zona}{suelo} | Horizontal Y | 1.0           | 1.0×T             | Sí             |
| SaV_{zona}{suelo} | Vertical     | 0.7           | 1.7×T             | No (R directo) |

- **R*** (reducción corregida): Para T < 0.16·R·T₁, se interpola linealmente de 1.5 a R.
- **Corrección por amortiguamiento**: Factor (0.05/ξ)^0.4
- Los espectros se definen como funciones User en SAP2000 y se asignan a Load Cases tipo Response Spectrum.
- El factor de escala del caso RS es **g = 9.81** (el espectro ya incluye R).

### Casos de carga creados

| Caso | Tipo             | Función    | Dirección | Amort. |
|------|------------------|------------|-----------|--------|
| EQX  | Response Spectrum | SaH_...    | U1        | ξx     |
| EQY  | Response Spectrum | SaH_...    | U2        | ξy     |
| EQZ  | Response Spectrum | SaV_...    | U3        | ξv     |

---

## 6. Combinaciones de Carga

### 6.1 Combinaciones NCh2369 (Regla 100/30/30)

Combinaciones lineales de los casos RS para la regla direccional:

| Combo | EQX | EQY | EQZ |
|-------|-----|-----|-----|
| E1    | 1.0 | 0.3 | 0.3 |
| E2    | 0.3 | 1.0 | 0.3 |
| E3    | 0.3 | 0.3 | 1.0 |

### 6.2 Combinaciones LRFD

Incluyen los 7 casos básicos de NCh3171 más combinaciones industriales NCh2369:

| Caso | Descripción                           | Variantes        |
|------|---------------------------------------|------------------|
| 1    | 1.4D                                  | ±T               |
| 2    | 1.2D + 1.6L + 0.5(R o S)             | R/S, ±T          |
| 3a   | 1.2D + 1.6(R o S) + L                | R/S, ±T          |
| 3b   | 1.2D + 1.6(R o S) + 0.8W             | R/S, ±WX/WY, ±T  |
| 4    | 1.2D + 1.6W + L + 0.5(R o S)         | R/S, ±WX/WY, ±T  |
| 6    | 0.9D + 1.6W                           | ±WX/WY, ±T       |
| NCh  | 1.2D + 0.25L + SO + SA ± E(1,2,3)    | ±E, ±T           |
| NCh  | 0.9D + SA ± E(1,2,3)                  | ±E, ±T           |

### 6.3 Combinaciones ASD

| Caso | Descripción                           | Variantes          |
|------|---------------------------------------|--------------------|
| 1    | D                                     | ±T                 |
| 2    | D + L                                 | ±T                 |
| 3    | D + (R o S)                           | R/S, ±T            |
| 4    | D + 0.75L + 0.75(R o S)              | R/S, ±T            |
| 5a   | D + W                                 | ±WX/WY, ±T         |
| 6a   | D + 0.75W + 0.75L + 0.75(R o S)      | R/S, ±WX/WY, ±T   |
| 7    | 0.6D + W                              | ±WX/WY, ±T         |
| NCh  | D + 0.1875L + 0.75SO + 0.75SA ± 0.7E | ±E(1,2,3), ±T     |
| NCh  | D + 0.75SA ± 0.7E                     | ±E(1,2,3), ±T     |

### 6.4 Envolventes

| Envolvente | Tipo     | Contenido                       |
|------------|----------|---------------------------------|
| ENV_LRFD   | Envelope | Todas las combinaciones LRFD    |
| ENV_ASD    | Envelope | Todas las combinaciones ASD     |

> Las combinaciones LRFD y ASD se marcan automáticamente como
> combos de diseño para acero y hormigón en SAP2000.

---

## 7. Resumen del Proceso

El backend ejecuta los siguientes pasos en orden:

1. Inicializar modelo nuevo (Tonf-m-C)
2. Crear archivo en blanco
3. Configurar materiales (A36, A500_GrB, G30, G25)
4. Crear 12 patrones de carga
5. Definir secciones de frame de ejemplo
6. Calcular y asignar espectros sísmicos (H-X, H-Y, V)
7. Crear combinaciones (NCh + LRFD + ASD)
8. Crear envolventes (ENV_LRFD, ENV_ASD)

> **Importante**: El modelo se crea EN BLANCO (sin geometría).
> La grilla, elementos y cargas se deben definir manualmente
> después de ejecutar el Modelo Base.
"""

_NOTA_CUSTOM = """\
# Mis Notas

*Escribe aquí tus consideraciones específicas del proyecto.*

## Información del Proyecto
- **Nombre**: 
- **Ubicación**: 
- **Categoría de ocupación**: 
- **Zona sísmica**: 
- **Tipo de suelo**: 

## Consideraciones Especiales
- 

## Pendientes
- [ ] Revisar combinaciones de carga
- [ ] Verificar materiales
- [ ] Definir secciones
- [ ] Asignar restricciones

## Registro de Cambios

| Fecha | Cambio | Responsable |
|-------|--------|-------------|
|       |        |             |
"""
