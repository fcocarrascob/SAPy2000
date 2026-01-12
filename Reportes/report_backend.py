import logging
import comtypes
from .word_service import WordService

logger = logging.getLogger(__name__)

class ReportBackend:
    def __init__(self, sap_model):
        self.SapModel = sap_model
        self.word_service = WordService()

    def _get_table_data(self, table_name):
        """
        Obtiene datos de una tabla de SAP2000 y los formatea como
        (headers, data_rows).
        Maneja la lógica de 'comtypes' y la API de SAP2000.
        """
        if self.SapModel is None:
            return None, None

        # 0 = Main group (all)
        # Empty field keys = all fields
        try:
            # param_in, param_out patterns conform to Rule 2
            # Function signature: GetTableForDisplayArray(TableName, FieldKeyList, GroupName, TableVersion, FieldKeysIncluded, NumberRecords, TableData, RetVal)
            # But in Python comtypes we pass inputs and get tuple return.
            # Inputs: TableName (str), FieldKeys (empty list of str), Group (str)
            
            # NOTE: Empty list for FieldKeyList in comtypes can be tricky, sometimes needs specific type.
            # Usually passing [] works if defined as ByRef param in type lib, but SAP API expects Array of Strings.
            # We will pass empty tuple or list.
            
            ret = self.SapModel.DatabaseTables.GetTableForDisplayArray(table_name, [], "ALL")
            
            # Application of Rule 1 & 2:
            # Return tuple varies.
            # We expect: (TableVersion, FieldKeysIncluded, NumberRecords, TableData, RetVal) - size 5
            # Or sometimes 6.
            
            ret_code = ret[-1]
            if ret_code != 0:
                logger.error(f"Error obteniendo tabla {table_name}: Code {ret_code}")
                return None, None
            
            # Extract data based on typical structure
            # Last element is RetVal.
            # Second to last is TableData.
            # Third to last is NumberRecords.
            # Fourth to last is FieldKeysIncluded.
            
            table_data_flat = ret[-2]
            num_records = ret[-3]
            field_keys = ret[-4]
            
            # Validation
            if num_records == 0:
                return field_keys, []
            
            num_cols = len(field_keys)
            if num_cols == 0:
                return [], []
                
            # Reshape flat list to rows
            # TableData is [Row1Col1, Row1Col2, ..., Row2Col1, ...]
            rows = []
            for i in range(num_records):
                start_idx = i * num_cols
                end_idx = start_idx + num_cols
                row = table_data_flat[start_idx:end_idx]
                rows.append(row)
                
            return field_keys, rows

        except Exception as e:
            logger.error(f"Excepción obteniendo tabla {table_name}: {e}")
            return None, None

    def insert_materials_table(self):
        """Inserta tabla de propiedades materiales en Word."""
        # Table: "Material Properties 02 - Basic Mechanical Properties"
        # Or simpler: "Material Properties 01 - General"
        table_name = "Material Properties 01 - General"
        headers, data = self._get_table_data(table_name)
        
        if not headers:
            logger.warning("No se encontraron datos de materiales.")
            return False
            
        self.word_service.connect()
        self.word_service.insert_heading("Propiedades de Materiales", 2)
        self.word_service.insert_table_from_data(headers, data)
        self.word_service.insert_text_at_cursor("\n") # Space after
        return True

    def insert_load_patterns_table(self):
        """Inserta tabla de patrones de carga."""
        table_name = "Load Pattern Definitions"
        headers, data = self._get_table_data(table_name)
        
        if not headers:
            return False
            
        self.word_service.connect()
        self.word_service.insert_heading("Patrones de Carga", 2)
        self.word_service.insert_table_from_data(headers, data)
        self.word_service.insert_text_at_cursor("\n")
        return True
        
    def insert_load_combinations_table(self):
        """Inserta tabla de combinaciones de carga."""
        # "Combination Definitions" usually contains the logic
        table_name = "Combination Definitions" 
        headers, data = self._get_table_data(table_name)

        if not headers:
            return False
            
        self.word_service.connect()
        self.word_service.insert_heading("Combinaciones de Carga", 2)
        self.word_service.insert_table_from_data(headers, data)
        self.word_service.insert_text_at_cursor("\n")
        return True

    def insert_frame_sections(self):
        table_name = "Frame Section Properties 01 - General"
        headers, data = self._get_table_data(table_name)
        
        if not headers: return False
        
        self.word_service.connect()
        self.word_service.insert_heading("Secciones de Marco", 2)
        # Limitar columnas si son muchas?
        # Por ahora todo
        self.word_service.insert_table_from_data(headers, data)
        self.word_service.insert_text_at_cursor("\n")
        return True

    def create_base_report(self):
        """Genera un reporte base completo."""
        self.word_service.create_new_document()
        self.word_service.insert_heading("Memoria de Cálculo (Generada Automáticamente)", 1)
        self.word_service.insert_text_at_cursor("Este documento contiene un resumen de los parámetros del modelo.\n")
        
        self.insert_materials_table()
        self.insert_frame_sections()
        self.insert_load_patterns_table()
        self.insert_load_combinations_table()
        
        logger.info("Reporte base generado.")
