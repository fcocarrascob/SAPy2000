"""
Test Suite para detección de errores en inserción de ecuaciones.

Este módulo está diseñado para ejecutarse SIN soluciones parche,
para detectar problemas reales en la inserción de ecuaciones y snippets.

Objetivos:
1. Detectar si BuildUp consume contenido posterior (headings, texto)
2. Detectar párrafos vacíos generados incorrectamente
3. Detectar fragmentación de ecuaciones
4. Verificar integridad de snippets completos
"""

import unittest
import os
import json
from comtypes.client import CreateObject


def get_word_app():
    """Obtiene o crea instancia de Word visible."""
    try:
        word = CreateObject("Word.Application")
        word.Visible = True
        return word
    except Exception as e:
        print(f"Error creando Word: {e}")
        return None


class TestEquationIntegrity(unittest.TestCase):
    """
    Tests para verificar la integridad de ecuaciones sin parches.
    Todos los tests usan el MISMO documento Word.
    """
    
    word_app = None
    doc = None
    ws = None  # WordService real
    
    @classmethod
    def setUpClass(cls):
        """Inicializar Word y WordService."""
        cls.word_app = get_word_app()
        if cls.word_app:
            cls.doc = cls.word_app.Documents.Add()
            
            # Título del documento
            selection = cls.word_app.Selection
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
            selection.TypeText("TEST SUITE: Detección de Errores (Sin Parches)")
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
        
        # Cargar WordService
        try:
            import sys
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from Reportes.word_service import WordService
            cls.ws = WordService()
            cls.ws.word_app = cls.word_app
        except Exception as e:
            print(f"Error cargando WordService: {e}")
            cls.ws = None
    
    @classmethod
    def tearDownClass(cls):
        """Dejar Word abierto para inspección."""
        print("\n" + "=" * 60)
        print("DOCUMENTO WORD ABIERTO PARA INSPECCIÓN")
        print("=" * 60)
    
    def _add_section(self, title):
        """Agrega separador visual para cada test."""
        selection = self.word_app.Selection
        selection.TypeParagraph()
        selection.TypeText(f"--- {title} ---")
        selection.TypeParagraph()
    
    def _count_content_in_range(self, start_pos, end_pos):
        """Analiza el contenido en un rango."""
        doc_range = self.doc.Range(start_pos, end_pos)
        
        stats = {
            "total": 0,
            "empty": 0,
            "headings": 0,
            "equations": 0,
            "text": 0,
            "heading_texts": [],
            "all_text": doc_range.Text
        }
        
        for para in doc_range.Paragraphs:
            stats["total"] += 1
            text = para.Range.Text.replace('\r', '').strip()
            style = str(para.Style.NameLocal).lower()
            
            if text == "":
                stats["empty"] += 1
            elif para.Range.OMaths.Count > 0:
                stats["equations"] += 1
            elif "heading" in style or "título" in style:
                stats["headings"] += 1
                stats["heading_texts"].append(text[:30])
            else:
                stats["text"] += 1
        
        return stats

    # =========================================================================
    # TEST 1: Ecuación simple entre headings
    # =========================================================================
    def test_01_simple_equation_between_headings(self):
        """
        CRÍTICO: Verificar que un heading después de ecuación NO se pierde.
        """
        self._add_section("TEST 01: Ecuación simple entre headings")
        
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        h1_id = "HEADING_ANTES_001"
        h2_id = "HEADING_DESPUES_002"
        
        start_pos = self.word_app.Selection.Range.Start
        
        self.ws.insert_heading(h1_id, level=2)
        self.ws.insert_equation("E = mc²")
        self.ws.insert_heading(h2_id, level=2)
        
        end_pos = self.word_app.Selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        # Verificaciones
        h1_found = h1_id in stats["all_text"]
        h2_found = h2_id in stats["all_text"]
        
        print(f"\nTEST 01:")
        print(f"  H1 encontrado: {h1_found}")
        print(f"  H2 encontrado: {h2_found}")
        print(f"  Headings con estilo: {stats['headings']}")
        print(f"  Párrafos vacíos: {stats['empty']}")
        
        # Assertions
        self.assertTrue(h1_found, f"Heading antes PERDIDO: '{h1_id}'")
        self.assertTrue(h2_found, f"Heading después PERDIDO: '{h2_id}' - BuildUp lo consumió")
        self.assertEqual(stats["headings"], 2, f"Deberían haber 2 headings, hay {stats['headings']}")
        self.assertEqual(stats["empty"], 0, f"No debería haber párrafos vacíos, hay {stats['empty']}")

    # =========================================================================
    # TEST 2: Múltiples ecuaciones consecutivas
    # =========================================================================
    def test_02_multiple_consecutive_equations(self):
        """
        Verificar que múltiples ecuaciones no generen párrafos vacíos extra.
        """
        self._add_section("TEST 02: Múltiples ecuaciones consecutivas")
        
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        start_pos = self.word_app.Selection.Range.Start
        
        self.ws.insert_heading("Ecuaciones Múltiples", level=2)
        
        equations = [
            "E = mc²",
            "a² + b² = c²",
            "F = ma",
        ]
        
        for eq in equations:
            self.ws.insert_equation(eq)
        
        self.ws.insert_heading("Siguiente Sección", level=2)
        
        end_pos = self.word_app.Selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        print(f"\nTEST 02:")
        print(f"  Total párrafos: {stats['total']}")
        print(f"  Ecuaciones: {stats['equations']}")
        print(f"  Párrafos vacíos: {stats['empty']}")
        
        # Esperamos: 2 headings + 3 ecuaciones = 5 párrafos mínimo
        expected_min = 2 + len(equations)
        excess = stats["total"] - expected_min
        
        print(f"  Exceso de párrafos: {excess}")
        
        self.assertEqual(stats["equations"], len(equations), 
            f"Deberían haber {len(equations)} ecuaciones")
        self.assertEqual(stats["empty"], 0, 
            f"No debería haber párrafos vacíos, hay {stats['empty']}")

    # =========================================================================
    # TEST 3: Ecuación compleja (fracción/matriz)
    # =========================================================================
    def test_03_complex_equation(self):
        """
        Verificar ecuaciones complejas (fracciones, matrices) que podrían causar más problemas.
        """
        self._add_section("TEST 03: Ecuaciones complejas")
        
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        start_pos = self.word_app.Selection.Range.Start
        
        h1 = "COMPLEX_ANTES_003"
        h2 = "COMPLEX_DESPUES_003"
        
        self.ws.insert_heading(h1, level=2)
        
        # Ecuación con fracción compleja
        self.ws.insert_equation("S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4")
        
        self.ws.insert_heading(h2, level=2)
        
        end_pos = self.word_app.Selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        h1_found = h1 in stats["all_text"]
        h2_found = h2 in stats["all_text"]
        
        print(f"\nTEST 03:")
        print(f"  H1 encontrado: {h1_found}")
        print(f"  H2 encontrado: {h2_found}")
        print(f"  Párrafos vacíos: {stats['empty']}")
        
        self.assertTrue(h1_found and h2_found, 
            f"Heading perdido: H1={h1_found}, H2={h2_found}")

    # =========================================================================
    # TEST 4: Secuencia H → Eq → H → Eq → H
    # =========================================================================
    def test_04_alternating_heading_equation(self):
        """
        Patrón típico de snippet: heading seguido de ecuación, repetido.
        """
        self._add_section("TEST 04: Secuencia alternada H-Eq-H-Eq")
        
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        headings = [
            "SEC_A_004",
            "SEC_B_004",
            "SEC_C_004",
            "SEC_D_004",
        ]
        
        equations = [
            "eq_1 = 1",
            "eq_2 = 2",
            "eq_3 = 3",
        ]
        
        start_pos = self.word_app.Selection.Range.Start
        
        for i in range(3):
            self.ws.insert_heading(headings[i], level=3)
            self.ws.insert_equation(equations[i])
        
        self.ws.insert_heading(headings[3], level=3)
        
        end_pos = self.word_app.Selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        # Verificar que todos los headings existen
        missing = [h for h in headings if h not in stats["all_text"]]
        
        print(f"\nTEST 04:")
        print(f"  Headings encontrados: {len(headings) - len(missing)}/{len(headings)}")
        print(f"  Headings perdidos: {missing}")
        print(f"  Párrafos vacíos: {stats['empty']}")
        
        self.assertEqual(len(missing), 0, f"Headings perdidos: {missing}")
        self.assertEqual(stats["headings"], len(headings), 
            f"Deberían haber {len(headings)} headings con estilo")

    # =========================================================================
    # TEST 5: Texto después de ecuación
    # =========================================================================
    def test_05_text_after_equation(self):
        """
        Verificar que el texto después de una ecuación no se pierde.
        """
        self._add_section("TEST 05: Texto después de ecuación")
        
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        text_id = "TEXTO_UNICO_DESPUES_EQ_005"
        
        start_pos = self.word_app.Selection.Range.Start
        
        self.ws.insert_heading("Sección", level=2)
        self.ws.insert_equation("∫_0^∞ e^(-x²) dx")
        self.ws.insert_text_at_cursor(text_id, "Normal")
        self.ws.insert_heading("Siguiente", level=2)
        
        end_pos = self.word_app.Selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        text_found = text_id in stats["all_text"]
        
        print(f"\nTEST 05:")
        print(f"  Texto encontrado: {text_found}")
        print(f"  Párrafos vacíos: {stats['empty']}")
        
        self.assertTrue(text_found, f"Texto perdido: '{text_id}'")


