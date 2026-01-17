"""
Test de Validación: Verificar que la corrección en WordService funciona.

Este test usa el WordService real (no mocks) para confirmar que
las ecuaciones inline ya no fragmentan el texto.

Ejecutar con:
    python -m unittest Reportes.tests.test_wordservice_fix -v
"""
import unittest
import time
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Reportes.word_service import WordService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWordServiceInlineEquationFix(unittest.TestCase):
    """
    Tests de integración usando WordService real.
    """
    
    @classmethod
    def setUpClass(cls):
        """Inicializar WordService una vez."""
        cls.ws = WordService()
        cls.ws.connect()
    
    def setUp(self):
        """Crear documento nuevo para cada test."""
        self.doc = self.ws.create_new_document()
        time.sleep(0.3)
    
    def tearDown(self):
        """Mantener documentos abiertos para inspección."""
        pass
    
    def get_document_text(self):
        """Obtiene el texto completo del documento."""
        return self.doc.Content.Text
    
    def count_paragraph_breaks(self, text):
        """Cuenta los saltos de párrafo en el texto."""
        return text.count('\r')
    
    def test_01_simple_inline_equation(self):
        """
        Test: Ecuación inline simple no debe fragmentar.
        ANTES del fix: "La energía es E = m\rc\r2\r"
        DESPUÉS del fix: "La energía es E = mc² ..."
        """
        self.ws.insert_text_at_cursor("La energía es $E = mc^2$ según Einstein.", "Normal")
        self.ws.insert_text_at_cursor("Esta línea debe estar separada.", "Normal")
        
        full_text = self.get_document_text()
        paragraph_count = self.count_paragraph_breaks(full_text)
        
        logger.info(f"[TEST SIMPLE INLINE]")
        logger.info(f"  Texto: {repr(full_text)}")
        logger.info(f"  Saltos de párrafo: {paragraph_count}")
        
        # Con el fix, debería haber exactamente 2 párrafos (uno por cada insert_text_at_cursor)
        # Sin el fix, habría más debido a la fragmentación de la ecuación
        self.assertIn("Einstein", full_text, "El texto después de la ecuación fue consumido")
        self.assertIn("separada", full_text, "La línea siguiente fue consumida")
        
        # Verificar que no hay fragmentación excesiva (máximo 3 párrafos es razonable)
        self.assertLessEqual(paragraph_count, 3, 
                             f"Demasiados saltos de párrafo ({paragraph_count}), posible fragmentación")
    
    def test_02_fraction_inline_equation(self):
        """
        Test: Fracción inline - caso más problemático.
        """
        self.ws.insert_text_at_cursor("El cociente es $a/b$ donde b≠0.", "Normal")
        self.ws.insert_text_at_cursor("MARCADOR_INTACTO", "Normal")
        
        full_text = self.get_document_text()
        
        logger.info(f"[TEST FRACCIÓN]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("donde", full_text, "Texto después de fracción consumido")
        self.assertIn("MARCADOR_INTACTO", full_text, "Línea siguiente consumida")
    
    def test_03_multiple_inline_equations(self):
        """
        Test: Múltiples ecuaciones inline en el mismo párrafo.
        """
        text = "Sabemos que $a^2 + b^2 = c^2$ y también $E = mc^2$ son famosas."
        self.ws.insert_text_at_cursor(text, "Normal")
        self.ws.insert_text_at_cursor("LÍNEA_SIGUIENTE_INTACTA", "Normal")
        
        full_text = self.get_document_text()
        
        logger.info(f"[TEST MÚLTIPLES INLINE]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("Sabemos", full_text)
        self.assertIn("y también", full_text, "Texto entre ecuaciones consumido")
        self.assertIn("famosas", full_text, "Texto final de línea consumido")
        self.assertIn("INTACTA", full_text, "Línea siguiente consumida")
    
    def test_04_inline_at_end_of_paragraph(self):
        """
        Test: Ecuación inline al final del párrafo.
        """
        self.ws.insert_text_at_cursor("El resultado final es $x = 42$", "Normal")
        self.ws.insert_text_at_cursor("Este párrafo viene después.", "Normal")
        
        full_text = self.get_document_text()
        
        logger.info(f"[TEST INLINE AL FINAL]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("resultado", full_text)
        self.assertIn("viene después", full_text, "Párrafo siguiente consumido")
    
    def test_05_display_equation_still_works(self):
        """
        Test: Ecuaciones display (no inline) siguen funcionando.
        """
        self.ws.insert_text_at_cursor("Introducción al teorema:", "Normal")
        self.ws.insert_equation("x = (-b ± √(b^2 - 4ac))/(2a)")
        self.ws.insert_text_at_cursor("Donde a, b, c son coeficientes.", "Normal")
        
        full_text = self.get_document_text()
        
        logger.info(f"[TEST DISPLAY EQUATION]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("Introducción", full_text)
        self.assertIn("coeficientes", full_text, "Texto después de ecuación display consumido")
    
    def test_06_mixed_content(self):
        """
        Test: Contenido mixto - texto normal, inline y display.
        """
        self.ws.insert_text_at_cursor("La física tiene ecuaciones como $F = ma$ en línea.", "Normal")
        self.ws.insert_equation("E = mc^2")
        self.ws.insert_text_at_cursor("Y también $P = UI$ para potencia.", "Normal")
        self.ws.insert_text_at_cursor("FIN DEL DOCUMENTO", "Normal")
        
        full_text = self.get_document_text()
        
        logger.info(f"[TEST MIXTO]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("física", full_text)
        self.assertIn("en línea", full_text)
        self.assertIn("potencia", full_text)
        self.assertIn("FIN DEL DOCUMENTO", full_text, "Texto final consumido")


class TestWordServiceRegressionCheck(unittest.TestCase):
    """
    Tests de regresión para asegurar que el fix no rompe funcionalidad existente.
    """
    
    @classmethod
    def setUpClass(cls):
        cls.ws = WordService()
        cls.ws.connect()
    
    def setUp(self):
        self.doc = self.ws.create_new_document()
        time.sleep(0.2)
    
    def test_text_without_equations(self):
        """
        Regresión: Texto sin ecuaciones sigue funcionando.
        """
        self.ws.insert_text_at_cursor("Línea 1 sin ecuaciones.", "Normal")
        self.ws.insert_text_at_cursor("Línea 2 también normal.", "Normal")
        
        full_text = self.doc.Content.Text
        
        self.assertIn("Línea 1", full_text)
        self.assertIn("Línea 2", full_text)
    
    def test_special_characters(self):
        """
        Regresión: Caracteres especiales sin $ no se confunden.
        """
        self.ws.insert_text_at_cursor("El precio es 100$ o más.", "Normal")
        
        full_text = self.doc.Content.Text
        
        # Con un solo $, no debería interpretarse como ecuación
        self.assertIn("precio", full_text)
    
    def test_greek_symbols_inline(self):
        """
        Regresión: Símbolos griegos en ecuaciones inline.
        """
        self.ws.insert_text_at_cursor("La constante $\\alpha + \\beta = \\gamma$ es importante.", "Normal")
        
        full_text = self.doc.Content.Text
        
        self.assertIn("constante", full_text)
        self.assertIn("importante", full_text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
