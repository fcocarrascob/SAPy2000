"""
Test Suite: Detección del Bug de BuildUp en Ecuaciones Word

Este módulo contiene tests para identificar y diagnosticar el problema donde
el método BuildUp() de Word OMML consume texto más allá del rango de la ecuación.

Ejecutar con:
    python -m unittest Reportes.tests.test_equation_buildup -v

O desde la carpeta Reportes:
    python -m unittest tests.test_equation_buildup -v
"""
import unittest
import time
import comtypes.client
import logging

# Configurar logging para ver detalles
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WordTestCase(unittest.TestCase):
    """
    Clase base para tests que interactúan con Word.
    Maneja la conexión/desconexión de Word y creación de documentos.
    """
    
    @classmethod
    def setUpClass(cls):
        """Conectar a Word una vez para todos los tests de la clase."""
        try:
            cls.word_app = comtypes.client.GetActiveObject("Word.Application")
            logger.info("Conectado a instancia activa de Word")
        except Exception:
            cls.word_app = comtypes.client.CreateObject("Word.Application")
            cls.word_app.Visible = True
            logger.info("Nueva instancia de Word creada")
        
        cls.word_app.Visible = True
    
    @classmethod
    def tearDownClass(cls):
        """Limpiar después de todos los tests."""
        # No cerramos Word para que el usuario pueda inspeccionar
        pass
    
    def setUp(self):
        """Crear documento nuevo para cada test."""
        self.doc = self.word_app.Documents.Add()
        self.selection = self.word_app.Selection
        time.sleep(0.3)  # Dar tiempo a Word para estabilizarse
    
    def tearDown(self):
        """Cerrar documento sin guardar después de cada test."""
        # Comentar la siguiente línea para mantener documentos abiertos e inspeccionar
        # self.doc.Close(0)  # 0 = wdDoNotSaveChanges
        pass
    
    def get_full_document_text(self):
        """Obtiene todo el texto del documento."""
        return self.doc.Content.Text
    
    def insert_marker_text(self, marker_text):
        """Inserta texto marcador que usaremos para verificar integridad."""
        self.selection.TypeText(marker_text)
    
    def insert_paragraph(self):
        """Inserta un salto de párrafo."""
        self.selection.TypeParagraph()