class TestSnippetIntegrity(unittest.TestCase):
    """
    Tests para verificar la integridad de snippets completos.
    """
    
    @classmethod
    def setUpClass(cls):
        # Reusar Word
        if TestEquationIntegrity.word_app is None:
            cls.word_app = get_word_app()
            cls.doc = cls.word_app.Documents.Add() if cls.word_app else None
        else:
            cls.word_app = TestEquationIntegrity.word_app
            cls.doc = TestEquationIntegrity.doc
        
        cls.ws = TestEquationIntegrity.ws
        
        # Cargar snippet sísmica
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            snippet_path = os.path.join(project_root, "Reportes", "library", "01_casos_de_carga.json")
            
            with open(snippet_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            cls.sismica_snippet = None
            for snippet in data.get("snippets", []):
                if snippet.get("id") == "solicitud_sismica_e":
                    cls.sismica_snippet = snippet
                    break
        except Exception as e:
            print(f"Error cargando snippet: {e}")
            cls.sismica_snippet = None
        
        if cls.word_app:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
            selection.TypeText("=== TESTS: Integridad de Snippets ===")
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
    
    def _count_content_in_range(self, start_pos, end_pos):
        """Analiza el contenido en un rango."""
        doc_range = self.doc.Range(start_pos, end_pos)
        
        stats = {
            "total": 0,
            "empty": 0,
            "headings": 0,
            "equations": 0,
            "text": 0,
        }
        
        for para in doc_range.Paragraphs:
            stats["total"] += 1
            text = para.Range.Text.replace('\r', '').strip()
            style = str(para.Style.NameLocal).lower()
            
            if text == "":
                stats["empty"] += 1
            elif para.Range.OMaths.Count > 0:
                stats["equations"] += 1
            elif "heading" in style or "título" in style:
                stats["headings"] += 1
            else:
                stats["text"] += 1
        
        return stats

    def test_snippet_sismica_complete(self):
        """
        Insertar snippet sísmica completo y verificar integridad.
        """
        if not self.ws or not self.sismica_snippet:
            self.skipTest("WordService o snippet no disponible")
        
        selection = self.word_app.Selection
        selection.TypeText(">>> Snippet Sísmica Completo")
        selection.TypeParagraph()
        
        # Contar elementos esperados en el snippet
        expected_headings = sum(1 for b in self.sismica_snippet["content"] if b.get("type") == "heading")
        expected_equations = sum(1 for b in self.sismica_snippet["content"] if b.get("type") == "equation")
        expected_text = sum(1 for b in self.sismica_snippet["content"] if b.get("type") == "text")
        
        start_pos = selection.Range.Start
        
        # Insertar usando TemplateEngine
        try:
            from Reportes.template_engine import TemplateEngine
            te = TemplateEngine()
            te.word_service = self.ws
            te.process_blocks(self.sismica_snippet["content"])
        except Exception as e:
            self.fail(f"Error insertando snippet: {e}")
        
        end_pos = selection.Range.Start
        
        stats = self._count_content_in_range(start_pos, end_pos)
        
        print(f"\nSNIPPET SÍSMICA:")
        print(f"  Esperado: {expected_headings} headings, {expected_equations} ecuaciones, {expected_text} textos")
        print(f"  Obtenido: {stats['headings']} headings, {stats['equations']} ecuaciones, {stats['text']} textos")
        print(f"  Párrafos vacíos: {stats['empty']}")
        print(f"  Total párrafos: {stats['total']}")
        
        # Verificaciones
        self.assertEqual(stats["headings"], expected_headings, 
            f"Headings: esperados {expected_headings}, obtenidos {stats['headings']}")
        self.assertEqual(stats["equations"], expected_equations, 
            f"Ecuaciones: esperadas {expected_equations}, obtenidas {stats['equations']}")
        self.assertEqual(stats["empty"], 0, 
            f"No debería haber párrafos vacíos, hay {stats['empty']}")


class TestFragmentationDetection(unittest.TestCase):
    """
    Tests para detectar fragmentación de ecuaciones.
    """
    
    @classmethod
    def setUpClass(cls):
        if TestEquationIntegrity.word_app is None:
            cls.word_app = get_word_app()
            cls.doc = cls.word_app.Documents.Add() if cls.word_app else None
        else:
            cls.word_app = TestEquationIntegrity.word_app
            cls.doc = TestEquationIntegrity.doc
        
        cls.ws = TestEquationIntegrity.ws
        
        if cls.word_app:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
            selection.TypeText("=== TESTS: Detección de Fragmentación ===")
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()

    def test_equation_single_paragraph(self):
        """
        Verificar que una ecuación display ocupa exactamente 1 párrafo.
        """
        if not self.ws:
            self.skipTest("WordService no disponible")
        
        selection = self.word_app.Selection
        selection.TypeText(">>> Ecuación debe ser 1 párrafo")
        selection.TypeParagraph()
        
        # Marcar inicio
        start_pos = selection.Range.Start
        para_before = self.doc.Paragraphs.Count
        
        self.ws.insert_equation("E = mc²")
        
        para_after = self.doc.Paragraphs.Count
        end_pos = selection.Range.Start
        
        # Una ecuación debería agregar exactamente 1 párrafo
        paragraphs_added = para_after - para_before
        
        print(f"\nFRAGMENTACIÓN:")
        print(f"  Párrafos agregados por ecuación: {paragraphs_added}")
        
        # Idealmente debería ser 1, pero puede ser 2 si incluye el párrafo final
        self.assertLessEqual(paragraphs_added, 2, 
            f"Ecuación fragmentada en {paragraphs_added} párrafos (máximo esperado: 2)")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEquationIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestSnippetIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestFragmentationDetection))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
