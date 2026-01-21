"""
Tests para ecuaciones display insertadas entre títulos (Headings).

Este módulo investiga el problema donde BuildUp() consumía el título
posterior al insertar una ecuación en modo display. La solución parche
implementa una estrategia de "3 párrafos buffer".

Todos los tests se ejecutan en el MISMO documento Word para eficiencia.

Escenarios a probar:
1. Heading → Ecuación Display → Heading
2. Heading → Texto → Ecuación Display → Texto → Heading
3. Múltiples ecuaciones entre headings
4. Diferentes niveles de heading (H1, H2, H3)
5. Snippet completo con headings y ecuaciones
"""

import unittest
import time
from comtypes.client import CreateObject


def get_word_app():
    """Obtiene o crea instancia de Word."""
    try:
        word = CreateObject("Word.Application")
        word.Visible = True
        return word
    except Exception as e:
        print(f"Error creando Word: {e}")
        return None


class TestDisplayEquationBetweenHeadings(unittest.TestCase):
    """
    Tests para ecuaciones display entre títulos.
    Todos los tests usan el MISMO documento Word.
    """
    
    word_app = None
    doc = None
    test_results = []
    
    @classmethod
    def setUpClass(cls):
        """Crear UNA instancia de Word y UN documento para todos los tests."""
        cls.word_app = get_word_app()
        if cls.word_app:
            cls.doc = cls.word_app.Documents.Add()
            # Insertar título del documento de pruebas
            selection = cls.word_app.Selection
            selection.TypeText("=== TESTS: Ecuaciones Display entre Headings ===")
            selection.TypeParagraph()
            selection.TypeParagraph()
            cls.test_results = []
    
    @classmethod
    def tearDownClass(cls):
        """Mostrar resumen al final pero NO cerrar Word para inspección."""
        if cls.word_app and cls.doc:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 50)
            selection.TypeParagraph()
            selection.TypeText(f"Tests completados: {len(cls.test_results)}")
            selection.TypeParagraph()
            for result in cls.test_results:
                selection.TypeText(f"  {result}")
                selection.TypeParagraph()
            # NO cerrar - dejar abierto para inspección visual
            print("\n" + "=" * 50)
            print("DOCUMENTO WORD ABIERTO PARA INSPECCIÓN")
            print("Ciérrelo manualmente cuando termine de revisar.")
            print("=" * 50)
    
    def _insert_heading(self, text, level=1):
        """Inserta un heading con el nivel especificado."""
        selection = self.word_app.Selection
        selection.TypeText(text)
        # Aplicar estilo Heading
        selection.Range.Style = -1 - level  # wdStyleHeading1=-2, etc.
        selection.TypeParagraph()
        # Reset a Normal
        selection.Style = -1  # wdStyleNormal
    
    def _insert_display_equation_with_buffer(self, equation_text):
        """
        Inserta ecuación display usando la estrategia de 3 párrafos buffer.
        Esta es la implementación actual en word_service.py.
        """
        selection = self.word_app.Selection
        selection.Collapse(0)  # wdCollapseEnd
        
        # Guardar posición inicial
        pos_inicial = selection.Range.Start
        
        # Insertar 3 párrafos de buffer
        for _ in range(3):
            selection.TypeParagraph()
        
        # Retroceder 3 párrafos
        selection.MoveUp(4, 3, 0)  # wdParagraph=4, Count=3, wdMove=0
        
        # Guardar posición para la ecuación
        start_pos = selection.Range.Start
        
        # Insertar texto de ecuación
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        # Crear rango y convertir a OMath
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        # BuildUp
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0  # wdOMathDisplay
        except Exception as e:
            pass
        
        # Mover al final de la ecuación
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        selection.Style = -1  # wdStyleNormal
        
        return True
    
    def _insert_display_equation_NO_buffer(self, equation_text):
        """
        Inserta ecuación display SIN la estrategia de buffer.
        Para demostrar el problema original.
        """
        selection = self.word_app.Selection
        selection.Collapse(0)
        
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0
        except:
            pass
        
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        
        return True
    
    def _add_section_separator(self, test_name):
        """Agrega separador visual entre tests."""
        selection = self.word_app.Selection
        selection.TypeParagraph()
        selection.TypeText(f"--- {test_name} ---")
        selection.TypeParagraph()
    
    def _count_headings_in_range(self, start, end):
        """Cuenta cuántos headings existen en un rango."""
        doc_range = self.doc.Range(start, end)
        heading_count = 0
        for para in doc_range.Paragraphs:
            style_name = str(para.Style.NameLocal).lower()
            if "heading" in style_name or "título" in style_name:
                heading_count += 1
        return heading_count
    
    def _get_paragraph_styles_in_range(self, start, end):
        """Obtiene lista de estilos de párrafo en un rango."""
        doc_range = self.doc.Range(start, end)
        styles = []
        for para in doc_range.Paragraphs:
            styles.append(str(para.Style.NameLocal))
        return styles

    # =========================================================================
    # TEST 1: Heading → Ecuación → Heading (CON buffer - solución actual)
    # =========================================================================
    def test_01_heading_equation_heading_with_buffer(self):
        """
        Escenario básico: H1 → Ecuación Display → H1
        Usando la estrategia de buffer de 3 párrafos.
        """
        self._add_section_separator("TEST 01: H1 → Eq → H1 (CON buffer)")
        
        # Marcar inicio
        start_pos = self.word_app.Selection.Range.Start
        
        # Insertar estructura
        self._insert_heading("Título Antes de Ecuación", level=1)
        self._insert_display_equation_with_buffer("E = mc²")
        self._insert_heading("Título Después de Ecuación", level=1)
        
        # Marcar fin
        end_pos = self.word_app.Selection.Range.Start
        
        # Verificar que ambos headings existen
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 01: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings encontrados: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2, 
            f"Deberían existir 2 headings, pero hay {heading_count}. "
            "BuildUp probablemente consumió el heading posterior.")

    # =========================================================================
    # TEST 2: Heading → Ecuación → Heading (SIN buffer - demostrar problema)
    # =========================================================================
    def test_02_heading_equation_heading_NO_buffer(self):
        """
        Demostración del PROBLEMA: Sin buffer, BuildUp consume el heading posterior.
        """
        self._add_section_separator("TEST 02: H1 → Eq → H1 (SIN buffer - PROBLEMA)")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self._insert_heading("Título Antes (sin buffer)", level=1)
        self._insert_display_equation_NO_buffer("a² + b² = c²")
        self._insert_heading("Título Después (sin buffer)", level=1)
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        styles = self._get_paragraph_styles_in_range(start_pos, end_pos)
        
        # Este test PUEDE fallar - es para demostrar el problema
        result = f"TEST 02: Headings={heading_count}, Styles={styles[:5]}..."
        self.test_results.append(result)
        
        # No hacemos assert aquí porque queremos ver el comportamiento

    # =========================================================================
    # TEST 3: H2 → Texto → Ecuación → Texto → H2
    # =========================================================================
    def test_03_heading_text_equation_text_heading(self):
        """
        Escenario con texto intermedio: H2 → párrafo → Eq → párrafo → H2
        """
        self._add_section_separator("TEST 03: H2 → texto → Eq → texto → H2")
        
        selection = self.word_app.Selection
        start_pos = selection.Range.Start
        
        self._insert_heading("Sección de Física", level=2)
        
        selection.TypeText("La ecuación de Einstein relaciona masa y energía:")
        selection.TypeParagraph()
        
        self._insert_display_equation_with_buffer("E = mc²")
        
        selection.TypeText("Esta ecuación revolucionó la física moderna.")
        selection.TypeParagraph()
        
        self._insert_heading("Siguiente Sección", level=2)
        
        end_pos = selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 03: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 4: Múltiples ecuaciones entre headings
    # =========================================================================
    def test_04_multiple_equations_between_headings(self):
        """
        Escenario: H1 → Eq1 → Eq2 → Eq3 → H1
        """
        self._add_section_separator("TEST 04: H1 → 3 Ecuaciones → H1")
        
        selection = self.word_app.Selection
        start_pos = selection.Range.Start
        
        self._insert_heading("Ecuaciones de Maxwell", level=1)
        
        equations = [
            "∇⋅E = ρ/ε₀",
            "∇⋅B = 0",
            "∇×E = -∂B/∂t"
        ]
        
        for eq in equations:
            self._insert_display_equation_with_buffer(eq)
        
        self._insert_heading("Aplicaciones", level=1)
        
        end_pos = selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 04: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 5: Jerarquía de headings H1 → H2 → Eq → H2 → H1
    # =========================================================================
    def test_05_heading_hierarchy_with_equation(self):
        """
        Escenario con jerarquía: H1 → H2 → Eq → H2 → H1
        """
        self._add_section_separator("TEST 05: Jerarquía H1→H2→Eq→H2→H1")
        
        selection = self.word_app.Selection
        start_pos = selection.Range.Start
        
        self._insert_heading("Capítulo 1: Física Cuántica", level=1)
        self._insert_heading("1.1 Ecuación de Schrödinger", level=2)
        
        selection.TypeText("La ecuación fundamental es:")
        selection.TypeParagraph()
        
        self._insert_display_equation_with_buffer("iℏ ∂Ψ/∂t = ĤΨ")
        
        self._insert_heading("1.2 Interpretación", level=2)
        
        selection.TypeText("Esta ecuación describe la evolución temporal.")
        selection.TypeParagraph()
        
        self._insert_heading("Capítulo 2: Relatividad", level=1)
        
        end_pos = selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 05: {'PASS' if heading_count >= 4 else 'FAIL'} - Headings: {heading_count} (esperados 4)"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 4, 
            f"Deberían existir 4 headings (2 H1 + 2 H2), hay {heading_count}")

    # =========================================================================
    # TEST 6: Ecuación compleja (fracción) entre headings
    # =========================================================================
    def test_06_complex_fraction_equation_between_headings(self):
        """
        Escenario con ecuación compleja (fracción grande).
        """
        self._add_section_separator("TEST 06: Ecuación Compleja (fracción)")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self._insert_heading("Teorema de Bayes", level=1)
        
        # Ecuación compleja con fracción
        self._insert_display_equation_with_buffer("P(A|B) = (P(B|A)⋅P(A))/P(B)")
        
        self._insert_heading("Aplicación en ML", level=1)
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 06: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 7: Ecuación con integral entre headings
    # =========================================================================
    def test_07_integral_equation_between_headings(self):
        """
        Escenario con integral definida.
        """
        self._add_section_separator("TEST 07: Integral entre headings")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self._insert_heading("Cálculo Integral", level=2)
        
        self._insert_display_equation_with_buffer("∫_0^∞ e^(-x²) dx = √π/2")
        
        self._insert_heading("Propiedades", level=2)
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 07: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 8: Matriz entre headings
    # =========================================================================
    def test_08_matrix_equation_between_headings(self):
        """
        Escenario con matriz (estructura vertical compleja).
        """
        self._add_section_separator("TEST 08: Matriz entre headings")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self._insert_heading("Álgebra Lineal", level=1)
        
        # Matriz 2x2
        self._insert_display_equation_with_buffer("[■(a&b@c&d)]")
        
        self._insert_heading("Determinantes", level=1)
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 08: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 9: H3 inmediatamente después de ecuación
    # =========================================================================
    def test_09_h3_immediately_after_equation(self):
        """
        Escenario crítico: H3 inmediatamente después de ecuación (sin texto intermedio).
        """
        self._add_section_separator("TEST 09: H3 inmediato post-ecuación")
        
        selection = self.word_app.Selection
        start_pos = selection.Range.Start
        
        self._insert_heading("Subsección A", level=3)
        self._insert_display_equation_with_buffer("F = ma")
        self._insert_heading("Subsección B", level=3)  # Inmediatamente después
        
        end_pos = selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 09: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)

    # =========================================================================
    # TEST 10: Verificar contenido del heading posterior
    # =========================================================================
    def test_10_verify_heading_content_preserved(self):
        """
        Verificar que el CONTENIDO del heading posterior no se pierde.
        """
        self._add_section_separator("TEST 10: Verificar contenido heading")
        
        selection = self.word_app.Selection
        start_pos = selection.Range.Start
        
        titulo_antes = "TÍTULO_ANTES_ÚNICO_123"
        titulo_despues = "TÍTULO_DESPUÉS_ÚNICO_456"
        
        self._insert_heading(titulo_antes, level=1)
        self._insert_display_equation_with_buffer("x² + y² = r²")
        self._insert_heading(titulo_despues, level=1)
        
        end_pos = selection.Range.Start
        
        # Buscar el texto del título posterior en el rango
        doc_range = self.doc.Range(start_pos, end_pos)
        text_content = doc_range.Text
        
        titulo_encontrado = titulo_despues in text_content
        
        result = f"TEST 10: {'PASS' if titulo_encontrado else 'FAIL'} - Título posterior {'encontrado' if titulo_encontrado else 'PERDIDO'}"
        self.test_results.append(result)
        
        self.assertTrue(titulo_encontrado, 
            f"El título '{titulo_despues}' fue consumido por BuildUp. "
            f"Contenido encontrado: {text_content[:200]}...")

    # =========================================================================
    # TEST 11: Secuencia alternada Heading-Ecuación
    # =========================================================================
    def test_11_alternating_heading_equation_sequence(self):
        """
        Secuencia: H → Eq → H → Eq → H → Eq → H
        """
        self._add_section_separator("TEST 11: Secuencia alternada H-Eq-H-Eq")
        
        start_pos = self.word_app.Selection.Range.Start
        
        for i in range(4):
            self._insert_heading(f"Sección {i+1}", level=2)
            if i < 3:  # No insertar ecuación después del último heading
                self._insert_display_equation_with_buffer(f"x_{i+1} = {i+1}")
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 11: {'PASS' if heading_count >= 4 else 'FAIL'} - Headings: {heading_count} (esperados 4)"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 4)

    # =========================================================================
    # TEST 12: Ecuación larga entre headings
    # =========================================================================
    def test_12_long_equation_between_headings(self):
        """
        Ecuación muy larga que podría causar más consumo de párrafos.
        """
        self._add_section_separator("TEST 12: Ecuación larga")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self._insert_heading("Fórmula Extendida", level=1)
        
        # Ecuación muy larga
        long_eq = "f(x) = a₀ + a₁x + a₂x² + a₃x³ + a₄x⁴ + a₅x⁵ + ⋯ + aₙxⁿ"
        self._insert_display_equation_with_buffer(long_eq)
        
        self._insert_heading("Convergencia", level=1)
        
        end_pos = self.word_app.Selection.Range.Start
        
        heading_count = self._count_headings_in_range(start_pos, end_pos)
        
        result = f"TEST 12: {'PASS' if heading_count >= 2 else 'FAIL'} - Headings: {heading_count}"
        self.test_results.append(result)
        
        self.assertGreaterEqual(heading_count, 2)