class TestBuildUpTextConsumption(WordTestCase):
    """
    Tests para detectar cuándo y cómo BuildUp consume texto.
    """
    
    def test_01_baseline_text_only(self):
        """
        BASELINE: Insertar solo texto sin ecuaciones.
        Esto establece que el mecanismo básico funciona.
        """
        marker_before = "ANTES_DE_ECUACION"
        marker_after = "DESPUES_DE_ECUACION"
        
        self.insert_marker_text(marker_before)
        self.insert_paragraph()
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        
        self.assertIn(marker_before, full_text, 
                      "El texto ANTES debería estar presente")
        self.assertIn(marker_after, full_text, 
                      "El texto DESPUES debería estar presente")
        
        logger.info(f"[BASELINE] Documento: {repr(full_text)}")
    
    def test_02_display_equation_with_buffer(self):
        """
        Test ecuación DISPLAY usando la estrategia de buffer (3 párrafos).
        Esta es la implementación actual que debería funcionar.
        """
        marker_before = "TEXTO_ANTES_DISPLAY"
        marker_after = "TEXTO_DESPUES_DISPLAY"
        equation_text = "x = (a + b)/c"
        
        # 1. Insertar texto antes
        self.insert_marker_text(marker_before)
        self.insert_paragraph()
        
        # 2. Insertar ecuación CON BUFFER (como en word_service.insert_equation)
        self._insert_equation_with_buffer(equation_text)
        
        # 3. Insertar texto después
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[DISPLAY+BUFFER] Documento: {repr(full_text)}")
        
        self.assertIn(marker_before, full_text, 
                      "DISPLAY+BUFFER: El texto ANTES fue consumido!")
        self.assertIn(marker_after, full_text, 
                      "DISPLAY+BUFFER: El texto DESPUES fue consumido!")
    
    def test_03_inline_equation_NO_buffer(self):
        """
        Test ecuación INLINE SIN buffer.
        Este es el escenario que probablemente falla.
        """
        marker_after = "TEXTO_DESPUES_INLINE"
        equation_text = "E = mc^2"
        
        # 1. Insertar ecuación SIN buffer (como en insert_text_at_cursor actual)
        self._insert_inline_equation_no_buffer(equation_text)
        
        # 2. Continuar escribiendo en la misma línea
        self.selection.TypeText(" y también ")
        self.insert_paragraph()
        
        # 3. Insertar texto en siguiente línea
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[INLINE SIN BUFFER] Documento: {repr(full_text)}")
        
        # Este test puede FALLAR - eso es lo que queremos detectar
        self.assertIn(marker_after, full_text, 
                      "INLINE SIN BUFFER: El texto DESPUES fue CONSUMIDO por BuildUp!")
        self.assertIn("y también", full_text,
                      "INLINE SIN BUFFER: El texto intermedio fue CONSUMIDO!")
    
    def test_04_inline_equation_followed_by_paragraph(self):
        """
        Test: Ecuación inline seguida inmediatamente por un nuevo párrafo.
        Escenario común donde BuildUp puede consumir el párrafo siguiente.
        """
        equation_text = "α + β = γ"
        marker_next_para = "PARRAFO_SIGUIENTE_INTACTO"
        
        # Simular lo que hace insert_text_at_cursor
        # 1. Escribir la ecuación inline
        self._insert_inline_equation_no_buffer(equation_text)
        
        # 2. Terminar el párrafo actual
        self.insert_paragraph()
        
        # 3. Escribir en el siguiente párrafo
        self.insert_marker_text(marker_next_para)
        
        full_text = self.get_full_document_text()
        logger.info(f"[INLINE + PARRAFO] Documento: {repr(full_text)}")
        
        self.assertIn(marker_next_para, full_text,
                      "El párrafo siguiente a la ecuación inline fue CONSUMIDO!")
    
    def test_05_multiple_inline_equations_same_paragraph(self):
        """
        Test: Múltiples ecuaciones inline en el mismo párrafo.
        """
        text_1 = "Sabemos que "
        eq_1 = "a^2 + b^2 = c^2"
        text_2 = " y además "
        eq_2 = "x = (-b ± √(b^2-4ac))/(2a)"
        text_3 = " son fórmulas importantes."
        marker = "FIN_PARRAFO_MULTIPLE"
        
        self.selection.TypeText(text_1)
        self._insert_inline_equation_no_buffer(eq_1)
        self.selection.TypeText(text_2)
        self._insert_inline_equation_no_buffer(eq_2)
        self.selection.TypeText(text_3)
        self.insert_paragraph()
        self.insert_marker_text(marker)
        
        full_text = self.get_full_document_text()
        logger.info(f"[MULTIPLE INLINE] Documento: {repr(full_text)}")
        
        self.assertIn("Sabemos que", full_text, "Texto inicial consumido")
        self.assertIn("y además", full_text, "Texto intermedio consumido")
        self.assertIn("son fórmulas", full_text, "Texto final consumido")
        self.assertIn(marker, full_text, "Marcador siguiente consumido")
    
    def test_06_inline_at_end_of_paragraph(self):
        """
        Test: Ecuación inline al FINAL del párrafo, seguida de nuevo contenido.
        Este es un escenario crítico para el bug.
        """
        text_before = "El valor final es "
        equation = "Δx/Δt"
        marker_next = "LINEA_SIGUIENTE_IMPORTANTE"
        
        self.selection.TypeText(text_before)
        self._insert_inline_equation_no_buffer(equation)
        # NO hay texto después de la ecuación en este párrafo
        self.insert_paragraph()
        self.insert_marker_text(marker_next)
        
        full_text = self.get_full_document_text()
        logger.info(f"[INLINE AL FINAL] Documento: {repr(full_text)}")
        
        self.assertIn(text_before, full_text, "Texto antes de ecuación consumido")
        self.assertIn(marker_next, full_text, 
                      "CRÍTICO: Línea siguiente CONSUMIDA por BuildUp!")
    
    def test_07_stress_buildup_paragraph_count(self):
        """
        Test de stress: Determinar cuántos párrafos consume BuildUp.
        Insertamos N párrafos después de la ecuación y verificamos cuántos sobreviven.
        """
        equation = "∫_0^∞ e^(-x^2) dx = √π/2"
        num_paragraphs = 5
        markers = [f"PARRAFO_{i}" for i in range(num_paragraphs)]
        
        # Insertar ecuación sin buffer
        self._insert_inline_equation_no_buffer(equation)
        self.insert_paragraph()
        
        # Insertar N párrafos con marcadores
        for marker in markers:
            self.insert_marker_text(marker)
            self.insert_paragraph()
        
        full_text = self.get_full_document_text()
        logger.info(f"[STRESS TEST] Documento: {repr(full_text)}")
        
        # Contar cuántos marcadores sobrevivieron
        survived = sum(1 for m in markers if m in full_text)
        consumed = num_paragraphs - survived
        
        logger.info(f"[STRESS TEST] Párrafos insertados: {num_paragraphs}")
        logger.info(f"[STRESS TEST] Párrafos sobrevivientes: {survived}")
        logger.info(f"[STRESS TEST] Párrafos CONSUMIDOS: {consumed}")
        
        if consumed > 0:
            self.fail(f"BuildUp consumió {consumed} de {num_paragraphs} párrafos!")
    
    # =========================================================================
    # MÉTODOS HELPER PARA INSERTAR ECUACIONES
    # =========================================================================
    
    def _insert_equation_with_buffer(self, equation_text):
        """
        Inserta ecuación DISPLAY con estrategia de buffer (3 párrafos).
        Replica la lógica de word_service.insert_equation()
        """
        selection = self.selection
        doc = self.doc
        
        # Insertar 3 párrafos de buffer
        for _ in range(3):
            selection.TypeParagraph()
        
        # Retroceder 3 párrafos (wdParagraph=4, wdMove=0)
        selection.MoveUp(4, 3, 0)
        
        # Guardar posición e insertar ecuación
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        # Crear rango y convertir a OMath
        eq_range = doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0  # wdOMathDisplay
        except Exception as e:
            logger.debug(f"BuildUp (buffer): {e}")
        
        # Mover cursor al final
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
    
    def _insert_inline_equation_no_buffer(self, equation_text):
        """
        Inserta ecuación INLINE SIN buffer.
        Replica la lógica de word_service.insert_text_at_cursor() para ecuaciones.
        """
        selection = self.selection
        doc = self.doc
        
        # Guardar posición e insertar texto de ecuación
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        # Crear rango sobre el texto insertado
        eq_range = doc.Range(start_pos, end_pos)
        
        # Convertir a OMath
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 1  # wdOMathInline
        except Exception as e:
            logger.debug(f"BuildUp (inline): {e}")
        
        # Mover cursor al final de la ecuación
        selection.SetRange(omath.Range.End, omath.Range.End)


