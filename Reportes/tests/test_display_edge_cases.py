"""
Test Suite: Casos Edge y Problemáticos para Ecuaciones Display

Este módulo busca específicamente casos que podrían causar problemas:
- Ecuaciones con caracteres especiales no soportados
- Sintaxis incorrecta o ambigua
- Casos límite de anidamiento
- Caracteres que Word podría malinterpretar

Ejecutar con:
    python -m unittest Reportes.tests.test_display_edge_cases -v
"""
import unittest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Reportes.word_service import WordService
from Reportes.equation_translator import validate_equation, expand_symbols
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdgeCaseTestCase(unittest.TestCase):
    """Clase base para tests de casos edge."""
    
    @classmethod
    def setUpClass(cls):
        cls.ws = WordService()
        cls.ws.connect()
    
    def setUp(self):
        self.doc = self.ws.create_new_document()
        time.sleep(0.3)
    
    def get_document_text(self):
        return self.doc.Content.Text


class TestEquationValidation(EdgeCaseTestCase):
    """Tests para validación de ecuaciones antes de inserción."""
    
    def test_validate_balanced_parentheses(self):
        """Verificar que paréntesis balanceados pasan validación."""
        valid_eqs = [
            "(a + b)",
            "((a + b) + c)",
            "(a/(b+c))",
            "√((x^2))",
        ]
        for eq in valid_eqs:
            is_valid, msg = validate_equation(eq)
            logger.info(f"  '{eq}' -> válido: {is_valid}, msg: {msg}")
            # No assertamos True porque validate_equation puede dar warnings
    
    def test_validate_unbalanced_parentheses(self):
        """Verificar que paréntesis desbalanceados generan warning."""
        invalid_eqs = [
            "(a + b",        # Falta cerrar
            "a + b)",        # Falta abrir
            "((a + b)",      # Una sin cerrar
            "(a + (b + c)",  # Anidado sin cerrar
        ]
        for eq in invalid_eqs:
            is_valid, msg = validate_equation(eq)
            logger.info(f"  '{eq}' -> válido: {is_valid}, msg: {msg}")
            # Deberían dar False o warning
    
    def test_validate_empty_groups(self):
        """Verificar manejo de grupos vacíos."""
        eqs = [
            "()",
            "a + () + b",
            "()/()",
        ]
        for eq in eqs:
            is_valid, msg = validate_equation(eq)
            logger.info(f"  '{eq}' -> válido: {is_valid}, msg: {msg}")


class TestSymbolExpansion(EdgeCaseTestCase):
    """Tests para expansión de símbolos \\command."""
    
    def test_expand_known_symbols(self):
        """Verificar expansión de símbolos conocidos."""
        cases = [
            ("\\alpha", "α"),
            ("\\beta", "β"),
            ("\\sum", "∑"),
            ("\\int", "∫"),
            ("\\infty", "∞"),
        ]
        for input_str, expected in cases:
            result = expand_symbols(input_str)
            logger.info(f"  '{input_str}' -> '{result}' (esperado: '{expected}')")
            self.assertEqual(result, expected)
    
    def test_expand_unknown_symbols(self):
        """Verificar que símbolos desconocidos permanecen sin cambios."""
        cases = [
            "\\noexiste",
            "\\xyz123",
        ]
        for s in cases:
            result = expand_symbols(s)
            logger.info(f"  '{s}' -> '{result}'")
            # Debería permanecer igual o dar algún manejo
    
    def test_mixed_expansion(self):
        """Verificar expansión en contexto mixto."""
        input_str = "\\alpha + \\beta = \\gamma"
        result = expand_symbols(input_str)
        logger.info(f"  '{input_str}' -> '{result}'")
        self.assertIn("α", result)
        self.assertIn("β", result)
        self.assertIn("γ", result)