class TestComparisonBufferVsNoBuffer(unittest.TestCase):
    """
    Comparación directa entre inserción CON y SIN buffer.
    Usa el MISMO documento que la clase anterior.
    """
    
    @classmethod
    def setUpClass(cls):
        # Reusar el documento de la clase anterior, o crear uno nuevo si no existe
        if TestDisplayEquationBetweenHeadings.word_app is None:
            cls.word_app = get_word_app()
            if cls.word_app:
                cls.doc = cls.word_app.Documents.Add()
        else:
            cls.word_app = TestDisplayEquationBetweenHeadings.word_app
            cls.doc = TestDisplayEquationBetweenHeadings.doc
        
        if cls.word_app:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 50)
            selection.TypeParagraph()
            selection.TypeText("=== COMPARACIÓN: CON Buffer vs SIN Buffer ===")
            selection.TypeParagraph()
    
    def _insert_heading(self, text, level=1):
        selection = self.word_app.Selection
        selection.TypeText(text)
        selection.Range.Style = -1 - level
        selection.TypeParagraph()
        selection.Style = -1

    def _count_headings_in_range(self, start, end):
        doc_range = self.doc.Range(start, end)
        count = 0
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                count += 1
        return count

    def test_side_by_side_comparison(self):
        """
        Comparación lado a lado del comportamiento.
        """
        selection = self.word_app.Selection
        
        # --- CON BUFFER ---
        selection.TypeText(">>> PRUEBA CON BUFFER:")
        selection.TypeParagraph()
        
        start_con = selection.Range.Start
        
        self._insert_heading("H1: Antes (con buffer)", level=1)
        
        # Con buffer
        selection.Collapse(0)
        for _ in range(3):
            selection.TypeParagraph()
        selection.MoveUp(4, 3, 0)
        start_pos = selection.Range.Start
        selection.TypeText("E = mc²")
        end_pos = selection.Range.Start
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0
        except:
            pass
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        selection.Style = -1
        
        self._insert_heading("H1: Después (con buffer)", level=1)
        
        end_con = selection.Range.Start
        headings_con = self._count_headings_in_range(start_con, end_con)
        
        # --- SIN BUFFER ---
        selection.TypeParagraph()
        selection.TypeText(">>> PRUEBA SIN BUFFER:")
        selection.TypeParagraph()
        
        start_sin = selection.Range.Start
        
        self._insert_heading("H1: Antes (sin buffer)", level=1)
        
        # Sin buffer
        selection.Collapse(0)
        start_pos = selection.Range.Start
        selection.TypeText("a² + b² = c²")
        end_pos = selection.Range.Start
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0
        except:
            pass
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        
        self._insert_heading("H1: Después (sin buffer)", level=1)
        
        end_sin = selection.Range.Start
        headings_sin = self._count_headings_in_range(start_sin, end_sin)
        
        # Resumen
        selection.TypeParagraph()
        selection.TypeText(f"RESULTADO: Con buffer={headings_con} headings, Sin buffer={headings_sin} headings")
        selection.TypeParagraph()
        
        TestDisplayEquationBetweenHeadings.test_results.append(
            f"COMPARACIÓN: Con buffer={headings_con}, Sin buffer={headings_sin}"
        )
        
        # El test pasa si con buffer preserva más o igual headings
        self.assertGreaterEqual(headings_con, headings_sin,
            "La estrategia de buffer debería preservar igual o más headings")


