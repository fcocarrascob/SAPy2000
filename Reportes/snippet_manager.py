import os
import json
import glob
import logging

logger = logging.getLogger(__name__)

class SnippetManager:
    """
    Gestiona la carga y organización de librerías de fragmentos (Snippets).
    """
    def __init__(self, library_path=None):
        if library_path is None:
            # Por defecto: Reportes/library
            self.library_path = os.path.join(os.path.dirname(__file__), "library")
        else:
            self.library_path = library_path
            
        self.categories = {} # { "NombreCategoria": [snippet1, snippet2] }

    def load_library(self):
        """Escanea la carpeta library y carga los JSONs."""
        self.categories = {}
        
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
