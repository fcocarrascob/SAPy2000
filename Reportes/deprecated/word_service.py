import comtypes.client
import logging
import re
# from .equation_translator import validate_equation, expand_symbols # DEPRECATED

logger = logging.getLogger(__name__)

class WordService:
    """
    Servicio para interactuar con Microsoft Word con comtypes.
    """
    def __init__(self):
        self.word_app = None
        self.active_doc = None

    def _set_style(self, selection, style_name="Normal"):
        """Aplica un estilo de forma defensiva para evitar heredar títulos."""
        if not selection:
            return False
        try:
            doc = self.get_active_document()
            if doc:
                styles = doc.Styles
                if style_name:
                    try:
                        selection.Style = styles(style_name)
                        return True
                    except Exception:
                        pass
                if style_name == "Normal":
                    try:
                        selection.Style = styles("Normal")
                        return True
                    except Exception:
                        pass
            if style_name == "Normal":
                selection.Style = -1  # wdStyleNormal
                return True
            if style_name:
                selection.Style = style_name
                return True
        except Exception as e:
            logger.debug(f"No se pudo aplicar estilo {style_name}: {e}")
        return False

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
        selection.Collapse(0)  # wdCollapseEnd para no sobrescribir contenido
        self._set_style(selection, style)

        # Si no hay delimitadores $, comportamiento standard rápido
        if "$" not in text:
            selection.TypeText(text)
            selection.TypeParagraph()
            self._set_style(selection, style)
            return True
            
        # Parsear contenido mixto
        parts = re.split(r'(\$.*?\$)', text)
        
        for part in parts:
            if not part: continue
            
            if part.startswith('$') and part.endswith('$') and len(part) > 2:
                # Es ecuación inline (Raw LaTeX)
                math_content = part[1:-1] # Quitar $
                
                # MÉTODO SEGURO: Usar TypeText + selección inversa
                start_pos = selection.Range.Start
                selection.TypeText(math_content)
                end_pos = selection.Range.Start
                
                # Crear rango sobre el texto recién insertado
                doc = self.get_active_document()
                eq_range = doc.Range(start_pos, end_pos)
                
                # Convertir a OMath
                omaths = eq_range.OMaths
                omaths.Add(eq_range)
                omath = omaths(omaths.Count)
                
                try:
                    # NO HACEMOS BuildUp()
                    # Dejamos el LaTeX crudo para que el usuario lo convierta manualmente (o Word lo detecte si está configurado)
                    # Forzar modo inline para que fluya con el texto
                    omath.Range.OMaths(1).Type = 1 # wdOMathInline
                except Exception as e:
                    logger.debug(f"Error inline math setup: {e}")
                
                # Mover cursor al final de la ecuación
                selection.SetRange(omath.Range.End, omath.Range.End)
            else:
                # Texto normal
                selection.TypeText(part)
        
        selection.TypeParagraph()
        self._set_style(selection, style)
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
        if not self.word_app: return False

        selection = self.word_app.Selection
        selection.TypeText(text)
        selection.Range.Style = -1 - level
        selection.TypeParagraph()
        selection.Style = -1
        return True

    def insert_equation(self, equation_text):
        """
        Inserta una ecuación en formato LaTeX (RAW) centrada (Display) en Word.
        """
        if not self.word_app: 
            return False

        try:
            logger.debug(f"Insertando LaTeX Raw: {equation_text}")
            
            selection = self.word_app.Selection
            selection.Collapse(0)  # wdCollapseEnd - Evita sobrescribir
            self._set_style(selection, "Normal")
            
            doc = self.get_active_document()
            
            # 3. Guardar posición e insertar texto de ecuación (sin traducción)
            start_pos = selection.Range.Start
            selection.TypeText(equation_text)
            end_pos = selection.Range.Start
            
            # 4. Crear rango sobre el texto recién insertado
            eq_range = doc.Range(start_pos, end_pos)
            
            # 5. Convertir el rango a OMath
            omaths = eq_range.OMaths
            omaths.Add(eq_range)
            omath = omaths(omaths.Count)
            
            # 6. Configurar
            try:
                # Cambiar a Display (centrado) - wdOMathDisplay = 0
                omath.Range.OMaths(1).Type = 0
            except Exception as e:
                logger.debug(f"Error configurando OMath: {e}")
            
            # 7. Mover cursor al final de la ecuación e insertar nuevo párrafo
            selection.SetRange(omath.Range.End, omath.Range.End)
            selection.TypeParagraph()
            self._set_style(selection, "Normal")
            
            return True
            
        except Exception as e:
            logger.error(f"Error insertando ecuación: {e}")
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
        
        table = doc.Tables.Add(selection.Range, rows, cols)
        
        try:
            table.Style = "Table Grid"
        except:
            pass

        for col_idx, header in enumerate(headers):
            cell = table.Cell(1, col_idx + 1)
            cell.Range.Text = str(header)
            cell.Range.Bold = True

        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                cell = table.Cell(row_idx + 2, col_idx + 1)
                cell.Range.Text = str(cell_data)
        
        selection.SetRange(table.Range.End, table.Range.End)
        selection.TypeParagraph()