class TestWordServiceIntegration(unittest.TestCase):
    """
    Tests usando WordService real para verificar la implementación completa.
    Usa el MISMO documento.
    """
    
    word_service = None
    
    @classmethod
    def setUpClass(cls):
        # Reusar Word de las clases anteriores, o crear uno nuevo si no existe
        if TestDisplayEquationBetweenHeadings.word_app is None:
            cls.word_app = get_word_app()
            if cls.word_app:
                cls.doc = cls.word_app.Documents.Add()
        else:
            cls.word_app = TestDisplayEquationBetweenHeadings.word_app
            cls.doc = TestDisplayEquationBetweenHeadings.doc
        
        if cls.word_app:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 50)
            selection.TypeParagraph()
            selection.TypeText("=== TESTS: WordService Integration ===")
            selection.TypeParagraph()
        
        # Importar WordService
        try:
            import sys
            import os
            # Agregar path del proyecto
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from Reportes.word_service import WordService
            cls.word_service = WordService()
            # Inyectar la instancia de Word existente
            cls.word_service.word_app = cls.word_app
        except Exception as e:
            print(f"No se pudo cargar WordService: {e}")
            cls.word_service = None
    
    def test_wordservice_heading_equation_heading(self):
        """
        Test usando WordService.insert_heading() y WordService.insert_equation()
        """
        if not self.word_service:
            self.skipTest("WordService no disponible")
        
        selection = self.word_app.Selection
        selection.TypeText(">>> WordService: H1 → Eq → H1")
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Usar métodos de WordService
        self.word_service.insert_heading("Heading vía WordService", level=1)
        self.word_service.insert_equation("∑_{i=1}^n i = n(n+1)/2")
        self.word_service.insert_heading("Siguiente Heading vía WordService", level=1)
        
        end_pos = selection.Range.Start
        
        # Contar headings
        doc_range = self.doc.Range(start_pos, end_pos)
        heading_count = 0
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                heading_count += 1
        
        TestDisplayEquationBetweenHeadings.test_results.append(
            f"WordService Integration: Headings={heading_count}"
        )
        
        self.assertGreaterEqual(heading_count, 2,
            f"WordService debería preservar ambos headings, encontrados: {heading_count}")


if __name__ == "__main__":
    # Ejecutar tests en orden
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests en orden
    suite.addTests(loader.loadTestsFromTestCase(TestDisplayEquationBetweenHeadings))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonBufferVsNoBuffer))
    suite.addTests(loader.loadTestsFromTestCase(TestWordServiceIntegration))
    
    # Ejecutar con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