class TestBuildUpMitigationStrategies(WordTestCase):
    """
    Tests para evaluar diferentes estrategias de mitigación del bug.
    """
    
    def test_strategy_01_inline_with_buffer(self):
        """
        ESTRATEGIA 1: Aplicar la misma técnica de buffer a ecuaciones inline.
        """
        marker_after = "TEXTO_POST_INLINE_BUFFER"
        equation = "F = ma"
        
        self._insert_inline_with_buffer(equation, buffer_count=1)
        self.selection.TypeText(" continúa aquí")
        self.insert_paragraph()
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[ESTRATEGIA BUFFER-1] Documento: {repr(full_text)}")
        
        self.assertIn("continúa aquí", full_text, "Texto inline perdido")
        self.assertIn(marker_after, full_text, "Párrafo siguiente perdido")
    
    def test_strategy_02_use_insertafter(self):
        """
        ESTRATEGIA 2: Usar Range.InsertAfter en lugar de TypeText.
        """
        marker_after = "TEXTO_POST_INSERTAFTER"
        equation = "V = IR"
        
        self._insert_inline_with_insertafter(equation)
        self.insert_paragraph()
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[ESTRATEGIA INSERTAFTER] Documento: {repr(full_text)}")
        
        self.assertIn(marker_after, full_text, "InsertAfter no protegió el texto")
    
    def test_strategy_03_collapse_after_buildup(self):
        """
        ESTRATEGIA 3: Colapsar explícitamente el rango después de BuildUp.
        """
        marker_after = "TEXTO_POST_COLLAPSE"
        equation = "P = UI"
        
        self._insert_inline_with_collapse(equation)
        self.insert_paragraph()
        self.insert_marker_text(marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[ESTRATEGIA COLLAPSE] Documento: {repr(full_text)}")
        
        self.assertIn(marker_after, full_text, "Collapse no protegió el texto")
    
    def test_strategy_04_bookmark_protection(self):
        """
        ESTRATEGIA 4: Usar bookmark para proteger contenido siguiente.
        """
        marker_after = "TEXTO_POST_BOOKMARK"
        equation = "ρ = m/V"
        
        self._insert_inline_with_bookmark_protection(equation, marker_after)
        
        full_text = self.get_full_document_text()
        logger.info(f"[ESTRATEGIA BOOKMARK] Documento: {repr(full_text)}")
        
        self.assertIn(marker_after, full_text, "Bookmark no protegió el texto")
    
    # =========================================================================
    # IMPLEMENTACIONES DE ESTRATEGIAS
    # =========================================================================
    
    def _insert_inline_with_buffer(self, equation_text, buffer_count=1):
        """Estrategia: Buffer mínimo para inline."""
        selection = self.selection
        doc = self.doc
        
        # Insertar buffer mínimo
        for _ in range(buffer_count):
            selection.TypeParagraph()
        
        # Retroceder
        selection.MoveUp(4, buffer_count, 0)
        
        # Insertar ecuación
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        eq_range = doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 1
        except Exception as e:
            logger.debug(f"BuildUp (inline+buffer): {e}")
        
        selection.SetRange(omath.Range.End, omath.Range.End)
    
    def _insert_inline_with_insertafter(self, equation_text):
        """Estrategia: Usar InsertAfter para el texto de ecuación."""
        selection = self.selection
        doc = self.doc
        
        # Crear un rango en la posición actual
        current_range = selection.Range
        start_pos = current_range.Start
        
        # Usar InsertAfter en lugar de TypeText
        current_range.InsertAfter(equation_text)
        end_pos = start_pos + len(equation_text)
        
        # Crear rango sobre el texto insertado
        eq_range = doc.Range(start_pos, end_pos)
        
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 1
        except Exception as e:
            logger.debug(f"BuildUp (insertafter): {e}")
        
        selection.SetRange(omath.Range.End, omath.Range.End)
    
    def _insert_inline_with_collapse(self, equation_text):
        """Estrategia: Colapsar rango explícitamente después de BuildUp."""
        selection = self.selection
        doc = self.doc
        
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        eq_range = doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 1
        except Exception as e:
            logger.debug(f"BuildUp (collapse): {e}")
        
        # ESTRATEGIA: Colapsar el rango de la ecuación al final
        final_range = omath.Range
        final_range.Collapse(0)  # wdCollapseEnd
        
        # Mover selección al final colapsado
        selection.SetRange(final_range.Start, final_range.End)
    
    def _insert_inline_with_bookmark_protection(self, equation_text, marker_after):
        """Estrategia: Insertar texto futuro primero, proteger con bookmark."""
        selection = self.selection
        doc = self.doc
        
        # 1. Primero insertar el contenido que queremos proteger
        bookmark_name = "ProtectedContent"
        self.insert_paragraph()
        
        # Guardar posición del contenido a proteger
        protect_start = selection.Range.Start
        selection.TypeText(marker_after)
        protect_end = selection.Range.Start
        
        # Crear bookmark sobre el contenido a proteger
        protect_range = doc.Range(protect_start, protect_end)
        doc.Bookmarks.Add(bookmark_name, protect_range)
        
        # 2. Volver arriba e insertar la ecuación
        selection.MoveUp(4, 1, 0)  # Subir un párrafo
        selection.HomeKey(5, 0)    # Ir al inicio de línea (wdLine=5)
        
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        eq_range = doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 1
        except Exception as e:
            logger.debug(f"BuildUp (bookmark): {e}")
        
        # 3. Recuperar contenido del bookmark y verificar que sigue ahí
        try:
            bookmark_range = doc.Bookmarks(bookmark_name).Range
            logger.info(f"Bookmark content: {bookmark_range.Text}")
        except Exception as e:
            logger.warning(f"Bookmark perdido: {e}")
        
        # Mover al final del documento
        selection.EndKey(6, 0)  # wdStory = 6


class TestRealWorldScenarios(WordTestCase):
    """
    Tests que replican escenarios reales de uso del sistema de reportes.
    """
    
    def test_snippet_with_text_equation_text(self):
        """
        Escenario real: Snippet con texto, ecuación display, más texto.
        Esto simula process_blocks de template_engine.
        """
        blocks = [
            {"type": "text", "content": "Introducción al problema."},
            {"type": "equation", "content": "σ = F/A"},
            {"type": "text", "content": "Donde σ es el esfuerzo."},
        ]
        
        for block in blocks:
            if block["type"] == "text":
                self.selection.TypeText(block["content"])
                self.insert_paragraph()
            elif block["type"] == "equation":
                self._insert_equation_with_buffer(block["content"])
        
        full_text = self.get_full_document_text()
        logger.info(f"[SNIPPET REAL] Documento: {repr(full_text)}")
        
        self.assertIn("Introducción", full_text)
        self.assertIn("Donde", full_text, "Texto después de ecuación display CONSUMIDO!")
    
    def test_snippet_with_inline_equations_in_text(self):
        """
        Escenario real: Texto con ecuaciones inline ($...$).
        """
        text_with_inline = "La energía es $E = mc^2$ y la fuerza es $F = ma$."
        next_paragraph = "Este párrafo debe permanecer intacto."
        
        # Simular insert_text_at_cursor con ecuaciones inline
        self._process_text_with_inline_equations(text_with_inline)
        self.insert_paragraph()
        self.selection.TypeText(next_paragraph)
        
        full_text = self.get_full_document_text()
        logger.info(f"[INLINE EN TEXTO] Documento: {repr(full_text)}")
        
        self.assertIn("La energía es", full_text)
        self.assertIn("y la fuerza es", full_text)
        self.assertIn("intacto", full_text, 
                      "Párrafo siguiente a inline CONSUMIDO!")
    
    def _insert_equation_with_buffer(self, equation_text):
        """Replica insert_equation de word_service."""
        selection = self.selection
        doc = self.doc
        
        for _ in range(3):
            selection.TypeParagraph()
        selection.MoveUp(4, 3, 0)
        
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        eq_range = doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0
        except Exception as e:
            logger.debug(f"BuildUp: {e}")
        
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
    
    def _process_text_with_inline_equations(self, text):
        """Simula el procesamiento de texto con $...$ de insert_text_at_cursor."""
        import re
        parts = re.split(r'(\$.*?\$)', text)
        
        for part in parts:
            if not part:
                continue
            if part.startswith('$') and part.endswith('$') and len(part) > 2:
                eq_content = part[1:-1]
                # Insertar inline SIN buffer (problema actual)
                start_pos = self.selection.Range.Start
                self.selection.TypeText(eq_content)
                end_pos = self.selection.Range.Start
                
                eq_range = self.doc.Range(start_pos, end_pos)
                omaths = eq_range.OMaths
                omaths.Add(eq_range)
                omath = omaths(omaths.Count)
                
                try:
                    omath.BuildUp()
                    omath.Range.OMaths(1).Type = 1
                except Exception as e:
                    logger.debug(f"Inline BuildUp: {e}")
                
                self.selection.SetRange(omath.Range.End, omath.Range.End)
            else:
                self.selection.TypeText(part)


if __name__ == '__main__':
    # Ejecutar tests con verbose output
    unittest.main(verbosity=2)
