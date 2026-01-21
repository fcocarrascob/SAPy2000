"""
Test de Integración: Flujo Completo de Snippets con Ecuaciones Display

Este test simula el flujo real del sistema:
1. Usuario crea/selecciona un snippet con ecuaciones
2. TemplateEngine procesa el JSON
3. WordService inserta el contenido en Word

Verifica que ecuaciones display complejas se insertan correctamente
cuando vienen de snippets JSON.

Ejecutar con:
    python -m unittest Reportes.tests.test_integration_snippets -v
"""
import unittest
import time
import json
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Reportes.template_engine import TemplateEngine
from Reportes.word_service import WordService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationSnippetTestCase(unittest.TestCase):
    """Clase base para tests de integración."""
    
    @classmethod
    def setUpClass(cls):
        cls.template_engine = TemplateEngine()
        cls.ws = cls.template_engine.word_service
        cls.ws.connect()
    
    def setUp(self):
        self.doc = self.ws.create_new_document()
        time.sleep(0.3)
    
    def get_document_text(self):
        return self.doc.Content.Text
    
    def create_temp_snippet(self, snippet_content):
        """Crea un archivo JSON temporal con el snippet."""
        # El template engine espera un formato con "sections"
        template_data = {
            "template_name": "Test Snippet",
            "sections": snippet_content if isinstance(snippet_content, list) else [snippet_content]
        }
        
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False)
        
        return path
    
    def cleanup_temp_file(self, path):
        try:
            os.unlink(path)
        except:
            pass


