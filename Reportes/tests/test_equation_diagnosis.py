"""
Test Suite: Diagnóstico y Solución del Bug de BuildUp

DIAGNÓSTICO CONFIRMADO:
El problema NO es que BuildUp "consume" texto, sino que al convertir
una ecuación inline, Word la renderiza como DISPLAY (multilínea),
insertando saltos de párrafo (\r) DENTRO de la ecuación.

Esto causa que el texto que sigue a la ecuación sea empujado a nuevas líneas,
dando la apariencia de que fue "consumido".

CAUSA RAÍZ:
omath.Range.OMaths(1).Type = 1 (wdOMathInline) se aplica DESPUÉS de BuildUp,
pero el rango de la ecuación ya se ha expandido para incluir múltiples líneas.

SOLUCIÓN PROPUESTA:
1. Forzar modo inline ANTES de BuildUp si es posible
2. O usar un enfoque diferente: no usar BuildUp para ecuaciones simples inline
3. O aplicar Range.InsertAfter con contenido protegido

Ejecutar con:
    python -m unittest Reportes.tests.test_equation_diagnosis -v
"""
import unittest
import time
import comtypes.client
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordTestCase(unittest.TestCase):
    """Clase base para tests con Word."""
    
    @classmethod
    def setUpClass(cls):
        try:
            cls.word_app = comtypes.client.GetActiveObject("Word.Application")
        except Exception:
            cls.word_app = comtypes.client.CreateObject("Word.Application")
            cls.word_app.Visible = True
        cls.word_app.Visible = True
    
    def setUp(self):
        self.doc = self.word_app.Documents.Add()
        self.selection = self.word_app.Selection
        time.sleep(0.2)
    
    def tearDown(self):
        # Mantener documentos abiertos para inspección visual
        pass


class TestDiagnosticInlineEquationFragmentation(WordTestCase):
    """
    Tests para diagnosticar cómo BuildUp fragmenta ecuaciones inline.
    """
    
    def test_simple_equation_paragraph_count(self):
        """
        Cuenta cuántos saltos de párrafo introduce BuildUp en una ecuación simple.
        """
        equation = "x^2"
        
        # Texto antes
        self.selection.TypeText("Antes: ")
        
        # Insertar ecuación inline SIN buffer (método actual)
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        # Contar párrafos ANTES de BuildUp
        paragraphs_before = self.doc.Paragraphs.Count
        
        omath.BuildUp()
        omath.Range.OMaths(1).Type = 1  # wdOMathInline
        
        # Contar párrafos DESPUÉS de BuildUp
        paragraphs_after = self.doc.Paragraphs.Count
        
        # Mover al final y escribir texto
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(" Después")
        
        full_text = self.doc.Content.Text
        
        logger.info(f"[SIMPLE x^2]")
        logger.info(f"  Párrafos antes:  {paragraphs_before}")
        logger.info(f"  Párrafos después: {paragraphs_after}")
        logger.info(f"  Párrafos añadidos por BuildUp: {paragraphs_after - paragraphs_before}")
        logger.info(f"  Texto completo: {repr(full_text)}")
        
        # El problema: BuildUp añade párrafos
        if paragraphs_after > paragraphs_before:
            logger.warning(f"  ⚠️  BuildUp añadió {paragraphs_after - paragraphs_before} párrafos!")
    
    def test_fraction_equation_paragraph_count(self):
        """
        Cuenta párrafos para una fracción (caso más problemático).
        """
        equation = "a/b"
        
        self.selection.TypeText("Fracción: ")
        
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        paragraphs_before = self.doc.Paragraphs.Count
        
        omath.BuildUp()
        omath.Range.OMaths(1).Type = 1
        
        paragraphs_after = self.doc.Paragraphs.Count
        
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(" continúa...")
        
        full_text = self.doc.Content.Text
        
        logger.info(f"[FRACCIÓN a/b]")
        logger.info(f"  Párrafos antes:  {paragraphs_before}")
        logger.info(f"  Párrafos después: {paragraphs_after}")
        logger.info(f"  Párrafos añadidos: {paragraphs_after - paragraphs_before}")
        logger.info(f"  Texto: {repr(full_text)}")


