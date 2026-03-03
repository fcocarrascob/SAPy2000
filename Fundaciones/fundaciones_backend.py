import comtypes.client
import sys

class FundacionesBackend:
    """
    Backend para análisis y diseño de fundaciones.
    
    Responsabilidades:
    - Leer y procesar datos de fundaciones desde SAP2000
    - Calcular reacciones y esfuerzos en fundaciones
    - Generar información para diseño de fundaciones
    """
    
    def __init__(self, sap_model=None):
        """
        Inicializa el backend de fundaciones.
        
        Args:
            sap_model: Objeto SapModel opcional ya conectado.
        """
        self.SapModel = sap_model
        # Constantes para tipos de material (según API SAP2000)
        self.eMatType_Concrete = 2
        self.eMatType_Rebar = 6
    
    def get_base_joints(self):
        """
        Obtiene los joints en la base del modelo (z mínimo).
        
        Returns:
            list: Lista de nombres de joints en la base
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Obtener todos los joints
            ret = self.SapModel.PointObj.GetNameList()
            if ret[-1] != 0:
                print("Error obteniendo lista de joints")
                return []
            
            count = ret[0]
            names = ret[1] if count > 0 else []
            
            # Por ahora retornamos todos los joints
            # En futuras versiones se filtrará por z mínimo
            return list(names) if names else []
            
        except Exception as e:
            print(f"Error en get_base_joints: {e}")
            return []
    
    def get_concrete_materials(self):
        """
        Obtiene la lista de materiales de tipo Concrete del modelo.
        
        Returns:
            list: Lista de nombres de materiales de hormigón/concreto
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Obtener todos los materiales
            ret = self.SapModel.PropMaterial.GetNameList()
            if ret[-1] != 0:
                print("Error obteniendo lista de materiales")
                return []
            
            count = ret[0]
            all_materials = ret[1] if count > 0 else []
            
            concrete_materials = []
            
            # Filtrar solo materiales de tipo Concrete
            for mat_name in all_materials:
                try:
                    # GetMaterial retorna (MatType, Color, Notes, GUID, RetCode)
                    ret_mat = self.SapModel.PropMaterial.GetMaterial(mat_name)
                    if ret_mat[-1] == 0:  # RetCode exitoso
                        mat_type = ret_mat[0]  # MatType es el primer elemento
                        if mat_type == self.eMatType_Concrete:
                            concrete_materials.append(mat_name)
                except Exception as e:
                    print(f"Error verificando material {mat_name}: {e}")
                    continue
            
            return concrete_materials
            
        except Exception as e:
            print(f"Error en get_concrete_materials: {e}")
            return []
    
    def get_rebar_materials(self):
        """
        Obtiene la lista de materiales de tipo Rebar del modelo.
        
        Returns:
            list: Lista de nombres de materiales de acero de refuerzo
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Obtener todos los materiales
            ret = self.SapModel.PropMaterial.GetNameList()
            if ret[-1] != 0:
                print("Error obteniendo lista de materiales")
                return []
            
            count = ret[0]
            all_materials = ret[1] if count > 0 else []
            
            rebar_materials = []
            
            # Filtrar solo materiales de tipo Rebar
            for mat_name in all_materials:
                try:
                    # GetMaterial retorna (MatType, Color, Notes, GUID, RetCode)
                    ret_mat = self.SapModel.PropMaterial.GetMaterial(mat_name)
                    if ret_mat[-1] == 0:  # RetCode exitoso
                        mat_type = ret_mat[0]  # MatType es el primer elemento
                        if mat_type == self.eMatType_Rebar:
                            rebar_materials.append(mat_name)
                except Exception as e:
                    print(f"Error verificando material {mat_name}: {e}")
                    continue
            
            return rebar_materials
            
        except Exception as e:
            print(f"Error en get_rebar_materials: {e}")
            return []
    
    def get_rebar_sizes(self):
        """
        Obtiene la lista de tamaños de barras (rebar) definidos en el modelo.
        
        Returns:
            list: Lista de nombres/tamaños de barras disponibles
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Obtener todos los rebars definidos
            ret = self.SapModel.PropRebar.GetNameList()
            if ret[-1] != 0:
                print("Error obteniendo lista de rebars")
                return []
            
            count = ret[0]
            rebar_names = ret[1] if count > 0 else []
            
            # Retornar la lista de nombres de rebar
            return list(rebar_names) if rebar_names else []
            
        except Exception as e:
            print(f"Error en get_rebar_sizes: {e}")
            return []
    
    def create_rectangular_pedestal_section(self, section_name, concrete_mat, rebar_mat,
                                           width, height, corner_bar_size, edge_bar_size,
                                           edge_spacing, cover):
        """
        Crea una sección rectangular de concreto con refuerzo usando Section Designer.
        
        Args:
            section_name (str): Nombre de la sección a crear
            concrete_mat (str): Material de concreto
            rebar_mat (str): Material de acero de refuerzo
            width (float): Ancho de la sección (mm)
            height (float): Alto de la sección (mm)
            corner_bar_size (str): Tamaño de barras en esquinas (ej: "16mm", "#8")
            edge_bar_size (str): Tamaño de barras en bordes (ej: "12mm", "#6")
            edge_spacing (float): Espaciamiento centro a centro en bordes (mm)
            cover (float): Recubrimiento de concreto (mm)
            
        Returns:
            bool: True si se creó exitosamente, False en caso contrario
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return False
        
        try:
            # 1. Inicializar sección de Section Designer
            ret = self.SapModel.PropFrame.SetSDSection(section_name, concrete_mat)
            if ret != 0:
                print(f"Error al inicializar Section Designer para {section_name}")
                return False
            
            print(f"✓ Sección {section_name} inicializada")
            
            # 2. Agregar rectángulo sólido de concreto CON refuerzo habilitado
            shape_name = "ConcreteCore"
            ret = self.SapModel.PropFrame.SDShape.SetSolidRect(
                section_name,      # Name
                shape_name,        # ShapeName
                concrete_mat,      # MatProp
                "Default",         # SSOverwrite
                0,                 # XCenter
                0,                 # YCenter
                height,            # h
                width,             # w
                0,                 # Rotation
                -1,                # Color (auto)
                True,              # Reinf - Habilita refuerzo
                rebar_mat          # MatRebar
            )
            
            # SetSolidRect retorna (ShapeName, RetCode) porque ShapeName es ByRef
            if ret[-1] != 0:
                print(f"Error al agregar rectángulo sólido")
                return False
            
            print(f"✓ Rectángulo sólido creado: {width}x{height} mm")
            
            # 3. Especificar barras en las 4 esquinas
            ret = self.SapModel.PropFrame.SDShape.SetReinfCorner(
                section_name,      # Name
                shape_name,        # ShapeName
                1,                 # PointNum (ignorado con All=True)
                corner_bar_size,   # RebarSize
                True               # All - Aplica a todas las esquinas
            )
            
            # SetReinfCorner retorna (ShapeName, RetCode) porque ShapeName es ByRef
            if ret[-1] != 0:
                print(f"Error al agregar refuerzo en esquinas")
                return False
            
            print(f"✓ Barras en esquinas: {corner_bar_size}")
            
            # 4. Especificar refuerzo distribuido en los 4 bordes
            ret = self.SapModel.PropFrame.SDShape.SetReinfEdge(
                section_name,      # Name
                shape_name,        # ShapeName
                1,                 # EdgeNum (ignorado con All=True)
                edge_bar_size,     # RebarSize
                edge_spacing,      # Spacing
                cover,             # Cover
                True               # All - Aplica a todos los bordes
            )
            
            # SetReinfEdge retorna (ShapeName, RetCode) porque ShapeName es ByRef
            if ret[-1] != 0:
                print(f"Error al agregar refuerzo en bordes")
                return False
            
            print(f"✓ Barras en bordes: {edge_bar_size} @ {edge_spacing} mm, rec={cover} mm")
            print(f"✓ Sección {section_name} creada exitosamente")
            
            return True
            
        except Exception as e:
            print(f"Error en create_rectangular_pedestal_section: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_joint_reactions(self, load_case_name):
        """
        Obtiene las reacciones en los joints para un caso de carga.
        
        Args:
            load_case_name (str): Nombre del caso de carga o combinación
            
        Returns:
            dict: Diccionario con reacciones por joint
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return {}
        
        # Placeholder para futuras implementaciones
        print(f"Consultando reacciones para: {load_case_name}")
        return {}
    
    def calculate_footing_design(self, joint_name, reactions):
        """
        Calcula el diseño preliminar de una zapata.
        
        Args:
            joint_name (str): Nombre del joint
            reactions (dict): Diccionario con reacciones (Fx, Fy, Fz, Mx, My, Mz)
            
        Returns:
            dict: Dimensiones y características de la zapata
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return {}
        
        # Placeholder para futuras implementaciones
        print(f"Calculando diseño de zapata para joint: {joint_name}")
        return {}


# Test standalone
if __name__ == "__main__":
    print("=== Test Fundaciones Backend ===")
    
    try:
        # Intentar conectar a instancia activa de SAP2000
        helper = comtypes.client.CreateObject('SAP2000v1.Helper')
        helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
        
        try:
            SapObject = helper.GetObject("CSI.SAP2000.API.SapObject")
            print("✓ Conectado a instancia activa de SAP2000")
        except:
            print("✗ No se encontró instancia activa de SAP2000")
            SapObject = None
        
        if SapObject:
            SapModel = SapObject.SapModel
            
            # Crear backend
            backend = FundacionesBackend(SapModel)
            
            # Test: obtener joints
            print("\nObteniendo joints...")
            joints = backend.get_base_joints()
            print(f"Total de joints encontrados: {len(joints)}")
            if joints:
                print(f"Primeros 5 joints: {joints[:5]}")
        else:
            print("\nCreando backend sin conexión (modo prueba)...")
            backend = FundacionesBackend()
            print("Backend creado (sin modelo activo)")
            
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
