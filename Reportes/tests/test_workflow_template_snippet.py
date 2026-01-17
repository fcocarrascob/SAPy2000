"""
Test del flujo de trabajo: Template + Snippet con ecuaciones.

Este test replica el flujo real del usuario:
1. Generar documento Word con template estructura_acero.json
2. Navegar a sección "Estados de Carga"
3. Insertar snippet "Solicitación Sísmica [E] 2025 AME"
4. Analizar párrafos vacíos generados

OBJETIVO: Identificar por qué se generan demasiados párrafos vacíos
cuando se insertan snippets con múltiples ecuaciones display.
"""

import unittest
import os
import json
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


class TestWorkflowTemplateSnippet(unittest.TestCase):
    """
    Test del flujo completo: Template → Snippet con ecuaciones.
    Todos los tests usan el MISMO documento Word.
    """
    
    word_app = None
    doc = None
    project_root = None
    
    @classmethod
    def setUpClass(cls):
        """Inicializar Word y cargar paths."""
        cls.word_app = get_word_app()
        if cls.word_app:
            cls.doc = cls.word_app.Documents.Add()
        
        # Path del proyecto
        cls.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Cargar snippet para los tests
        snippet_path = os.path.join(cls.project_root, "Reportes", "library", "01_casos_de_carga.json")
        with open(snippet_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        # Encontrar el snippet de solicitación sísmica
        cls.sismica_snippet = None
        for snippet in data.get("snippets", []):
            if snippet.get("id") == "solicitud_sismica_e":
                cls.sismica_snippet = snippet
                break
    
    @classmethod
    def tearDownClass(cls):
        """Dejar Word abierto para inspección."""
        print("\n" + "=" * 60)
        print("DOCUMENTO WORD ABIERTO PARA INSPECCIÓN")
        print("Revise los párrafos vacíos manualmente.")
        print("=" * 60)
    
    def _count_empty_paragraphs(self, start_pos, end_pos):
        """Cuenta párrafos vacíos en un rango."""
        doc_range = self.doc.Range(start_pos, end_pos)
        empty_count = 0
        total_count = 0
        
        for para in doc_range.Paragraphs:
            total_count += 1
            text = para.Range.Text
            # Un párrafo vacío solo tiene \r (carriage return)
            # o tiene solo espacios/tabs antes del \r
            stripped = text.replace('\r', '').strip()
            if stripped == "":
                empty_count += 1
        
        return empty_count, total_count
    
    def _analyze_paragraph_content(self, start_pos, end_pos, max_show=30):
        """Analiza y muestra el contenido de cada párrafo en un rango."""
        doc_range = self.doc.Range(start_pos, end_pos)
        paragraphs_info = []
        
        for i, para in enumerate(doc_range.Paragraphs, 1):
            text = para.Range.Text
            style = str(para.Style.NameLocal)
            
            # Clasificar el párrafo
            stripped = text.replace('\r', '').strip()
            if stripped == "":
                para_type = "VACÍO"
            elif para.Range.OMaths.Count > 0:
                para_type = "ECUACIÓN"
            elif "heading" in style.lower() or "título" in style.lower():
                para_type = "HEADING"
            else:
                para_type = "TEXTO"
            
            # Representar el texto (escapar caracteres especiales)
            display_text = repr(text[:40]) if len(text) > 40 else repr(text)
            
            paragraphs_info.append({
                "num": i,
                "type": para_type,
                "style": style,
                "text": display_text
            })
            
            if i <= max_show:
                print(f"    {i:2d}. [{para_type:8s}] {style:20s} | {display_text}")
        
        return paragraphs_info
    
    def _insert_heading(self, text, level=1):
        """Inserta un heading."""
        selection = self.word_app.Selection
        selection.TypeText(text)
        selection.Range.Style = -1 - level
        selection.TypeParagraph()
        selection.Style = -1  # Normal
    
    def _insert_text(self, text):
        """Inserta texto normal."""
        selection = self.word_app.Selection
        selection.TypeText(text)
        selection.TypeParagraph()
    
    def _insert_display_equation_with_buffer(self, equation_text):
        """
        Inserta ecuación display usando la estrategia de 3 párrafos buffer.
        REPLICA EXACTA de word_service.py insert_equation()
        """
        selection = self.word_app.Selection
        selection.Collapse(0)  # wdCollapseEnd
        selection.Style = -1  # Normal
        
        # 3 párrafos buffer
        for _ in range(3):
            selection.TypeParagraph()
        
        # Retroceder 3 párrafos
        selection.MoveUp(4, 3, 0)  # wdParagraph=4
        
        # Insertar ecuación
        start_pos = selection.Range.Start
        selection.TypeText(equation_text)
        end_pos = selection.Range.Start
        
        # Convertir a OMath
        eq_range = self.doc.Range(start_pos, end_pos)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            omath.BuildUp()
            omath.Range.OMaths(1).Type = 0  # Display
        except:
            pass
        
        # Mover al final
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        selection.Style = -1
    
    def _insert_snippet_content(self, content_blocks):
        """Inserta el contenido de un snippet (lista de bloques)."""
        for block in content_blocks:
            block_type = block.get("type")
            content = block.get("content", "")
            params = block.get("parameters", {})
            
            if not content:
                continue
            
            if block_type == "heading":
                level = params.get("level", 1)
                self._insert_heading(content, level)
            
            elif block_type == "text":
                self._insert_text(content)
            
            elif block_type == "equation":
                self._insert_display_equation_with_buffer(content)

    # =========================================================================
    # TEST 1: Simular flujo completo con template parcial
    # =========================================================================
    def test_01_workflow_estados_carga_snippet(self):
        """
        Simular: Estados de Carga → (párrafo) → Snippet Sísmica → Siguiente sección
        """
        selection = self.word_app.Selection
        
        # Título del test
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 01: Flujo Estados de Carga → Snippet Sísmica")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # Marcar inicio
        start_pos = selection.Range.Start
        
        # --- Simular estructura del template ---
        self._insert_heading("Estados de Carga", level=2)  # Del template
        
        # Usuario agrega un párrafo manualmente
        self._insert_text("A continuación se describen los estados de carga considerados:")
        
        # --- Insertar snippet de solicitación sísmica ---
        if self.sismica_snippet:
            self._insert_snippet_content(self.sismica_snippet["content"])
        else:
            self._insert_text("[SNIPPET NO ENCONTRADO]")
        
        # --- Siguiente sección del template ---
        self._insert_heading("Combinaciones de Carga", level=2)  # Del template
        
        self._insert_text("Las combinaciones de carga se definen según...")
        
        # Marcar fin
        end_pos = selection.Range.Start
        
        # --- Análisis de párrafos ---
        empty_count, total_count = self._count_empty_paragraphs(start_pos, end_pos)
        
        selection.TypeParagraph()
        selection.TypeText(f">>> ANÁLISIS: {empty_count} párrafos vacíos de {total_count} totales")
        selection.TypeParagraph()
        
        print(f"\nTEST 01 - Párrafos vacíos: {empty_count} / {total_count} totales")
        
        # El snippet tiene ~8 ecuaciones display
        # Con buffer de 3, esperaríamos ~24 párrafos extra
        # Pero algunos deberían ser consumidos por BuildUp
        
        # Advertir si hay demasiados párrafos vacíos
        if empty_count > 10:
            print(f"  ⚠️  ADVERTENCIA: Demasiados párrafos vacíos ({empty_count})")

    # =========================================================================
    # TEST 2: Análisis detallado - Insertar snippet con diagnóstico
    # =========================================================================
    def test_02_detailed_analysis_snippet(self):
        """
        Insertar snippet ecuación por ecuación con diagnóstico.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 02: Análisis detallado por ecuación")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        self._insert_heading("Sección Antes", level=2)
        
        # Extraer solo las ecuaciones del snippet
        if self.sismica_snippet:
            equations = [
                b["content"] for b in self.sismica_snippet["content"]
                if b.get("type") == "equation"
            ]
            
            for i, eq in enumerate(equations[:5], 1):  # Solo primeras 5
                self._insert_text(f"Ecuación {i}:")
                
                pos_before = selection.Range.Start
                self._insert_display_equation_with_buffer(eq)
                pos_after = selection.Range.Start
                
                # Contar párrafos insertados por esta ecuación
                eq_range = self.doc.Range(pos_before, pos_after)
                para_count = eq_range.Paragraphs.Count
                
                selection.TypeText(f"  [Párrafos generados: {para_count}]")
                selection.TypeParagraph()
        
        self._insert_heading("Sección Después", level=2)
        
        end_pos = selection.Range.Start
        
        empty_count, total_count = self._count_empty_paragraphs(start_pos, end_pos)
        
        selection.TypeParagraph()
        selection.TypeText(f">>> ANÁLISIS: {empty_count} párrafos vacíos de {total_count}")
        selection.TypeParagraph()
        
        print(f"\nTEST 02 - Párrafos vacíos: {empty_count} / {total_count}")

    # =========================================================================
    # TEST 3: Comparar CON y SIN buffer
    # =========================================================================
    def test_03_compare_buffer_strategies(self):
        """
        Comparar inserción de ecuación con y sin buffer.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 03: Comparación CON buffer vs SIN buffer")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # --- CON BUFFER ---
        selection.TypeText(">>> CON BUFFER (3 párrafos):")
        selection.TypeParagraph()
        
        start_con = selection.Range.Start
        
        self._insert_heading("Título Antes (con buffer)", level=2)
        self._insert_display_equation_with_buffer("E = mc²")
        self._insert_heading("Título Después (con buffer)", level=2)
        
        end_con = selection.Range.Start
        
        empty_con, total_con = self._count_empty_paragraphs(start_con, end_con)
        
        selection.TypeText(f"  Párrafos vacíos: {empty_con} / {total_con}")
        selection.TypeParagraph()
        
        # --- SIN BUFFER ---
        selection.TypeParagraph()
        selection.TypeText(">>> SIN BUFFER:")
        selection.TypeParagraph()
        
        start_sin = selection.Range.Start
        
        self._insert_heading("Título Antes (sin buffer)", level=2)
        
        # Insertar ecuación SIN buffer
        selection.Collapse(0)
        eq_start = selection.Range.Start
        selection.TypeText("a² + b² = c²")
        eq_end = selection.Range.Start
        
        eq_range = self.doc.Range(eq_start, eq_end)
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
        
        self._insert_heading("Título Después (sin buffer)", level=2)
        
        end_sin = selection.Range.Start
        
        empty_sin, total_sin = self._count_empty_paragraphs(start_sin, end_sin)
        
        selection.TypeText(f"  Párrafos vacíos: {empty_sin} / {total_sin}")
        selection.TypeParagraph()
        
        # --- Resumen ---
        selection.TypeParagraph()
        selection.TypeText(f"RESUMEN: Con buffer={empty_con} vacíos, Sin buffer={empty_sin} vacíos")
        selection.TypeParagraph()
        
        print(f"\nTEST 03 - Con buffer: {empty_con} vacíos, Sin buffer: {empty_sin} vacíos")

    # =========================================================================
    # TEST 4: Verificar si BuildUp realmente consume los 3 párrafos
    # =========================================================================
    def test_04_buildup_consumption_analysis(self):
        """
        Analizar cuántos párrafos realmente consume BuildUp.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 04: Análisis de consumo de BuildUp")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # Ecuaciones de diferentes complejidades
        test_equations = [
            ("Simple", "E = mc²"),
            ("Fracción", "(a+b)/(c+d)"),
            ("Integral", "∫_0^1 x² dx"),
            ("Matriz", "[■(a&b@c&d)]"),
            ("Larga", "S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4"),
        ]
        
        for name, eq in test_equations:
            selection.TypeText(f">>> Ecuación {name}:")
            selection.TypeParagraph()
            
            # Marcar posición antes
            pos_before = selection.Range.Start
            paragraphs_before = self.doc.Paragraphs.Count
            
            # Insertar con buffer
            self._insert_display_equation_with_buffer(eq)
            
            # Contar después
            paragraphs_after = self.doc.Paragraphs.Count
            pos_after = selection.Range.Start
            
            # Calcular párrafos netos agregados
            net_paragraphs = paragraphs_after - paragraphs_before
            
            # Contar vacíos en el rango
            empty, total = self._count_empty_paragraphs(pos_before, pos_after)
            
            selection.TypeText(f"    Párrafos netos: +{net_paragraphs}, Vacíos: {empty}/{total}")
            selection.TypeParagraph()
            
            print(f"  {name}: +{net_paragraphs} párrafos, {empty} vacíos")

    # =========================================================================
    # TEST 5: Heading inmediatamente después de ecuación
    # =========================================================================
    def test_05_heading_immediately_after_equation(self):
        """
        Verificar comportamiento cuando heading viene inmediatamente después.
        NOTA: Este test verifica tanto el CONTENIDO como el ESTILO.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 05: Heading inmediato post-ecuación")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # Usar identificadores únicos
        h1_text = "Horizontal_T05_001"
        h2_text = "Vertical_T05_002"
        h3_text = "Siguiente_T05_003"
        h4_text = "Final_T05_004"
        
        start_pos = selection.Range.Start
        
        self._insert_heading(h1_text, level=4)
        self._insert_display_equation_with_buffer("S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4")
        self._insert_heading(h2_text, level=4)  # Este es el que se perdía
        self._insert_display_equation_with_buffer("S_a(T_V)=(I⋅S_(aV)(T_V))/(R_V)⋅((0.05)/(ξ_V))^0.4")
        self._insert_heading(h3_text, level=3)
        
        end_pos = selection.Range.Start
        
        # Análisis del rango
        doc_range = self.doc.Range(start_pos, end_pos)
        full_text = doc_range.Text
        
        # Verificar CONTENIDO (si el texto existe)
        content_h1 = h1_text in full_text
        content_h2 = h2_text in full_text
        content_h3 = h3_text in full_text
        
        # Verificar ESTILO (si tiene formato heading)
        heading_count = 0
        headings_with_style = []
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                heading_count += 1
                headings_with_style.append(para.Range.Text.strip()[:30])
        
        selection.TypeParagraph()
        selection.TypeText(f">>> Contenido encontrado: H1={content_h1}, H2={content_h2}, H3={content_h3}")
        selection.TypeParagraph()
        selection.TypeText(f">>> Headings con estilo: {heading_count}/3")
        selection.TypeParagraph()
        selection.TypeText(f">>> Headings: {headings_with_style}")
        selection.TypeParagraph()
        
        # Listar párrafos para diagnóstico
        selection.TypeText(">>> Todos los párrafos:")
        selection.TypeParagraph()
        for i, para in enumerate(doc_range.Paragraphs, 1):
            text = para.Range.Text.strip()[:40]
            style = str(para.Style.NameLocal)
            if text:
                selection.TypeText(f"    {i}: [{style}] {text}")
                selection.TypeParagraph()
        
        print(f"\nTEST 05 - Contenido: H1={content_h1}, H2={content_h2}, H3={content_h3}")
        print(f"TEST 05 - Headings con estilo: {heading_count}/3 -> {headings_with_style}")
        
        # Verificar que el CONTENIDO existe
        self.assertTrue(content_h1 and content_h2 and content_h3,
            f"Contenido perdido: H1={content_h1}, H2={content_h2}, H3={content_h3}")
        
        # Verificar que tienen ESTILO (esto puede fallar si BuildUp modifica el estilo)
        if heading_count < 3:
            print(f"  ⚠️  ADVERTENCIA: Solo {heading_count}/3 headings mantienen estilo")

    # =========================================================================
    # TEST 6: Diagnóstico detallado - qué párrafo se pierde
    # =========================================================================
    def test_06_detailed_paragraph_diagnosis(self):
        """
        Diagnóstico paso a paso para ver exactamente qué se pierde.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 06: Diagnóstico detallado")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Paso 1: Insertar heading
        selection.TypeText("H4: Horizontal_UNICO_001")
        selection.Range.Style = -4  # Heading 4
        selection.TypeParagraph()
        selection.Style = -1
        
        pos_after_h1 = selection.Range.Start
        selection.TypeText(f"  [Pos después de H1: {pos_after_h1}]")
        selection.TypeParagraph()
        
        # Paso 2: Insertar ecuación con buffer
        selection.TypeText(">>> Insertando ecuación...")
        selection.TypeParagraph()
        
        pos_before_eq = selection.Range.Start
        
        # Buffer de 3 párrafos
        selection.Collapse(0)
        selection.Style = -1
        for _ in range(3):
            selection.TypeParagraph()
        
        # Retroceder
        selection.MoveUp(4, 3, 0)
        
        eq_start = selection.Range.Start
        selection.TypeText("E = mc²")
        eq_end = selection.Range.Start
        
        eq_range = self.doc.Range(eq_start, eq_end)
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
        
        pos_after_eq = selection.Range.Start
        
        # Paso 3: Insertar segundo heading INMEDIATAMENTE
        selection.TypeText("H4: Vertical_UNICO_002")
        selection.Range.Style = -4
        selection.TypeParagraph()
        selection.Style = -1
        
        pos_after_h2 = selection.Range.Start
        
        end_pos = selection.Range.Start
        
        # Análisis: buscar los textos únicos
        doc_range = self.doc.Range(start_pos, end_pos)
        full_text = doc_range.Text
        
        found_h1 = "Horizontal_UNICO_001" in full_text
        found_h2 = "Vertical_UNICO_002" in full_text
        
        selection.TypeParagraph()
        selection.TypeText(f">>> H1 encontrado: {found_h1}")
        selection.TypeParagraph()
        selection.TypeText(f">>> H2 encontrado: {found_h2}")
        selection.TypeParagraph()
        
        # Listar todos los párrafos
        selection.TypeText(">>> Lista de párrafos:")
        selection.TypeParagraph()
        for i, para in enumerate(doc_range.Paragraphs, 1):
            text = para.Range.Text.strip()[:40]
            style = str(para.Style.NameLocal)
            selection.TypeText(f"    {i}: [{style}] {text}")
            selection.TypeParagraph()
        
        print(f"\nTEST 06 - H1 found: {found_h1}, H2 found: {found_h2}")
        
        self.assertTrue(found_h1 and found_h2,
            f"H1={found_h1}, H2={found_h2}. El heading posterior se perdió.")

    # =========================================================================
    # TEST 7: Secuencia H→Eq→H→Eq con diagnóstico
    # =========================================================================
    def test_07_sequence_h_eq_h_eq_diagnosis(self):
        """
        Probar la secuencia exacta que falla: H → Eq → H → Eq
        Con identificadores únicos para rastrear qué se pierde.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 07: Secuencia H→Eq→H→Eq diagnóstico")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Secuencia exacta del snippet problemático
        headings_to_insert = [
            ("HEADING_A_111", 4),
            ("HEADING_B_222", 4),
            ("HEADING_C_333", 4),
            ("HEADING_D_444", 3),
        ]
        
        equations_to_insert = [
            "S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4",
            "S_a(T_V)=(I⋅S_(aV)(T_V))/(R_V)⋅((0.05)/(ξ_V))^0.4",
            "Q_(0,min)=0.25(I⋅A_r⋅S)/(g)P",
        ]
        
        # Insertar: H_A → Eq_1 → H_B → Eq_2 → H_C → Eq_3 → H_D
        for i in range(3):
            # Heading
            h_text, h_level = headings_to_insert[i]
            self._insert_heading(h_text, level=h_level)
            print(f"  Insertado: {h_text}")
            
            # Ecuación
            self._insert_display_equation_with_buffer(equations_to_insert[i])
            print(f"  Insertada ecuación {i+1}")
        
        # Último heading
        h_text, h_level = headings_to_insert[3]
        self._insert_heading(h_text, level=h_level)
        print(f"  Insertado: {h_text}")
        
        end_pos = selection.Range.Start
        
        # Análisis
        doc_range = self.doc.Range(start_pos, end_pos)
        full_text = doc_range.Text
        
        # Buscar cada heading
        found_headings = []
        missing_headings = []
        for h_text, _ in headings_to_insert:
            if h_text in full_text:
                found_headings.append(h_text)
            else:
                missing_headings.append(h_text)
        
        selection.TypeParagraph()
        selection.TypeText(f">>> Headings encontrados: {len(found_headings)}/4")
        selection.TypeParagraph()
        
        if missing_headings:
            selection.TypeText(f">>> PERDIDOS: {', '.join(missing_headings)}")
            selection.TypeParagraph()
        
        # Listar todos los párrafos para diagnóstico
        selection.TypeText(">>> Contenido del rango:")
        selection.TypeParagraph()
        for i, para in enumerate(doc_range.Paragraphs, 1):
            text = para.Range.Text.strip()[:50]
            style = str(para.Style.NameLocal)
            # Solo mostrar párrafos con contenido
            if text and text != "\r":
                selection.TypeText(f"    {i}: [{style}] {text}")
                selection.TypeParagraph()
        
        print(f"\nTEST 07 - Encontrados: {found_headings}")
        print(f"TEST 07 - Perdidos: {missing_headings}")
        
        self.assertEqual(len(found_headings), 4,
            f"Faltan headings: {missing_headings}")

    # =========================================================================
    # TEST 8: Análisis completo de párrafos del snippet sísmica
    # =========================================================================
    def test_08_full_paragraph_analysis(self):
        """
        Análisis completo de todos los párrafos generados por el snippet.
        Este test muestra exactamente qué se genera para diagnóstico.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 08: Análisis completo de párrafos")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # Simular solo una parte del snippet para análisis detallado
        start_pos = selection.Range.Start
        
        self._insert_heading("Estados de Carga", level=2)
        self._insert_text("Descripción de cargas:")
        
        # Insertar solo 2 bloques: heading + ecuación
        self._insert_heading("Horizontal", level=4)
        self._insert_display_equation_with_buffer("S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4")
        
        self._insert_heading("Vertical", level=4)
        self._insert_display_equation_with_buffer("S_a(T_V)=(I⋅S_(aV)(T_V))/(R_V)⋅((0.05)/(ξ_V))^0.4")
        
        self._insert_heading("Siguiente Sección", level=2)
        
        end_pos = selection.Range.Start
        
        # Análisis detallado
        print("\n>>> ANÁLISIS DE PÁRRAFOS:")
        paragraphs = self._analyze_paragraph_content(start_pos, end_pos)
        
        # Conteos
        empty_count = sum(1 for p in paragraphs if p["type"] == "VACÍO")
        eq_count = sum(1 for p in paragraphs if p["type"] == "ECUACIÓN")
        heading_count = sum(1 for p in paragraphs if p["type"] == "HEADING")
        text_count = sum(1 for p in paragraphs if p["type"] == "TEXTO")
        
        selection.TypeParagraph()
        selection.TypeText(f">>> RESUMEN: Total={len(paragraphs)}, Vacíos={empty_count}, Ecuaciones={eq_count}, Headings={heading_count}, Texto={text_count}")
        selection.TypeParagraph()
        
        print(f"\nRESUMEN:")
        print(f"  Total párrafos: {len(paragraphs)}")
        print(f"  Vacíos: {empty_count}")
        print(f"  Ecuaciones: {eq_count}")
        print(f"  Headings: {heading_count}")
        print(f"  Texto: {text_count}")
        
        # Calcular el "exceso" de párrafos
        # Sin buffer, esperaríamos: 5 headings + 1 texto + 2 ecuaciones = 8 párrafos
        expected_min = heading_count + text_count + eq_count
        excess = len(paragraphs) - expected_min
        
        print(f"  Exceso (párrafos extra): {excess}")
        
        if empty_count > 0:
            print(f"\n  ⚠️  HAY {empty_count} PÁRRAFOS VACÍOS")

    # =========================================================================
    # TEST 9: Usar WordService real para insertar snippet
    # =========================================================================
    def test_09_wordservice_real_snippet(self):
        """
        Usar WordService y TemplateEngine reales para insertar el snippet.
        Esto replica exactamente el flujo del usuario.
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        selection.TypeText("TEST 09: WordService real - Snippet Sísmica")
        selection.TypeParagraph()
        selection.TypeText("=" * 50)
        selection.TypeParagraph()
        
        # Importar WordService
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from Reportes.word_service import WordService
            from Reportes.template_engine import TemplateEngine
        except Exception as e:
            print(f"Error importando: {e}")
            self.skipTest(f"No se pudo importar WordService: {e}")
        
        # Crear WordService y conectar al documento existente
        ws = WordService()
        ws.word_app = self.word_app  # Inyectar nuestra instancia
        
        start_pos = selection.Range.Start
        
        # Usar métodos reales de WordService
        ws.insert_heading("Estados de Carga (WordService)", level=2)
        ws.insert_text_at_cursor("Descripción usando WordService:", "Normal")
        
        # Insertar snippet parcial usando process_blocks del TemplateEngine
        te = TemplateEngine()
        te.word_service = ws  # Inyectar nuestro WordService
        
        # Usar el snippet sísmica
        if self.sismica_snippet:
            # Solo insertar los primeros 5 bloques del snippet
            blocks = self.sismica_snippet["content"][:5]
            te.process_blocks(blocks)
        
        ws.insert_heading("Siguiente Sección (WordService)", level=2)
        
        end_pos = selection.Range.Start
        
        # Análisis
        print("\n>>> ANÁLISIS CON WORDSERVICE REAL:")
        paragraphs = self._analyze_paragraph_content(start_pos, end_pos)
        
        empty_count = sum(1 for p in paragraphs if p["type"] == "VACÍO")
        
        selection.TypeParagraph()
        selection.TypeText(f">>> Total={len(paragraphs)}, Vacíos={empty_count}")
        selection.TypeParagraph()
        
        print(f"\nRESUMEN WordService:")
        print(f"  Total párrafos: {len(paragraphs)}")
        print(f"  Vacíos: {empty_count}")
        
        if empty_count > 0:
            print(f"\n  ⚠️  HAY {empty_count} PÁRRAFOS VACÍOS CON WORDSERVICE REAL")

    # =========================================================================
    # TEST 10: Flujo EXACTO del usuario
    # =========================================================================
    def test_10_exact_user_workflow(self):
        """
        Replica EXACTAMENTE el flujo del usuario:
        1. Template genera Estados de Carga (heading)
        2. Usuario agrega párrafo manualmente
        3. Usuario inserta snippet sísmica COMPLETO
        4. Template continúa con Combinaciones de Carga
        """
        selection = self.word_app.Selection
        
        selection.TypeParagraph()
        selection.TypeText("=" * 60)
        selection.TypeParagraph()
        selection.TypeText("TEST 10: FLUJO EXACTO DEL USUARIO")
        selection.TypeParagraph()
        selection.TypeText("=" * 60)
        selection.TypeParagraph()
        
        # Importar servicios
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from Reportes.word_service import WordService
            from Reportes.template_engine import TemplateEngine
        except Exception as e:
            self.skipTest(f"No se pudo importar: {e}")
        
        ws = WordService()
        ws.word_app = self.word_app
        
        te = TemplateEngine()
        te.word_service = ws
        
        start_pos = selection.Range.Start
        
        # --- PASO 1: Template inserta heading "Estados de Carga" ---
        ws.insert_heading("Estados de Carga", level=2)
        
        # --- PASO 2: Usuario agrega párrafo manualmente ---
        ws.insert_text_at_cursor("A continuación se describen los estados de carga considerados en el análisis:", "Normal")
        
        # --- PASO 3: Usuario inserta snippet sísmica COMPLETO ---
        if self.sismica_snippet:
            print("\n>>> Insertando snippet sísmica completo...")
            te.process_blocks(self.sismica_snippet["content"])
        
        # --- PASO 4: Template continúa con siguiente sección ---
        ws.insert_heading("Combinaciones de Carga", level=2)
        ws.insert_text_at_cursor("Las combinaciones de carga se definen según la normativa vigente.", "Normal")
        
        end_pos = selection.Range.Start
        
        # Análisis completo
        print("\n>>> ANÁLISIS FLUJO COMPLETO:")
        paragraphs = self._analyze_paragraph_content(start_pos, end_pos, max_show=50)
        
        # Conteos
        empty_count = sum(1 for p in paragraphs if p["type"] == "VACÍO")
        eq_count = sum(1 for p in paragraphs if p["type"] == "ECUACIÓN")
        heading_count = sum(1 for p in paragraphs if p["type"] == "HEADING")
        text_count = sum(1 for p in paragraphs if p["type"] == "TEXTO")
        
        selection.TypeParagraph()
        selection.TypeText(f">>> RESUMEN FINAL:")
        selection.TypeParagraph()
        selection.TypeText(f"    Total: {len(paragraphs)}, Vacíos: {empty_count}, Ecuaciones: {eq_count}, Headings: {heading_count}, Texto: {text_count}")
        selection.TypeParagraph()
        
        print(f"\n{'='*50}")
        print(f"RESUMEN FLUJO USUARIO:")
        print(f"  Total párrafos: {len(paragraphs)}")
        print(f"  Vacíos: {empty_count}")
        print(f"  Ecuaciones: {eq_count}")
        print(f"  Headings: {heading_count}")
        print(f"  Texto: {text_count}")
        print(f"{'='*50}")
        
        if empty_count > 0:
            print(f"\n⚠️  PROBLEMA: HAY {empty_count} PÁRRAFOS VACÍOS")
            # Listar los vacíos
            for p in paragraphs:
                if p["type"] == "VACÍO":
                    print(f"    Párrafo {p['num']}: {p['text']}")


class TestBufferOptimization(unittest.TestCase):
    """
    Tests para explorar optimizaciones del buffer.
    """
    
    @classmethod
    def setUpClass(cls):
        # Reusar Word de la clase anterior, o crear nuevo si no existe
        if TestWorkflowTemplateSnippet.word_app is None:
            cls.word_app = get_word_app()
            if cls.word_app:
                cls.doc = cls.word_app.Documents.Add()
        else:
            cls.word_app = TestWorkflowTemplateSnippet.word_app
            cls.doc = TestWorkflowTemplateSnippet.doc
        
        if cls.word_app:
            selection = cls.word_app.Selection
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
            selection.TypeText("=== TESTS: Optimización del Buffer ===")
            selection.TypeParagraph()
            selection.TypeText("=" * 60)
            selection.TypeParagraph()
    
    def test_buffer_with_2_paragraphs(self):
        """Probar con solo 2 párrafos de buffer."""
        selection = self.word_app.Selection
        
        selection.TypeText(">>> Buffer de 2 párrafos:")
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Heading antes
        selection.TypeText("Título Antes")
        selection.Range.Style = -2  # Heading 1
        selection.TypeParagraph()
        selection.Style = -1
        
        # Ecuación con buffer de 2
        selection.Collapse(0)
        for _ in range(2):  # Solo 2 párrafos
            selection.TypeParagraph()
        selection.MoveUp(4, 2, 0)  # Retroceder 2
        
        eq_start = selection.Range.Start
        selection.TypeText("E = mc²")
        eq_end = selection.Range.Start
        
        eq_range = self.doc.Range(eq_start, eq_end)
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
        
        # Heading después
        selection.TypeText("Título Después")
        selection.Range.Style = -2
        selection.TypeParagraph()
        selection.Style = -1
        
        end_pos = selection.Range.Start
        
        # Contar headings
        doc_range = self.doc.Range(start_pos, end_pos)
        heading_count = 0
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                heading_count += 1
        
        selection.TypeText(f"    Headings: {heading_count}/2")
        selection.TypeParagraph()
        
        print(f"\nBuffer 2: Headings {heading_count}/2")

    def test_buffer_with_1_paragraph(self):
        """Probar con solo 1 párrafo de buffer."""
        selection = self.word_app.Selection
        
        selection.TypeText(">>> Buffer de 1 párrafo:")
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Heading antes
        selection.TypeText("Título Antes")
        selection.Range.Style = -2
        selection.TypeParagraph()
        selection.Style = -1
        
        # Ecuación con buffer de 1
        selection.Collapse(0)
        selection.TypeParagraph()  # Solo 1 párrafo
        selection.MoveUp(4, 1, 0)  # Retroceder 1
        
        eq_start = selection.Range.Start
        selection.TypeText("a² + b² = c²")
        eq_end = selection.Range.Start
        
        eq_range = self.doc.Range(eq_start, eq_end)
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
        
        # Heading después
        selection.TypeText("Título Después")
        selection.Range.Style = -2
        selection.TypeParagraph()
        selection.Style = -1
        
        end_pos = selection.Range.Start
        
        # Contar headings
        doc_range = self.doc.Range(start_pos, end_pos)
        heading_count = 0
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                heading_count += 1
        
        selection.TypeText(f"    Headings: {heading_count}/2")
        selection.TypeParagraph()
        
        print(f"Buffer 1: Headings {heading_count}/2")

    def test_no_buffer_with_justification_fix(self):
        """
        Probar SIN buffer pero CON el fix de Justification=7.
        Este podría ser el fix definitivo si funciona para display.
        """
        selection = self.word_app.Selection
        
        selection.TypeText(">>> Sin buffer + Justification=7:")
        selection.TypeParagraph()
        
        start_pos = selection.Range.Start
        
        # Heading antes
        selection.TypeText("Título Antes")
        selection.Range.Style = -2
        selection.TypeParagraph()
        selection.Style = -1
        
        # Ecuación SIN buffer pero CON Justification=7
        selection.Collapse(0)
        
        eq_start = selection.Range.Start
        selection.TypeText("∫_0^1 x² dx")
        eq_end = selection.Range.Start
        
        eq_range = self.doc.Range(eq_start, eq_end)
        omaths = eq_range.OMaths
        omaths.Add(eq_range)
        omath = omaths(omaths.Count)
        
        try:
            # Aplicar Justification ANTES de BuildUp
            omath.Justification = 7
            omath.BuildUp()
            # Luego cambiar a Display
            omath.Range.OMaths(1).Type = 0
            omath.Range.OMaths(1).Justification = 1  # Centered
        except Exception as e:
            selection.TypeText(f"  [Error: {e}]")
            selection.TypeParagraph()
        
        selection.SetRange(omath.Range.End, omath.Range.End)
        selection.TypeParagraph()
        selection.Style = -1
        
        # Heading después
        selection.TypeText("Título Después")
        selection.Range.Style = -2
        selection.TypeParagraph()
        selection.Style = -1
        
        end_pos = selection.Range.Start
        
        # Contar headings y párrafos vacíos
        doc_range = self.doc.Range(start_pos, end_pos)
        heading_count = 0
        empty_count = 0
        for para in doc_range.Paragraphs:
            style = str(para.Style.NameLocal).lower()
            if "heading" in style or "título" in style:
                heading_count += 1
            if para.Range.Text.strip() in ("", "\r"):
                empty_count += 1
        
        selection.TypeText(f"    Headings: {heading_count}/2, Vacíos: {empty_count}")
        selection.TypeParagraph()
        
        print(f"Sin buffer + J=7: Headings {heading_count}/2, Vacíos: {empty_count}")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ejecutar en orden
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowTemplateSnippet))
    suite.addTests(loader.loadTestsFromTestCase(TestBufferOptimization))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