class TestSolutionLinearMode(WordTestCase):
    """
    SOLUCIÓN 1: NO usar BuildUp para ecuaciones inline simples.
    Mantener la ecuación en modo "linear" (como texto).
    """
    
    def test_inline_without_buildup(self):
        """
        Insertar ecuación inline SIN llamar a BuildUp.
        La ecuación permanece en formato linear pero es reconocida como OMath.
        """
        equation = "x^2 + y^2 = z^2"
        
        self.selection.TypeText("Teorema: ")
        
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        # NO llamar BuildUp - mantener linear
        # omath.BuildUp()  # <-- COMENTADO
        
        # Solo establecer tipo inline
        try:
            omath.Range.OMaths(1).Type = 1
        except:
            pass
        
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(" es famoso.")
        self.selection.TypeParagraph()
        self.selection.TypeText("Este párrafo debe estar en la siguiente línea.")
        
        full_text = self.doc.Content.Text
        paragraph_count = full_text.count('\r')
        
        logger.info(f"[SIN BUILDUP]")
        logger.info(f"  Saltos de párrafo: {paragraph_count}")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("es famoso", full_text)
        self.assertIn("siguiente línea", full_text)


class TestSolutionTypeInlineBeforeBuildUp(WordTestCase):
    """
    SOLUCIÓN 2: Establecer Type=Inline ANTES de BuildUp.
    """
    
    def test_set_type_before_buildup(self):
        """
        Intentar forzar modo inline antes de BuildUp.
        """
        equation = "E = mc^2"
        
        self.selection.TypeText("Einstein: ")
        
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        paragraphs_before = self.doc.Paragraphs.Count
        
        # NUEVO: Establecer tipo ANTES de BuildUp
        try:
            omath.Range.OMaths(1).Type = 1  # wdOMathInline ANTES
        except Exception as e:
            logger.warning(f"  No se pudo establecer tipo antes: {e}")
        
        omath.BuildUp()
        
        # Reforzar tipo después también
        try:
            omath.Range.OMaths(1).Type = 1
        except:
            pass
        
        paragraphs_after = self.doc.Paragraphs.Count
        
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(" revolucionó la física.")
        
        full_text = self.doc.Content.Text
        
        logger.info(f"[TYPE ANTES DE BUILDUP]")
        logger.info(f"  Párrafos añadidos: {paragraphs_after - paragraphs_before}")
        logger.info(f"  Texto: {repr(full_text)}")


class TestSolutionOMathJustification(WordTestCase):
    """
    SOLUCIÓN 3: Controlar la justificación del OMath para forzar inline.
    """
    
    def test_set_justification_inline(self):
        """
        Usar la propiedad Justification del OMath.
        wdOMathJustificationInline = 7 según documentación.
        """
        equation = "F = ma"
        
        self.selection.TypeText("Newton: ")
        
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        paragraphs_before = self.doc.Paragraphs.Count
        
        # Intentar configurar justificación antes de BuildUp
        try:
            # wdOMathJustificationInline = 7 (no es estándar, probar valores)
            omath.Justification = 7
        except Exception as e:
            logger.debug(f"  Justification falló: {e}")
        
        omath.BuildUp()
        omath.Range.OMaths(1).Type = 1
        
        paragraphs_after = self.doc.Paragraphs.Count
        
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(" explicó el movimiento.")
        
        full_text = self.doc.Content.Text
        
        logger.info(f"[JUSTIFICATION]")
        logger.info(f"  Párrafos añadidos: {paragraphs_after - paragraphs_before}")
        logger.info(f"  Texto: {repr(full_text)}")


class TestSolutionManualOmmlControl(WordTestCase):
    """
    SOLUCIÓN 4: Control manual del rango durante BuildUp.
    Guardar posiciones exactas y restaurar después.
    """
    
    def test_range_protection_during_buildup(self):
        """
        Proteger el rango que sigue a la ecuación guardando su contenido.
        """
        equation = "∫f(x)dx"
        next_text = " es una integral."
        final_marker = "MARCADOR_FINAL"
        
        self.selection.TypeText("Cálculo: ")
        
        # Guardar posición antes de ecuación
        pre_eq_pos = self.selection.Range.Start
        
        # Insertar ecuación
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        # GUARDAR posición exacta del final de la ecuación
        eq_end_before_buildup = omath.Range.End
        
        paragraphs_before = self.doc.Paragraphs.Count
        
        omath.BuildUp()
        omath.Range.OMaths(1).Type = 1
        
        paragraphs_after = self.doc.Paragraphs.Count
        
        # OBTENER nueva posición del final de ecuación post-BuildUp
        eq_end_after_buildup = omath.Range.End
        
        logger.info(f"[RANGE PROTECTION]")
        logger.info(f"  Fin ecuación antes BuildUp: {eq_end_before_buildup}")
        logger.info(f"  Fin ecuación después BuildUp: {eq_end_after_buildup}")
        logger.info(f"  Diferencia de posición: {eq_end_after_buildup - eq_end_before_buildup}")
        logger.info(f"  Párrafos añadidos: {paragraphs_after - paragraphs_before}")
        
        # Posicionar cursor al final real de la ecuación
        self.selection.SetRange(omath.Range.End, omath.Range.End)
        self.selection.TypeText(next_text)
        self.selection.TypeParagraph()
        self.selection.TypeText(final_marker)
        
        full_text = self.doc.Content.Text
        logger.info(f"  Texto final: {repr(full_text)}")
        
        self.assertIn("integral", full_text)
        self.assertIn(final_marker, full_text)


