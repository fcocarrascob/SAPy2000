import comtypes.client
import logging
import re
from .equation_translator import validate_equation, expand_symbols

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
        """
        Inserta texto en la posición del cursor con soporte para ecuaciones inline ($...$).
        Ej: "El valor de $x$ es..."
        """
        if not self.word_app: 
            return False
            
        selection = self.word_app.Selection
        
        # Aplicar estilo primero
        try:
            # wdStyleNormal = -1
            target_style = style if style != "Normal" else -1
            selection.Style = target_style
        except:
            pass 

        # Si no hay delimitadores $, comportamiento standard rápido
        if "$" not in text:
            selection.TypeText(text)
            selection.TypeParagraph()
            return True
            
        # Parsear contenido mixto
        parts = re.split(r'(\$.*?\$)', text)
        
        for part in parts:
            if not part: continue
            
            if part.startswith('$') and part.endswith('$') and len(part) > 2:
                # Es ecuación inline
                math_content = part[1:-1] # Quitar $
                
                # Expandir símbolos (si el usuario escribió \alpha)
                math_unicode = expand_symbols(math_content)

                rng = selection.Range
                rng.Collapse(0) # wdCollapseEnd
                
                # Insertar ecuación
                omaths = rng.OMaths
                omaths.Add(rng)
                omath = omaths(omaths.Count)
                omath.Range.Text = math_unicode
                
                try:
                    omath.BuildUp()
                    # Forzar modo inline para que fluya con el texto
                    omath.Range.OMaths(1).Type = 1 # wdOMathInline
                except Exception as e:
                    logger.debug(f"Error inline math build: {e}")
                
                # Mover cursor al final de la ecuación
                selection.SetRange(omath.Range.End, omath.Range.End)
            else:
                # Texto normal
                selection.TypeText(part)
        
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

    def insert_equation(self, equation_text):
        """
        Inserta una ecuación UnicodeMath en Word.
        
        Flujo:
        1. Valida la sintaxis de la ecuación
        2. Expande símbolos \\command a Unicode si los hay
        3. Crea objeto OMath y aplica BuildUp para renderizar
        
        NOTA: El contenido ya debe estar en sintaxis UnicodeMath nativa.
        """
        if not self.word_app: 
            return False

        try:
            # 1. Validar ecuación
            is_valid, error_msg = validate_equation(equation_text)
            if not is_valid:
                logger.warning(f"Ecuación con posibles errores: {error_msg}")
            
            # 2. Expandir símbolos \\command a Unicode (si el usuario usó \\alpha, etc)
            equation_unicode = expand_symbols(equation_text)
            logger.debug(f"UnicodeMath: {equation_unicode}")
            
            selection = self.word_app.Selection
            rng = selection.Range
            rng.Collapse(0)  # wdCollapseEnd
            
            # 3. Crear objeto OMath y asignar texto UnicodeMath
            omaths = rng.OMaths
            omaths.Add(rng)
            omath = omaths(omaths.Count)
            
            # Asignar el texto UnicodeMath
            omath.Range.Text = equation_unicode
            
            # 4. BuildUp convierte Linear UnicodeMath a Professional (2D)
            try:
                omath.BuildUp()
            except Exception as e:
                logger.debug(f"BuildUp info: {e}")
            
            # 5. Mover cursor después de la ecuación
            end_pos = omath.Range.End
            selection.SetRange(end_pos, end_pos)
            selection.TypeParagraph()
            
            return True
            
        except Exception as e:
            logger.error(f"Error insertando ecuación: {e}")
            # Fallback: insertar como texto plano
            try:
                self.insert_text_at_cursor(f"[ECUACIÓN: {equation_text}]", "Normal")
            except:
                pass
            return False

    def insert_equation_via_field(self, equation_text):
        """
        Método alternativo: inserta ecuación usando EQ field code.
        Útil como fallback si OMath falla.
        """
        if not self.word_app:
            return False
        
        try:
            selection = self.word_app.Selection
            # wdFieldEquation = 49
            # El campo EQ usa sintaxis diferente, no LaTeX puro
            # Esto es solo un fallback muy básico
            selection.Fields.Add(selection.Range, 49, equation_text, False)
            selection.TypeParagraph()
            return True
        except Exception as e:
            logger.error(f"Error insertando campo EQ: {e}")
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