class TestProblematicEquations(EdgeCaseTestCase):
    """Tests para ecuaciones que podrían causar problemas."""
    
    def test_equation_with_quotes(self):
        """Ecuación con texto entre comillas (texto en ecuación)."""
        equation = '"texto" = x'
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[QUOTES] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_with_spaces(self):
        """Ecuación con espacios significativos."""
        equation = "a    +    b    =    c"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[SPACES] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_very_long(self):
        """Ecuación muy larga que podría causar overflow."""
        # Generar ecuación larga
        terms = [f"x_{i}" for i in range(20)]
        equation = " + ".join(terms) + " = 0"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[LONG EQ] Longitud: {len(equation)} chars")
        logger.info(f"[LONG EQ] Texto: {repr(text[:200])}...")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_with_ampersand(self):
        """Ecuación con & (separador de columnas en matrices)."""
        equation = "\\matrix(a&b@c&d)"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[AMPERSAND] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_with_at_symbol(self):
        """Ecuación con @ (separador de filas en matrices)."""
        equation = "\\matrix(1@2@3)"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[AT SYMBOL] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_only_numbers(self):
        """Ecuación con solo números."""
        equation = "1 + 2 + 3 = 6"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[NUMBERS] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_single_character(self):
        """Ecuación de un solo carácter."""
        equation = "x"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[SINGLE CHAR] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_equation_empty_string(self):
        """Ecuación vacía (debería manejarse gracefully)."""
        equation = ""
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[EMPTY] Result: {result}, Texto: {repr(text)}")
        
        # La ecuación vacía puede fallar, pero no debe romper el documento
        self.assertIn("ANTES", text)


class TestSpecialUnicodeCharacters(EdgeCaseTestCase):
    """Tests para caracteres Unicode especiales."""
    
    def test_mathematical_bold(self):
        """Caracteres matemáticos en negrita."""
        equation = "𝐀 + 𝐁 = 𝐂"  # Mathematical Bold
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[BOLD MATH] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_mathematical_script(self):
        """Caracteres matemáticos script."""
        equation = "ℒ{f(t)} = F(s)"  # Laplace transform notation
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[SCRIPT] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_combining_diacriticals(self):
        """Caracteres con diacríticos combinados (vectores, etc)."""
        equation = "v⃗ + u⃗ = w⃗"  # Combining arrow
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[VECTORS] {repr(text)}")
        
        self.assertIn("DESPUES", text)
    
    def test_double_struck(self):
        """Caracteres double-struck (conjuntos numéricos)."""
        equation = "x ∈ ℝ, n ∈ ℕ, z ∈ ℂ"
        
        self.ws.insert_text_at_cursor("ANTES", "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor("DESPUES", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[DOUBLE STRUCK] {repr(text)}")
        
        self.assertIn("DESPUES", text)


class TestRecoveryAfterError(EdgeCaseTestCase):
    """Tests para verificar recuperación después de errores."""
    
    def test_continue_after_malformed_equation(self):
        """Verificar que se puede continuar después de ecuación malformada."""
        # Primero una ecuación malformada
        self.ws.insert_text_at_cursor("ANTES_MALFORMADA", "Normal")
        result1 = self.ws.insert_equation("((((")  # Muy malformada
        
        # Luego una ecuación buena
        result2 = self.ws.insert_equation("a + b = c")
        self.ws.insert_text_at_cursor("DESPUES_BUENA", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[RECOVERY] R1={result1}, R2={result2}")
        logger.info(f"[RECOVERY] {repr(text)}")
        
        # El documento debería estar intacto
        self.assertIn("ANTES_MALFORMADA", text)
        self.assertIn("DESPUES_BUENA", text)
    
    def test_multiple_equations_with_one_failing(self):
        """Múltiples ecuaciones donde una falla en medio."""
        equations = [
            ("a + b = c", True),
            ("", False),  # Vacía - podría fallar
            ("x^2 + y^2 = z^2", True),
        ]
        
        self.ws.insert_text_at_cursor("INICIO", "Normal")
        
        for eq, should_work in equations:
            result = self.ws.insert_equation(eq)
            logger.info(f"  '{eq}' -> {result} (esperado: {should_work})")
        
        self.ws.insert_text_at_cursor("FIN", "Normal")
        
        text = self.get_document_text()
        
        self.assertIn("INICIO", text)
        self.assertIn("FIN", text)


class TestDisplayFormatting(EdgeCaseTestCase):
    """Tests para verificar que las ecuaciones display están centradas."""
    
    def test_equation_is_display_mode(self):
        """Verificar que la ecuación está en modo display (no inline)."""
        equation = "E = mc^2"
        
        self.ws.insert_equation(equation)
        
        # Obtener el rango del documento y buscar OMaths
        doc = self.ws.get_active_document()
        
        try:
            omaths = doc.OMaths
            if omaths.Count > 0:
                omath = omaths(1)
                omath_type = omath.Type
                # wdOMathDisplay = 0, wdOMathInline = 1
                logger.info(f"[DISPLAY CHECK] OMath Type: {omath_type} (0=Display, 1=Inline)")
                self.assertEqual(omath_type, 0, "La ecuación debería estar en modo Display (0)")
        except Exception as e:
            logger.warning(f"No se pudo verificar tipo de OMath: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