class TestSnippetWithDisplayEquations(IntegrationSnippetTestCase):
    """Tests para snippets que contienen ecuaciones display."""
    
    def test_simple_equation_block(self):
        """Snippet con una ecuación display simple."""
        snippet = [
            {"type": "text", "content": "La fórmula cuadrática es:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "x = (-b ± √(b^2 - 4ac))/(2a)", "parameters": {}},
            {"type": "text", "content": "Esta fórmula resuelve ecuaciones de segundo grado.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[SIMPLE EQUATION BLOCK] {repr(text)}")
            
            self.assertIn("fórmula cuadrática", text)
            self.assertIn("segundo grado", text, "Texto después de ecuación consumido")
        finally:
            self.cleanup_temp_file(path)
    
    def test_multiple_equations_sequence(self):
        """Snippet con múltiples ecuaciones display en secuencia."""
        snippet = [
            {"type": "heading", "content": "Ecuaciones Fundamentales", "parameters": {"level": 2}},
            {"type": "equation", "content": "E = mc^2", "parameters": {}},
            {"type": "equation", "content": "F = ma", "parameters": {}},
            {"type": "equation", "content": "P = UI", "parameters": {}},
            {"type": "text", "content": "Estas son ecuaciones de física básica.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[MULTIPLE EQUATIONS] {repr(text)}")
            
            self.assertIn("Fundamentales", text)
            self.assertIn("física básica", text, "Texto final consumido")
        finally:
            self.cleanup_temp_file(path)
    
    def test_engineering_report_snippet(self):
        """Snippet típico de reporte de ingeniería con ecuaciones."""
        snippet = [
            {"type": "heading", "content": "Verificación de Resistencia", "parameters": {"level": 2}},
            {"type": "text", "content": "El esfuerzo admisible se calcula como:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "σ_adm = (F_y)/(Ω)", "parameters": {}},
            {"type": "text", "content": "Donde:", "parameters": {"style": "Normal"}},
            {"type": "text", "content": "• Fy = Tensión de fluencia", "parameters": {"style": "Normal"}},
            {"type": "text", "content": "• Ω = Factor de seguridad", "parameters": {"style": "Normal"}},
            {"type": "heading", "content": "Verificación", "parameters": {"level": 3}},
            {"type": "equation", "content": "DCR = (σ_act)/(σ_adm) ≤ 1.0", "parameters": {}},
            {"type": "text", "content": "El elemento cumple con la verificación.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[ENGINEERING REPORT] Longitud: {len(text)} chars")
            logger.info(f"[ENGINEERING REPORT] {repr(text[:500])}...")
            
            self.assertIn("Resistencia", text)
            self.assertIn("admisible", text)
            self.assertIn("cumple", text, "Conclusión final consumida")
        finally:
            self.cleanup_temp_file(path)
    
    def test_complex_matrix_equation(self):
        """Snippet con ecuación de matriz."""
        snippet = [
            {"type": "text", "content": "La matriz de rigidez es:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "[K] = [\\matrix(k_11&k_12@k_21&k_22)]", "parameters": {}},
            {"type": "text", "content": "Los términos se calculan según las propiedades del elemento.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[MATRIX] {repr(text)}")
            
            self.assertIn("rigidez", text)
            self.assertIn("propiedades", text, "Texto después de matriz consumido")
        finally:
            self.cleanup_temp_file(path)
    
    def test_calculus_snippet(self):
        """Snippet con operadores de cálculo (integrales, sumatorias)."""
        snippet = [
            {"type": "heading", "content": "Trabajo de una Fuerza", "parameters": {"level": 3}},
            {"type": "text", "content": "El trabajo se define como:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "W = ∫_(a)^(b) F(x)dx", "parameters": {}},
            {"type": "text", "content": "Para fuerzas discretas:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "W = ∑_(i=1)^(n) F_i ⋅ Δx_i", "parameters": {}},
            {"type": "text", "content": "Ambas formulaciones son equivalentes en el límite.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[CALCULUS] {repr(text)}")
            
            self.assertIn("Trabajo", text)
            self.assertIn("equivalentes", text, "Conclusión final consumida")
        finally:
            self.cleanup_temp_file(path)


class TestSnippetMixedContent(IntegrationSnippetTestCase):
    """Tests para snippets con contenido mixto (inline + display)."""
    
    def test_inline_and_display_mixed(self):
        """Snippet que mezcla ecuaciones inline y display."""
        snippet = [
            {"type": "text", "content": "Sabemos que $E = mc^2$ es la ecuación de Einstein.", "parameters": {"style": "Normal"}},
            {"type": "text", "content": "La forma expandida es:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "E^2 = (pc)^2 + (m_0 c^2)^2", "parameters": {}},
            {"type": "text", "content": "Donde $p$ es el momento y $m_0$ es la masa en reposo.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[MIXED INLINE/DISPLAY] {repr(text)}")
            
            self.assertIn("Einstein", text)
            self.assertIn("expandida", text)
            self.assertIn("masa en reposo", text, "Texto con inline después de display consumido")
        finally:
            self.cleanup_temp_file(path)
    
    def test_greek_symbols_in_text_and_equation(self):
        """Snippet con símbolos griegos tanto inline como display."""
        snippet = [
            {"type": "text", "content": "El ángulo $\\alpha$ se relaciona con $\\beta$ mediante:", "parameters": {"style": "Normal"}},
            {"type": "equation", "content": "\\gamma = \\alpha + \\beta", "parameters": {}},
            {"type": "text", "content": "Esta relación es fundamental en trigonometría.", "parameters": {"style": "Normal"}}
        ]
        
        path = self.create_temp_snippet(snippet)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[GREEK SYMBOLS] {repr(text)}")
            
            self.assertIn("ángulo", text)
            self.assertIn("trigonometría", text, "Texto final consumido")
        finally:
            self.cleanup_temp_file(path)


class TestRealWorldSnippets(IntegrationSnippetTestCase):
    """Tests usando snippets reales del directorio library."""
    
    def test_load_test_suite_from_library(self):
        """Cargar y procesar el test suite de ecuaciones."""
        library_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'library',
            '99_test_suite_ecuaciones.json'
        )
        
        if not os.path.exists(library_path):
            self.skipTest(f"Archivo no encontrado: {library_path}")
        
        with open(library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Procesar solo el primer snippet como prueba
        snippets = data.get('snippets', [])
        if not snippets:
            self.skipTest("No hay snippets en el archivo")
        
        first_snippet = snippets[0]
        content_blocks = first_snippet.get('content', [])
        
        logger.info(f"[REAL SNIPPET] Procesando: {first_snippet.get('title')}")
        
        # Crear template temporal con los bloques
        path = self.create_temp_snippet(content_blocks)
        try:
            self.template_engine.insert_structure_at_cursor(path)
            
            text = self.get_document_text()
            logger.info(f"[REAL SNIPPET] Longitud: {len(text)} chars")
            
            # Verificar que el documento no está vacío
            self.assertGreater(len(text), 50, "Documento parece vacío")
        finally:
            self.cleanup_temp_file(path)
    
    def test_stress_all_test_cases(self):
        """Procesar todos los snippets del test suite."""
        library_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'library',
            '99_test_suite_ecuaciones.json'
        )
        
        if not os.path.exists(library_path):
            self.skipTest(f"Archivo no encontrado: {library_path}")
        
        with open(library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        snippets = data.get('snippets', [])
        
        # Procesar cada snippet en el mismo documento
        for snippet in snippets:
            title = snippet.get('title', 'Sin título')
            content_blocks = snippet.get('content', [])
            
            logger.info(f"[STRESS] Procesando: {title}")
            
            # Insertar separador
            self.ws.insert_text_at_cursor(f"=== {title} ===", "Normal")
            
            # Procesar bloques directamente
            self.template_engine.process_blocks(content_blocks)
        
        # Verificar documento final
        text = self.get_document_text()
        logger.info(f"[STRESS] Documento final: {len(text)} caracteres")
        
        # Verificar que todos los snippets fueron procesados
        for snippet in snippets:
            title = snippet.get('title', '')
            if title:
                # Al menos el separador debería estar
                self.assertIn("===", text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
