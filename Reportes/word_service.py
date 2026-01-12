import comtypes.client
import logging

logger = logging.getLogger(__name__)

class WordService:
    """
    Servicio para interactuar con Microsoft Word con comtypes.
    """
    def __init__(self):
        self.word_app = None
        self.active_doc = None

    def connect(self):
        """Conecta a una instancia activa de Word o crea una nueva si no existe."""
        try:
            self.word_app = comtypes.client.GetActiveObject("Word.Application")
            logger.info("Conectado a instancia activa de Word.")
        except Exception:
            try:
                self.word_app = comtypes.client.CreateObject("Word.Application")
                logger.info("Nueva instancia de Word creada.")
            except Exception as e:
                logger.error(f"No se pudo iniciar Word: {e}")
                return False
        
        self.word_app.Visible = True
        return True

    def get_active_document(self):
        """Obtiene el documento activo o crea uno nuevo."""
        if not self.word_app:
            if not self.connect():
                return None

        try:
            self.active_doc = self.word_app.ActiveDocument
        except Exception:
            # Si no hay documento abierto (com error), crear uno nuevo
            self.active_doc = self.word_app.Documents.Add()
        
        return self.active_doc

    def create_new_document(self):
        """Fuerza la creación de un nuevo documento."""
        if not self.word_app:
            if not self.connect():
                return None
        
        self.active_doc = self.word_app.Documents.Add()
        return self.active_doc

    def insert_text_at_cursor(self, text, style="Normal"):
        """Inserta texto en la posición del cursor."""
        if not self.word_app: 
            return False
            
        selection = self.word_app.Selection
        selection.TypeText(text)
        try:
            # A veces los estilos tienen nombres locales
            selection.Style = style
        except:
            pass # Si falla el estilo, seguimos
        selection.TypeParagraph()
        return True

    def insert_page_break(self):
        """Inserta un salto de página."""
        if not self.word_app: return False
        
        # wdPageBreak = 7
        self.word_app.Selection.InsertBreak(7)
        return True

    def insert_heading(self, text, level=1):
        """Inserta un título con el nivel especificado."""
        style = f"Heading {level}"
        # En español a veces es "Título 1", pero comtypes/automation suele usar nombres internos en inglés o localizados.
        # Word a veces es tricky con los nombres de estilos localizados.
        # Intentaremos usar la constante numérica si falla el string, pero por ahora string.
        # WdBuiltinStyle: wdStyleHeading1 = -2, wdStyleHeading2 = -3, etc.
        
        # Una forma segura es usar el active document styles
        if not self.word_app: return False

        selection = self.word_app.Selection
        selection.TypeText(text)
        # wdStyleHeading1 = -2
        # Start at -2 for Level 1, -3 for Level 2... -> -1 - level
        # selection.Style = -1 - level 
        # Pero vamos a intentar dejarlo simple: escribir y luego aplicar estilo si fuera necesario, 
        # o simplemente escribir un parrafo.
        # Para simplificar, asumiremos que el usuario formatea o usaremos 'TypeParagraph'
        selection.Range.Style = -1 - level  # wdStyleHeadingX
        selection.TypeParagraph()
        # Reset to Normal to avoid next text being Heading
        selection.Style = -1 # wdStyleNormal
        return True

    def _preprocess_latex_to_unicode(self, text):
        """Reemplaza comandos comunes de LaTeX por caracteres Unicode que Word entiende."""
        replacements = {
            r"\sqrt": "\u221A",
            r"\sigma": "\u03C3", 
            r"\pi": "\u03C0",
            r"\int": "\u222B",
            r"\sum": "\u2211",
            r"\Delta": "\u0394",
            r"\gamma": "\u03B3",
            r"\alpha": "\u03B1",
            r"\beta": "\u03B2",
            r"\theta": "\u03B8",
            r"\lambda": "\u03BB",
            r"\phi": "\u03C6",
            r"\omega": "\u03C9",
            r"\infty": "\u221E",
            r"\approx": "\u2248",
            r"\neq": "\u2260",
            r"\leq": "\u2264",
            r"\geq": "\u2265",
        }
        
        processed = text
        for latex, unicode_char in replacements.items():
            processed = processed.replace(latex, unicode_char)
        return processed

    def insert_equation(self, equation_text):
        """
        Inserta una ecuación controlando el objeto OMath directamente para asegurar
        el formateo correcto (BuildUp).
        """
        if not self.word_app: return False

        try:
            # Preprocesar LaTeX -> Unicode antes de insertar
            equation_text = self._preprocess_latex_to_unicode(equation_text)

            selection = self.word_app.Selection
            # Usar un rango duplicado para no depender de la selección visual
            rng = selection.Range
            rng.Collapse(0) # wdCollapseEnd (asegurar que es un punto)
            
            # 1. Crear el contenedor OMath vacío en el punto
            # BUG FIX: comtypes a veces devuelve int/Range incorrecto desde Add()
            # Recuperamos el objeto real de la colección
            omaths = rng.OMaths
            omaths.Add(rng)
            omath = omaths(omaths.Count)
            
            # 2. Asignar el texto al RANGO de la ecuación
            # Esto es clave: al asignar al rango del OMath, Word lo trata como Linear Math
            omath.Range.Text = equation_text
            
            # 3. Forzar conversión a formato profesional
            omath.BuildUp()
            
            # 4. Mover la selección después de la ecuación
            # Usamos el final del rango de la ecuación ya procesada
            end_pos = omath.Range.End
            selection.SetRange(end_pos, end_pos)
            
            # 5. Salto de línea
            selection.TypeParagraph()
            
            return True
            
        except Exception as e:
            logger.error(f"Error insertando ecuación: {e}")
            return False

    def insert_table_from_data(self, headers, data):
        """
        Inserta una tabla en la posición del cursor.
        headers: Lista de strings
        data: Lista de listas de strings
        """
        if not self.word_app: return False
        
        selection = self.word_app.Selection
        doc = self.active_doc
        
        rows = len(data) + 1
        cols = len(headers)
        
        # Crear tabla en el rango de selección
        # Word.Range, NumRows, NumColumns, DefaultTableBehavior, AutoFitBehavior
        table = doc.Tables.Add(selection.Range, rows, cols)
        
        # Estilo de tabla (opcional)
        try:
            table.Style = "Table Grid" # Nombre estándar en inglés, a veces funciona en español "Tabla con cuadrícula"
        except:
            pass # Si falla el estilo, seguimos sin estilo

        # Llenar headers
        for col_idx, header in enumerate(headers):
            # Cell(fila, col) -> 1-based index
            cell = table.Cell(1, col_idx + 1)
            cell.Range.Text = str(header)
            cell.Range.Bold = True

        # Llenar datos
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                cell = table.Cell(row_idx + 2, col_idx + 1)
                cell.Range.Text = str(cell_data)

        # Mover cursor fuera de la tabla (después de la tabla)
        # table.Range.Collapse(0) # wdCollapseEnd
        # selection.EndKey(6) # wdStory ? No, solo queremos salir de la tabla.
        
        # Una forma robusta de salir de la tabla es seleccionar el rango despues de la tabla
        pass
