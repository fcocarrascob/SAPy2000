import os
import json
import glob
import logging
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class SnippetManager:
    """
    Gestiona la carga, edición y guardado de librerías de fragmentos (Snippets).
    """
    def __init__(self, library_path=None):
        if library_path is None:
            # Por defecto: Reportes/library
            self.library_path = os.path.join(os.path.dirname(__file__), "library")
        else:
            self.library_path = library_path
            
        self.categories = {} # { "NombreCategoria": [snippet1, snippet2] }
        self._category_files = {} # { "NombreCategoria": "ruta/archivo.json" }

    def load_library(self):
        """Escanea la carpeta library y carga los JSONs."""
        self.categories = {}
        self._category_files = {}
        
        if not os.path.exists(self.library_path):
            os.makedirs(self.library_path)
            return

        files = glob.glob(os.path.join(self.library_path, "*.json"))
        
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    
                    cat_name = data.get("category", "Sin Categoría")
                    snippets = data.get("snippets", [])
                    
                    if cat_name not in self.categories:
                        self.categories[cat_name] = []
                        self._category_files[cat_name] = f
                    
                    self.categories[cat_name].extend(snippets)
                    
            except Exception as e:
                logger.error(f"Error cargando librería {f}: {e}")

    def get_categories(self):
        return list(self.categories.keys())

    def get_snippets_in_category(self, category):
        return self.categories.get(category, [])

    def get_snippet_by_id(self, snippet_id):
        """Busca un snippet por ID en todas las categorias."""
        for cat_list in self.categories.values():
            for s in cat_list:
                if s.get("id") == snippet_id:
                    return s
        return None

    def get_category_file(self, category):
        """Retorna la ruta del archivo JSON para una categoría."""
        return self._category_files.get(category)

    def save_snippet(self, category, snippet_data, original_id=None):
        """
        Guarda o actualiza un snippet en el JSON de la categoría.
        Si original_id es None, agrega un nuevo snippet.
        Si original_id existe, reemplaza ese snippet.
        """
        file_path = self._category_files.get(category)
        if not file_path:
            logger.error(f"Categoría '{category}' no tiene archivo asociado.")
            return False
        
        try:
            # Crear backup antes de modificar
            self._create_backup(file_path)
            
            # Cargar archivo actual
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            snippets = data.get("snippets", [])
            
            if original_id:
                # Actualizar snippet existente
                for i, s in enumerate(snippets):
                    if s.get("id") == original_id:
                        snippets[i] = snippet_data
                        break
                else:
                    # No se encontró, agregar como nuevo
                    snippets.append(snippet_data)
            else:
                # Agregar nuevo snippet
                snippets.append(snippet_data)
            
            data["snippets"] = snippets
            
            # Guardar
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Snippet '{snippet_data.get('id')}' guardado en {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando snippet: {e}")
            return False

    def delete_snippet(self, category, snippet_id):
        """Elimina un snippet por ID de la categoría especificada."""
        file_path = self._category_files.get(category)
        if not file_path:
            logger.error(f"Categoría '{category}' no tiene archivo asociado.")
            return False
        
        try:
            self._create_backup(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            snippets = data.get("snippets", [])
            initial_count = len(snippets)
            
            # Filtrar para eliminar el ID
            filtered_snippets = [s for s in snippets if s.get("id") != snippet_id]
            
            if len(filtered_snippets) == initial_count:
                logger.warning(f"No se encontró el snippet '{snippet_id}' para eliminar.")
                return False
            
            data["snippets"] = filtered_snippets
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Snippet '{snippet_id}' eliminado correctamente.")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando snippet: {e}")
            return False

    def _create_backup(self, file_path):
        """Crea una copia de seguridad del archivo antes de modificarlo."""
        backup_dir = os.path.join(self.library_path, ".backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.basename(file_path)
        backup_name = f"{basename}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backup creado: {backup_path}")
