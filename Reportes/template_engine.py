import json
import logging
from .word_service import WordService

logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    Motor para generar estructuras de documentos Word basadas en templates JSON.
    Totalmente desacoplado de SAP2000.
    """
    def __init__(self):
        self.word_service = WordService()

    def generate_structure(self, template_path):
        """
        Lee el JSON en `template_path` y construye el documento usando WordService.
        """
        try:
            with open(template_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo template {template_path}: {e}")
            return False

        sections = data.get("sections", [])
        if not sections:
            logger.warning("El template no tiene secciones.")
            return False

        # Iniciar Doc
        if not self.word_service.create_new_document():
            logger.error("No se pudo crear el documento Word.")
            return False

        logger.info(f"Generando template: {data.get('template_name', 'Sin Nombre')}")
        
        return self.process_blocks(sections)

    def insert_structure_at_cursor(self, template_path):
        """
        Lee el JSON en `template_path` e inserta el contenido en el cursor del documento activo.
        No crea un documento nuevo.
        """
        try:
            with open(template_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo template {template_path}: {e}")
            return False

        sections = data.get("sections", [])
        if not sections:
            logger.warning("El template no tiene secciones.")
            return False

        # Verificar conexión con doc activo
        if not self.word_service.connect():
             logger.error("No se pudo conectar con Word o no hay documento activo.")
             return False
        
        logger.info(f"Insertando template en cursor: {data.get('template_name', 'Sin Nombre')}")
        
        return self.process_blocks(sections)

    def process_blocks(self, blocks):
        """Procesa una lista de bloques (secciones/snippets) e inserta en Word."""
        try:
            for block in blocks:
                # Comprobar si Word sigue conectado (por seguridad)
                if not self.word_service.get_active_document():
                     self.word_service.connect() # Reintentar conexión simple

                sType = block.get("type")
                content = block.get("content", "")
                params = block.get("parameters", {})

                if sType == "heading":
                    level = params.get("level", 1)
                    self.word_service.insert_heading(content, level)

                elif sType == "text":
                    style = params.get("style", "Normal")
                    self.word_service.insert_text_at_cursor(content, style)
                
                elif sType == "equation":
                    self.word_service.insert_equation(content)

                elif sType == "placeholder":
                    # Texto resaltado para indicar que falta contenido
                    # Podriamos agregar un estilo simple manual simulando un resaltado
                    # Por ahora texto normal con prefijo
                    self.word_service.insert_text_at_cursor(f" >>> {content} <<< ", "Normal")
                    # TODO: Implementar resaltado (Highlight) en WordService si se desea

                elif sType == "page_break":
                    self.word_service.insert_page_break()

                elif sType == "table":
                    # Espera que content sea un dict con headers y data
                    if isinstance(content, dict):
                        headers = content.get("headers", [])
                        data = content.get("data", [])
                        self.word_service.insert_table_from_data(headers, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando bloques: {e}")
            return False

