"""
Test Suite: Ecuaciones Display (Centradas) - Stress Testing

Este módulo prueba la inserción de ecuaciones en modo "display" (centradas)
usando el método insert_equation() de WordService.

Incluye:
- Ecuaciones básicas (fracciones, raíces, exponentes)
- Matrices y sistemas de ecuaciones
- Operadores de cálculo (integrales, sumatorias, límites)
- Símbolos griegos y operadores lógicos
- Ecuaciones de ingeniería estructural (específico para SAP2000)
- Casos de stress con anidamiento profundo

Ejecutar con:
    python -m unittest Reportes.tests.test_display_equations -v
"""
import unittest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Reportes.word_service import WordService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DisplayEquationTestCase(unittest.TestCase):
    """Clase base para tests de ecuaciones display."""
    
    @classmethod
    def setUpClass(cls):
        cls.ws = WordService()
        cls.ws.connect()
    
    def setUp(self):
        self.doc = self.ws.create_new_document()
        time.sleep(0.3)
    
    def get_document_text(self):
        return self.doc.Content.Text
    
    def get_paragraph_count(self):
        return self.doc.Paragraphs.Count
    
    def insert_with_context(self, equation, description=""):
        """Inserta ecuación con texto antes y después para verificar integridad."""
        marker_before = f"ANTES_{description}"
        marker_after = f"DESPUES_{description}"
        
        self.ws.insert_text_at_cursor(marker_before, "Normal")
        result = self.ws.insert_equation(equation)
        self.ws.insert_text_at_cursor(marker_after, "Normal")
        
        return result, marker_before, marker_after