class TestSolutionLinearFallback(WordTestCase):
    """
    SOLUCIÓN 5 (HÍBRIDA): Usar BuildUp selectivamente.
    - Ecuaciones simples: NO BuildUp (linear mode)
    - Ecuaciones complejas: BuildUp con buffer
    """
    
    def _is_simple_equation(self, eq_text):
        """Determina si una ecuación es 'simple' y puede quedarse linear."""
        # Ecuaciones simples: solo variables, operadores básicos, exponentes simples
        # Complejas: fracciones, raíces, matrices, integrales
        complex_patterns = [
            r'/',           # Fracciones
            r'√',           # Raíces
            r'∫',           # Integrales
            r'∑',           # Sumatorias
            r'∏',           # Productorias
            r'■',           # Matrices
            r'█',           # Eqarray
            r'\^{\(',       # Exponentes complejos (más de un carácter)
        ]
        for pattern in complex_patterns:
            if re.search(pattern, eq_text):
                return False
        return True
    
    def test_smart_buildup_decision(self):
        """
        Aplicar BuildUp solo cuando es necesario.
        """
        test_cases = [
            ("x^2", True),           # Simple - no necesita BuildUp
            ("a + b = c", True),     # Simple
            ("a/b", False),          # Fracción - necesita BuildUp
            ("√(x)", False),         # Raíz - necesita BuildUp
            ("E = mc^2", True),      # Simple exponente
        ]
        
        for eq, expected_simple in test_cases:
            is_simple = self._is_simple_equation(eq)
            logger.info(f"  '{eq}' -> Simple: {is_simple} (esperado: {expected_simple})")
            self.assertEqual(is_simple, expected_simple)
    
    def test_hybrid_insertion(self):
        """
        Prueba inserción híbrida: BuildUp solo para complejas.
        """
        # Ecuación simple - sin BuildUp
        self.selection.TypeText("Simple: ")
        self._insert_smart_inline("x^2")
        self.selection.TypeText(" ok. ")
        
        # Ecuación compleja - con BuildUp y buffer
        self.selection.TypeText("Compleja: ")
        self._insert_smart_inline("a/b")
        self.selection.TypeText(" también ok.")
        
        self.selection.TypeParagraph()
        self.selection.TypeText("LÍNEA FINAL INTACTA")
        
        full_text = self.doc.Content.Text
        
        logger.info(f"[HÍBRIDO]")
        logger.info(f"  Texto: {repr(full_text)}")
        
        self.assertIn("LÍNEA FINAL INTACTA", full_text)
    
    def _insert_smart_inline(self, equation_text):
        """Inserta ecuación inline de forma inteligente."""
        is_simple = self._is_simple_equation(equation_text)
        
        start_pos = self.selection.Range.Start
        self.selection.TypeText(equation_text)
        end_pos = self.selection.Range.Start
        
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        if is_simple:
            # Ecuación simple: NO BuildUp, solo marcar como OMath
            logger.debug(f"  {equation_text}: Modo LINEAR (sin BuildUp)")
        else:
            # Ecuación compleja: BuildUp necesario
            # Aplicar mini-buffer de 1 párrafo
            self.selection.TypeParagraph()
            self.selection.MoveUp(4, 1, 0)
            
            omath.BuildUp()
            logger.debug(f"  {equation_text}: BuildUp aplicado")
        
        try:
            omath.Range.OMaths(1).Type = 1  # wdOMathInline
        except:
            pass
        
        self.selection.SetRange(omath.Range.End, omath.Range.End)


if __name__ == '__main__':
    unittest.main(verbosity=2)