class TestDisplayBasicEquations(DisplayEquationTestCase):
    """Tests para ecuaciones básicas en modo display."""
    
    def test_simple_fraction(self):
        """Fracción simple centrada."""
        result, before, after = self.insert_with_context("a/b", "FRACTION")
        
        text = self.get_document_text()
        logger.info(f"[FRACCIÓN] {repr(text)}")
        
        self.assertTrue(result, "insert_equation retornó False")
        self.assertIn(before, text, "Texto antes consumido")
        self.assertIn(after, text, "Texto después consumido")
    
    def test_nested_fraction(self):
        """Fracción anidada: a/(b + c/d)."""
        equation = "(a)/(b + (c)/(d))"
        result, before, after = self.insert_with_context(equation, "NESTED_FRAC")
        
        text = self.get_document_text()
        logger.info(f"[FRACCIÓN ANIDADA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text, "Texto después de fracción anidada consumido")
    
    def test_square_root(self):
        """Raíz cuadrada."""
        equation = "√(x^2 + y^2)"
        result, before, after = self.insert_with_context(equation, "SQRT")
        
        text = self.get_document_text()
        logger.info(f"[RAÍZ] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_nth_root(self):
        """Raíz n-ésima: √(3&x) = raíz cúbica de x."""
        equation = "√(3&x^3 + y^3)"
        result, before, after = self.insert_with_context(equation, "NROOT")
        
        text = self.get_document_text()
        logger.info(f"[RAÍZ N-ÉSIMA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_quadratic_formula(self):
        """Fórmula cuadrática completa."""
        equation = "x = (-b ± √(b^2 - 4ac))/(2a)"
        result, before, after = self.insert_with_context(equation, "QUADRATIC")
        
        text = self.get_document_text()
        logger.info(f"[FÓRMULA CUADRÁTICA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_exponents_and_subscripts(self):
        """Exponentes y subíndices complejos."""
        equation = "x_1^2 + x_2^2 = r^2"
        result, before, after = self.insert_with_context(equation, "EXPSUB")
        
        text = self.get_document_text()
        logger.info(f"[EXP/SUB] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplayCalculusOperators(DisplayEquationTestCase):
    """Tests para operadores de cálculo."""
    
    def test_definite_integral(self):
        """Integral definida."""
        equation = "∫_(a)^(b) f(x)dx"
        result, before, after = self.insert_with_context(equation, "INTEGRAL")
        
        text = self.get_document_text()
        logger.info(f"[INTEGRAL] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_double_integral(self):
        """Integral doble."""
        equation = "∬_D f(x,y) dA"
        result, before, after = self.insert_with_context(equation, "DBLINT")
        
        text = self.get_document_text()
        logger.info(f"[INTEGRAL DOBLE] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_summation(self):
        """Sumatoria con límites."""
        equation = "∑_(i=1)^(n) i^2 = (n(n+1)(2n+1))/(6)"
        result, before, after = self.insert_with_context(equation, "SUMMATION")
        
        text = self.get_document_text()
        logger.info(f"[SUMATORIA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_product(self):
        """Productoria."""
        equation = "∏_(k=1)^(n) a_k"
        result, before, after = self.insert_with_context(equation, "PRODUCT")
        
        text = self.get_document_text()
        logger.info(f"[PRODUCTORIA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_limit(self):
        """Límite."""
        equation = "lim_(x→∞) (1 + 1/x)^x = e"
        result, before, after = self.insert_with_context(equation, "LIMIT")
        
        text = self.get_document_text()
        logger.info(f"[LÍMITE] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_partial_derivative(self):
        """Derivadas parciales."""
        equation = "(∂^2 f)/(∂x^2) + (∂^2 f)/(∂y^2) = 0"
        result, before, after = self.insert_with_context(equation, "PARTIAL")
        
        text = self.get_document_text()
        logger.info(f"[DERIVADA PARCIAL] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplayMatricesAndSystems(DisplayEquationTestCase):
    """Tests para matrices y sistemas de ecuaciones."""
    
    def test_2x2_matrix(self):
        """Matriz 2x2."""
        equation = "A = [\\matrix(a&b@c&d)]"
        result, before, after = self.insert_with_context(equation, "MATRIX2X2")
        
        text = self.get_document_text()
        logger.info(f"[MATRIZ 2x2] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_3x3_identity_matrix(self):
        """Matriz identidad 3x3."""
        equation = "I = [\\matrix(1&0&0@0&1&0@0&0&1)]"
        result, before, after = self.insert_with_context(equation, "IDENTITY")
        
        text = self.get_document_text()
        logger.info(f"[MATRIZ IDENTIDAD] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_column_vector(self):
        """Vector columna."""
        equation = "v⃗ = (\\matrix(v_x@v_y@v_z))"
        result, before, after = self.insert_with_context(equation, "VECTOR")
        
        text = self.get_document_text()
        logger.info(f"[VECTOR] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_equation_system_eqarray(self):
        """Sistema de ecuaciones con eqarray."""
        equation = "█(x + 2y = 5 @ 3x - y = -2)"
        result, before, after = self.insert_with_context(equation, "EQARRAY")
        
        text = self.get_document_text()
        logger.info(f"[SISTEMA ECUACIONES] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_piecewise_function(self):
        """Función por partes (cases)."""
        equation = "f(x) = ❴█(x^2 & if x ≥ 0 @ -x^2 & if x < 0)"
        result, before, after = self.insert_with_context(equation, "PIECEWISE")
        
        text = self.get_document_text()
        logger.info(f"[FUNCIÓN POR PARTES] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_determinant(self):
        """Determinante de matriz."""
        equation = "det(A) = |\\matrix(a&b@c&d)| = ad - bc"
        result, before, after = self.insert_with_context(equation, "DETERMINANT")
        
        text = self.get_document_text()
        logger.info(f"[DETERMINANTE] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplayGreekAndSymbols(DisplayEquationTestCase):
    """Tests para símbolos griegos y operadores especiales."""
    
    def test_greek_lowercase(self):
        """Letras griegas minúsculas."""
        equation = "α + β + γ + δ + ε + θ + λ + μ + π + σ + φ + ω"
        result, before, after = self.insert_with_context(equation, "GREEK_LOWER")
        
        text = self.get_document_text()
        logger.info(f"[GRIEGO MINÚSCULA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_greek_uppercase(self):
        """Letras griegas mayúsculas."""
        equation = "Γ + Δ + Θ + Λ + Ξ + Π + Σ + Φ + Ψ + Ω"
        result, before, after = self.insert_with_context(equation, "GREEK_UPPER")
        
        text = self.get_document_text()
        logger.info(f"[GRIEGO MAYÚSCULA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_set_theory_operators(self):
        """Operadores de teoría de conjuntos."""
        equation = "A ∩ B ⊆ A ∪ B"
        result, before, after = self.insert_with_context(equation, "SET_OPS")
        
        text = self.get_document_text()
        logger.info(f"[CONJUNTOS] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_logic_quantifiers(self):
        """Cuantificadores lógicos."""
        equation = "∀ x ∈ ℝ, ∃ y : y > x"
        result, before, after = self.insert_with_context(equation, "QUANTIFIERS")
        
        text = self.get_document_text()
        logger.info(f"[CUANTIFICADORES] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_arrows_and_implications(self):
        """Flechas e implicaciones."""
        equation = "A ⇒ B ⇔ ¬A ∨ B"
        result, before, after = self.insert_with_context(equation, "ARROWS")
        
        text = self.get_document_text()
        logger.info(f"[FLECHAS] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_comparison_operators(self):
        """Operadores de comparación."""
        equation = "a ≤ b < c ≠ d ≈ e"
        result, before, after = self.insert_with_context(equation, "COMPARISON")
        
        text = self.get_document_text()
        logger.info(f"[COMPARACIÓN] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplayEngineeringFormulas(DisplayEquationTestCase):
    """Tests para fórmulas de ingeniería estructural (relevantes para SAP2000)."""
    
    def test_stress_formula(self):
        """Fórmula de esfuerzo."""
        equation = "σ = F/A"
        result, before, after = self.insert_with_context(equation, "STRESS")
        
        text = self.get_document_text()
        logger.info(f"[ESFUERZO] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_bending_stress(self):
        """Esfuerzo de flexión."""
        equation = "σ_b = (M⋅c)/(I)"
        result, before, after = self.insert_with_context(equation, "BENDING")
        
        text = self.get_document_text()
        logger.info(f"[FLEXIÓN] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_euler_buckling(self):
        """Carga crítica de Euler."""
        equation = "P_cr = (π^2 EI)/(L_e^2)"
        result, before, after = self.insert_with_context(equation, "EULER")
        
        text = self.get_document_text()
        logger.info(f"[EULER] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_moment_of_inertia(self):
        """Momento de inercia."""
        equation = "I_x = ∫_A y^2 dA"
        result, before, after = self.insert_with_context(equation, "INERTIA")
        
        text = self.get_document_text()
        logger.info(f"[INERCIA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_deflection_formula(self):
        """Deflexión de viga."""
        equation = "δ_max = (5wL^4)/(384EI)"
        result, before, after = self.insert_with_context(equation, "DEFLECTION")
        
        text = self.get_document_text()
        logger.info(f"[DEFLEXIÓN] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_combined_stress(self):
        """Esfuerzo combinado."""
        equation = "σ_eq = √(σ_x^2 + 3τ_xy^2)"
        result, before, after = self.insert_with_context(equation, "COMBINED")
        
        text = self.get_document_text()
        logger.info(f"[ESFUERZO COMBINADO] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_seismic_base_shear(self):
        """Cortante basal sísmico."""
        equation = "V = C_s ⋅ W"
        result, before, after = self.insert_with_context(equation, "BASESHEAR")
        
        text = self.get_document_text()
        logger.info(f"[CORTANTE BASAL] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_seismic_response_coefficient(self):
        """Coeficiente de respuesta sísmica NCh433."""
        equation = "C = (2.75 S⋅A_0)/(R) ⋅ ((T′)/(T))^n"
        result, before, after = self.insert_with_context(equation, "SEISMIC_C")
        
        text = self.get_document_text()
        logger.info(f"[COEFICIENTE C] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplayStressTest(DisplayEquationTestCase):
    """Tests de stress con ecuaciones complejas y anidamiento profundo."""
    
    def test_taylor_series(self):
        """Serie de Taylor."""
        equation = "e^x = ∑_(n=0)^(∞) (x^n)/(n!) = 1 + x + (x^2)/(2!) + (x^3)/(3!) + ⋯"
        result, before, after = self.insert_with_context(equation, "TAYLOR")
        
        text = self.get_document_text()
        logger.info(f"[TAYLOR] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_maxwell_equations(self):
        """Ecuaciones de Maxwell."""
        equation = "∇⋅E⃗ = ρ/ε_0, ∇×E⃗ = -(∂B⃗)/(∂t)"
        result, before, after = self.insert_with_context(equation, "MAXWELL")
        
        text = self.get_document_text()
        logger.info(f"[MAXWELL] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_einstein_field_equation(self):
        """Ecuación de campo de Einstein."""
        equation = "R_μν - (1)/(2)Rg_μν + Λg_μν = (8πG)/(c^4)T_μν"
        result, before, after = self.insert_with_context(equation, "EINSTEIN")
        
        text = self.get_document_text()
        logger.info(f"[EINSTEIN] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_schrodinger_equation(self):
        """Ecuación de Schrödinger."""
        equation = "iℏ(∂Ψ)/(∂t) = -(ℏ^2)/(2m)∇^2Ψ + VΨ"
        result, before, after = self.insert_with_context(equation, "SCHRODINGER")
        
        text = self.get_document_text()
        logger.info(f"[SCHRÖDINGER] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_deeply_nested_fractions(self):
        """Fracciones profundamente anidadas (3 niveles)."""
        equation = "(a)/((b)/((c)/(d)))"
        result, before, after = self.insert_with_context(equation, "NESTED3")
        
        text = self.get_document_text()
        logger.info(f"[ANIDADO 3 NIVELES] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_complex_integral(self):
        """Integral compleja con fracciones y raíces."""
        equation = "∫_0^(∞) (e^(-x^2))/(√(2π)) dx = (1)/(2)"
        result, before, after = self.insert_with_context(equation, "COMPLEX_INT")
        
        text = self.get_document_text()
        logger.info(f"[INTEGRAL COMPLEJA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_matrix_inverse(self):
        """Inversa de matriz 2x2."""
        equation = "A^(-1) = (1)/(ad-bc)[\\matrix(d&-b@-c&a)]"
        result, before, after = self.insert_with_context(equation, "MATRIX_INV")
        
        text = self.get_document_text()
        logger.info(f"[MATRIZ INVERSA] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_multiple_integrals_with_limits(self):
        """Integrales múltiples con límites complejos."""
        equation = "∫_0^(2π) ∫_0^(R) r⋅f(r,θ) dr dθ"
        result, before, after = self.insert_with_context(equation, "MULTI_INT")
        
        text = self.get_document_text()
        logger.info(f"[INTEGRALES MÚLTIPLES] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


class TestDisplaySequentialInsertion(DisplayEquationTestCase):
    """Tests para inserción secuencial de múltiples ecuaciones display."""
    
    def test_three_equations_in_sequence(self):
        """Tres ecuaciones display seguidas."""
        equations = [
            "a^2 + b^2 = c^2",
            "E = mc^2",
            "F = ma"
        ]
        
        self.ws.insert_text_at_cursor("INICIO", "Normal")
        
        for eq in equations:
            self.ws.insert_equation(eq)
        
        self.ws.insert_text_at_cursor("FIN", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[3 ECUACIONES] {repr(text)}")
        
        self.assertIn("INICIO", text)
        self.assertIn("FIN", text, "Texto final consumido después de múltiples ecuaciones")
    
    def test_alternating_text_and_equations(self):
        """Alternancia de texto y ecuaciones."""
        self.ws.insert_text_at_cursor("Teorema de Pitágoras:", "Normal")
        self.ws.insert_equation("a^2 + b^2 = c^2")
        self.ws.insert_text_at_cursor("Energía relativista:", "Normal")
        self.ws.insert_equation("E = mc^2")
        self.ws.insert_text_at_cursor("Segunda ley de Newton:", "Normal")
        self.ws.insert_equation("F = ma")
        self.ws.insert_text_at_cursor("FIN DEL DOCUMENTO", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[ALTERNADO] {repr(text)}")
        
        self.assertIn("Pitágoras", text)
        self.assertIn("relativista", text)
        self.assertIn("Newton", text)
        self.assertIn("FIN DEL DOCUMENTO", text)
    
    def test_mixed_inline_and_display(self):
        """Mezcla de ecuaciones inline y display."""
        self.ws.insert_text_at_cursor("Sabemos que $E = mc^2$ es famosa.", "Normal")
        self.ws.insert_text_at_cursor("La versión expandida es:", "Normal")
        self.ws.insert_equation("E^2 = (pc)^2 + (m_0 c^2)^2")
        self.ws.insert_text_at_cursor("Donde $m_0$ es la masa en reposo.", "Normal")
        
        text = self.get_document_text()
        logger.info(f"[MIXTO INLINE/DISPLAY] {repr(text)}")
        
        self.assertIn("Sabemos", text)
        self.assertIn("expandida", text)
        self.assertIn("masa en reposo", text)


class TestDisplayBackslashSymbols(DisplayEquationTestCase):
    """Tests para símbolos usando notación \\command."""
    
    def test_greek_with_backslash(self):
        """Símbolos griegos con \\alpha, \\beta, etc."""
        equation = "\\alpha + \\beta = \\gamma"
        result, before, after = self.insert_with_context(equation, "BACKSLASH_GREEK")
        
        text = self.get_document_text()
        logger.info(f"[BACKSLASH GREEK] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_operators_with_backslash(self):
        """Operadores con \\sum, \\int, etc."""
        equation = "\\sum_(i=1)^(n) x_i = \\int_a^b f(x)dx"
        result, before, after = self.insert_with_context(equation, "BACKSLASH_OPS")
        
        text = self.get_document_text()
        logger.info(f"[BACKSLASH OPS] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)
    
    def test_mixed_unicode_and_backslash(self):
        """Mezcla de Unicode directo y \\commands."""
        equation = "σ = \\sigma = \\alpha⋅E⋅ε"
        result, before, after = self.insert_with_context(equation, "MIXED_NOTATION")
        
        text = self.get_document_text()
        logger.info(f"[MIXTO] {repr(text)}")
        
        self.assertTrue(result)
        self.assertIn(after, text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
