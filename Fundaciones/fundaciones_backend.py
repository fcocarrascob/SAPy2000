import comtypes.client
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code, get_materials_by_type

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
        self.logger = AppLogger()
    
    def get_base_joints(self):
        """
        Obtiene los joints en la base del modelo (z mínimo).
        
        Returns:
            list: Lista de nombres de joints en la base
        """
        if not self.SapModel:
            self.logger.warning("No hay conexión con SAP2000")
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
            return get_materials_by_type(self.SapModel, self.eMatType_Concrete)
            
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
            self.logger.warning("No hay conexión con SAP2000")
            return []

        try:
            return get_materials_by_type(self.SapModel, self.eMatType_Rebar)
        except Exception as e:
            self.logger.error(f"Error en get_rebar_materials: {e}")
            return []
        
    
    def get_rebar_sizes(self):
        """
        Obtiene la lista de tamaños de barras (rebar) definidos en el modelo.
        
        Returns:
            list: Lista de nombres/tamaños de barras disponibles
        """
        if not self.SapModel:
            self.logger.warning("No hay conexión con SAP2000")
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
    
    def get_concrete_frame_sections(self):
        """
        Obtiene la lista de secciones de Frame (columnas/vigas) de hormigón del modelo.
        
        Returns:
            list: Lista de nombres de secciones de Frame de hormigón
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Obtener todas las secciones de Frame
            ret = self.SapModel.PropFrame.GetNameList()
            if not check_ret_code(ret):
                self.logger.error("Error obteniendo lista de secciones de Frame")
                return []
            
            count = ret[0]
            all_sections = ret[1] if count > 0 else []
            
            concrete_sections = []
            
            # Filtrar solo secciones con material de hormigón
            for sec_name in all_sections:
                try:
                    # Obtener propiedades de la sección para verificar material
                    # PropFrame.GetMaterial retorna (MatProp, RetCode)
                    ret_mat = self.SapModel.PropFrame.GetMaterial(sec_name)
                    if check_ret_code(ret_mat):
                        mat_name = ret_mat[0]
                        ret_mat_type = self.SapModel.PropMaterial.GetMaterial(mat_name)
                        if check_ret_code(ret_mat_type):
                            mat_type = ret_mat_type[0]
                            if mat_type == self.eMatType_Concrete:
                                concrete_sections.append(sec_name)
                except Exception as e:
                    print(f"Error verificando sección {sec_name}: {e}")
                    continue
            
            return concrete_sections
            
        except Exception as e:
            print(f"Error en get_concrete_frame_sections: {e}")
            return []
    
    def get_shell_sections(self):
        """
        Obtiene la lista de secciones de Shell/Area del modelo.
        
        Returns:
            list: Lista de nombres de secciones de Shell
        """
        if not self.SapModel:
            self.logger.warning("No hay conexión con SAP2000")
            return []
        
        try:
            # Obtener todas las secciones de Area
            ret = self.SapModel.PropArea.GetNameList()
            if not check_ret_code(ret):
                self.logger.error("Error obteniendo lista de secciones de Area")
                return []
            
            count = ret[0]
            all_sections = ret[1] if count > 0 else []
            
            # Retornar todas las secciones de Shell/Area
            return list(all_sections) if all_sections else []
            
        except Exception as e:
            print(f"Error en get_shell_sections: {e}")
            return []
    
    def get_selected_point_coords(self):
        """
        Retorna las coordenadas (x, y, z) del primer punto seleccionado.
        Retorna None si no hay conexión o no hay puntos seleccionados.
        
        Returns:
            dict: Diccionario con 'name', 'x', 'y', 'z' o None si no hay selección
        """
        if not self.SapModel:
            self.logger.warning("No hay conexión con SAP2000")
            return None
        
        try:
            # 1. Obtener objetos seleccionados
            # GetSelected retorna (NumberItems, ObjectTypes, ObjectNames, RetCode)
            ret_sel = self.SapModel.SelectObj.GetSelected(0, [], [])

            if not check_ret_code(ret_sel):
                return None
            
            num_items = ret_sel[0]
            if num_items == 0:
                return None
            
            obj_types = ret_sel[1]
            obj_names = ret_sel[2]
            
            point_name = None
            
            # Buscar el primer objeto de tipo 1 (PointObject)
            for i in range(num_items):
                if int(obj_types[i]) == 1:  # 1 = PointObject
                    point_name = obj_names[i]
                    break
            
            if not point_name:
                return None
            
            # 2. Obtener coordenadas del punto
            # GetCoordCartesian retorna (x, y, z, RetCode)
            ret_coord = self.SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0, "Global")

            if check_ret_code(ret_coord):
                return {
                    "name": point_name,
                    "x": ret_coord[0],
                    "y": ret_coord[1],
                    "z": ret_coord[2]
                }
                
        except Exception as e:
            print(f"Error obteniendo coordenadas del punto seleccionado: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def get_frame_section_dimensions(self, section_name):
        """
        Obtiene las dimensiones (ancho, alto) de una sección de Frame rectangular.
        
        Args:
            section_name: Nombre de la sección de Frame
            
        Returns:
            tuple: (width, height) en mm, o None si no se puede determinar
        """
        if not self.SapModel:
            self.logger.warning("No hay conexión con SAP2000")
            return None
        
        try:
            # Guardar unidades actuales
            current_units = self.SapModel.GetPresentUnits()
            
            # Cambiar a tonf-mm-C para leer dimensiones en mm
            self.SapModel.SetPresentUnits(7)  # eUnits.tonf_mm_C
            
            # Intentar obtener propiedades de la sección
            # Para Section Designer (SD), usar GetSDSection
            # PropFrame.GetSDSection retorna (NameSD, RetCode)
            ret_sd = self.SapModel.PropFrame.GetSDSection(section_name, "")

            if check_ret_code(ret_sd) and ret_sd[0]:
                # Es una sección SD, obtener dimensiones del bounding box
                sd_name = ret_sd[0]

                # Intentamos obtener propiedades generales de la sección
                ret_props = self.SapModel.PropFrame.GetSectionProps(section_name)
                if check_ret_code(ret_props):
                    # Intentar obtener las formas SD asociadas
                    ret_shapes = self.SapModel.PropFrame.SDShape.GetAllSDShapes(sd_name, 0, [], [], [], [])

                    if check_ret_code(ret_shapes) and ret_shapes[0] > 0:
                        shape_names = ret_shapes[1]
                        shape_types = ret_shapes[2]

                        # Buscar la forma rectangular principal (tipo "Rectangular")
                        for i, shape_name in enumerate(shape_names):
                            shape_type = shape_types[i]

                            # Tipo 1 = Rectangular
                            if shape_type == 1:
                                # GetRectangle(SDName, ShapeName, NameMat, SSOverwrite, CenterX, CenterY, H, W, Rotation, Color, RetCode)
                                ret_rect = self.SapModel.PropFrame.SDShape.GetRectangle(sd_name, shape_name)

                                if check_ret_code(ret_rect):
                                    # ret_rect = (NameMat, SSOverwrite, CenterX, CenterY, H, W, Rotation, Color, RetCode)
                                    height = ret_rect[4]  # H
                                    width = ret_rect[5]   # W

                                    # Restaurar unidades
                                    self.SapModel.SetPresentUnits(current_units)

                                    return (width, height)
            
            # Si no es SD o no se pudo obtener, intentar como sección rectangular estándar
            # GetRectangle retorna (FileName, MatProp, t3, t2, Color, Notes, GUID, RetCode)
            ret_rect_std = self.SapModel.PropFrame.GetRectangle(section_name)

            if check_ret_code(ret_rect_std):
                height = ret_rect_std[2]  # t3
                width = ret_rect_std[3]   # t2
                
                # Restaurar unidades
                self.SapModel.SetPresentUnits(current_units)
                
                return (width, height)
            
            # Restaurar unidades antes de retornar None
            self.SapModel.SetPresentUnits(current_units)
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo dimensiones de sección {section_name}: {e}")
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
            return None
    
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
            # Guardar unidades actuales y cambiar a Ton_mm_C
            current_units = self.SapModel.GetPresentUnits()
            ret = self.SapModel.SetPresentUnits(11)  # Ton_mm_C = 11
            if ret != 0:
                print("⚠️ Advertencia: No se pudieron cambiar las unidades")
            else:
                print("✓ Unidades cambiadas a Ton_mm_C")
            
            # 1. Inicializar sección de Section Designer
            ret = self.SapModel.PropFrame.SetSDSection(section_name, concrete_mat)
            if ret != 0:
                print(f"Error al inicializar Section Designer para {section_name}")
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
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
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
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
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
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
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
                return False
            
            print(f"✓ Barras en bordes: {edge_bar_size} @ {edge_spacing} mm, rec={cover} mm")
            print(f"✓ Sección {section_name} creada exitosamente")
            
            # Restaurar unidades originales
            self.SapModel.SetPresentUnits(current_units)
            print(f"✓ Unidades restauradas")
            
            return True
            
        except Exception as e:
            print(f"Error en create_rectangular_pedestal_section: {e}")
            import traceback
            traceback.print_exc()
            # Intentar restaurar unidades en caso de error
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
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
    
    def create_shell_thick_sections(self, base_name, material, thickness):
        """
        Crea dos secciones Shell-Thick para losas de fundación.
        
        Args:
            base_name (str): Nombre base para las secciones (ej: "LOSA_")
            material (str): Material de concreto
            thickness (float): Espesor de la losa en mm (se usa para membrana y flexión)
            
        Returns:
            bool: True si se crearon exitosamente, False en caso contrario
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return False
        
        try:
            # Guardar unidades actuales y cambiar a Ton_mm_C
            current_units = self.SapModel.GetPresentUnits()
            ret = self.SapModel.SetPresentUnits(11)  # Ton_mm_C = 11
            if ret != 0:
                print("⚠️ Advertencia: No se pudieron cambiar las unidades")
            else:
                print("✓ Unidades cambiadas a Ton_mm_C")
            
            # Nombres de las dos secciones
            section_1 = base_name
            section_2 = base_name + "PED"
            
            # Colores en formato Windows Long (BGR)
            # RGB(200, 200, 200) → gris claro
            color_light_gray = 200 + (200 * 256) + (200 * 65536)  # 13158600
            # RGB(128, 128, 128) → gris oscuro
            color_dark_gray = 128 + (128 * 256) + (128 * 65536)   # 8421504
            
            # Parámetros comunes
            shell_type = 2  # Shell - thick
            include_drilling_dof = True
            mat_angle = 0.0
            
            # Trabajar directamente en mm (ya estamos en Ton_mm_C)
            thickness_mm = thickness
            
            print(f"Creando sección 1: {section_1}")
            # Sección 1: Gris claro
            ret = self.SapModel.PropArea.SetShell_1(
                section_1,              # Name
                shell_type,             # ShellType (2 = Shell-thick)
                include_drilling_dof,   # IncludeDrillingDOF
                material,               # MatProp
                mat_angle,              # MatAng
                thickness_mm,           # Thickness (membrana) en mm
                thickness_mm,           # Bending (flexión) en mm
                color_light_gray,       # Color
                "",                     # Notes
                ""                      # GUID
            )
            
            if ret != 0:
                print(f"Error al crear sección {section_1}")
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
                return False
            
            print(f"✓ Sección {section_1} creada (gris claro)")
            
            print(f"Creando sección 2: {section_2}")
            # Sección 2: Gris oscuro
            ret = self.SapModel.PropArea.SetShell_1(
                section_2,              # Name
                shell_type,             # ShellType (2 = Shell-thick)
                include_drilling_dof,   # IncludeDrillingDOF
                material,               # MatProp
                mat_angle,              # MatAng
                thickness_mm,           # Thickness (membrana) en mm
                thickness_mm,           # Bending (flexión) en mm
                color_dark_gray,        # Color
                "",                     # Notes
                ""                      # GUID
            )
            
            if ret != 0:
                print(f"Error al crear sección {section_2}")
                # Restaurar unidades antes de retornar
                self.SapModel.SetPresentUnits(current_units)
                return False
            
            print(f"✓ Sección {section_2} creada (gris oscuro)")
            print(f"✓ Ambas secciones Shell-Thick creadas exitosamente")
            
            # Restaurar unidades originales
            self.SapModel.SetPresentUnits(current_units)
            print(f"✓ Unidades restauradas")
            
            return True
            
        except Exception as e:
            print(f"Error en create_shell_thick_sections: {e}")
            import traceback
            traceback.print_exc()
            # Intentar restaurar unidades en caso de error
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
            return False
    
    def create_frame_element(self, x1, y1, z1, x2, y2, z2, section_name, point_name_1=None, point_name_2=None):
        """
        Crea un elemento Frame entre dos puntos.
        
        Args:
            x1, y1, z1: Coordenadas del punto inicial (en mm)
            x2, y2, z2: Coordenadas del punto final (en mm)
            section_name: Nombre de la sección del frame
            point_name_1: Nombre personalizado para el punto 1 (opcional)
            point_name_2: Nombre personalizado para el punto 2 (opcional)
            
        Returns:
            tuple: (frame_name, point1_name, point2_name) o (None, None, None) si falla
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return None, None, None
        
        try:
            # Guardar unidades actuales
            current_units = self.SapModel.GetPresentUnits()
            
            # Cambiar a tonf-mm-C
            self.SapModel.SetPresentUnits(7)  # eUnits.tonf_mm_C
            
            # Crear o verificar punto 1
            if point_name_1:
                ret = self.SapModel.PointObj.AddCartesian(x1, y1, z1, point_name_1, point_name_1)
            else:
                ret = self.SapModel.PointObj.AddCartesian(x1, y1, z1)
            
            if ret[-1] != 0:
                print(f"Error al crear punto inicial")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            pt1_name = ret[0]
            
            # Crear o verificar punto 2
            if point_name_2:
                ret = self.SapModel.PointObj.AddCartesian(x2, y2, z2, point_name_2, point_name_2)
            else:
                ret = self.SapModel.PointObj.AddCartesian(x2, y2, z2)
            
            if ret[-1] != 0:
                print(f"Error al crear punto final")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            pt2_name = ret[0]
            
            # Crear frame entre los puntos
            ret = self.SapModel.FrameObj.AddByPoint(pt1_name, pt2_name)
            
            if ret[-1] != 0:
                print(f"Error al crear frame")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            frame_name = ret[0]
            
            # Asignar sección al frame
            ret = self.SapModel.FrameObj.SetSection(frame_name, section_name)
            
            if ret != 0:
                print(f"Error al asignar sección {section_name} al frame")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            print(f"✓ Frame creado: {frame_name} desde ({x1}, {y1}, {z1}) hasta ({x2}, {y2}, {z2})")
            
            # Restaurar unidades originales
            self.SapModel.SetPresentUnits(current_units)
            
            return frame_name, pt1_name, pt2_name
            
        except Exception as e:
            print(f"Error en create_frame_element: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
            return None, None, None
    
    def create_rigid_link_property(self, prop_name="LIN_RIGIDO"):
        """
        Crea una propiedad de link rígido (todas las direcciones fixed).
        
        Args:
            prop_name: Nombre de la propiedad del link
            
        Returns:
            bool: True si se creó exitosamente, False en caso contrario
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return False
        
        try:
            # Definir la propiedad como tipo Linear
            # SetLinear(Name, DOF, Fixed, Ke, Ce, DJ, 0)
            # DOF = [U1, U2, U3, R1, R2, R3]
            # Fixed = [True/False para cada DOF]
            
            dof = [True, True, True, True, True, True]  # Activar todos los DOF
            fixed = [True, True, True, True, True, True]  # Todos fixed (rígido)
            ke = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # Rigidez (no usado cuando fixed=True)
            ce = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # Amortiguamiento
            dj = 0.0  # Factor de peso
            
            ret = self.SapModel.PropLink.SetLinear(
                prop_name,  # Name
                dof,        # DOF
                fixed,      # Fixed
                ke,         # Ke
                ce,         # Ce
                dj,         # DJ
                0           # Notes (0 significa no sobrescribir)
            )
            
            if ret != 0:
                print(f"Error al crear propiedad de link {prop_name}")
                return False
            
            print(f"✓ Propiedad de link rígido creada: {prop_name}")
            return True
            
        except Exception as e:
            print(f"Error en create_rigid_link_property: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_link_element(self, x1, y1, z1, x2, y2, z2, link_prop_name, point_name_1=None, point_name_2=None):
        """
        Crea un elemento Link entre dos puntos.
        
        Args:
            x1, y1, z1: Coordenadas del punto inicial (en mm)
            x2, y2, z2: Coordenadas del punto final (en mm)
            link_prop_name: Nombre de la propiedad del link
            point_name_1: Nombre personalizado para el punto 1 (opcional)
            point_name_2: Nombre personalizado para el punto 2 (opcional)
            
        Returns:
            tuple: (link_name, point1_name, point2_name) o (None, None, None) si falla
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return None, None, None
        
        try:
            # Guardar unidades actuales
            current_units = self.SapModel.GetPresentUnits()
            
            # Cambiar a tonf-mm-C
            self.SapModel.SetPresentUnits(7)  # eUnits.tonf_mm_C
            
            # Crear o verificar punto 1
            if point_name_1:
                ret = self.SapModel.PointObj.AddCartesian(x1, y1, z1, point_name_1, point_name_1)
            else:
                ret = self.SapModel.PointObj.AddCartesian(x1, y1, z1)
            
            if ret[-1] != 0:
                print(f"Error al crear punto inicial del link")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            pt1_name = ret[0]
            
            # Crear o verificar punto 2
            if point_name_2:
                ret = self.SapModel.PointObj.AddCartesian(x2, y2, z2, point_name_2, point_name_2)
            else:
                ret = self.SapModel.PointObj.AddCartesian(x2, y2, z2)
            
            if ret[-1] != 0:
                print(f"Error al crear punto final del link")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            pt2_name = ret[0]
            
            # Crear link entre los puntos
            ret = self.SapModel.LinkObj.AddByPoint(pt1_name, pt2_name)
            
            if ret[-1] != 0:
                print(f"Error al crear link")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            link_name = ret[0]
            
            # Asignar propiedad al link
            ret = self.SapModel.LinkObj.SetProperty(link_name, link_prop_name)
            
            if ret != 0:
                print(f"Error al asignar propiedad {link_prop_name} al link")
                self.SapModel.SetPresentUnits(current_units)
                return None, None, None
            
            print(f"✓ Link creado: {link_name} desde ({x1}, {y1}, {z1}) hasta ({x2}, {y2}, {z2})")
            
            # Restaurar unidades originales
            self.SapModel.SetPresentUnits(current_units)
            
            return link_name, pt1_name, pt2_name
            
        except Exception as e:
            print(f"Error en create_link_element: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
            return None, None, None
    
    def create_rectangular_slab_mesh(self, center_x, center_y, z, width, height, shell_section, nx=4, ny=4):
        """
        Crea una malla rectangular de áreas (losa) centrada en las coordenadas especificadas.
        
        Args:
            center_x, center_y: Coordenadas del centro de la losa (en mm)
            z: Coordenada Z de la losa (en mm)
            width: Ancho de la losa en dirección X (en mm)
            height: Alto de la losa en dirección Y (en mm)
            shell_section: Nombre de la sección de shell a asignar
            nx: Número de divisiones en X (default 4)
            ny: Número de divisiones en Y (default 4)
            
        Returns:
            list: Lista de nombres de las áreas creadas, o lista vacía si falla
        """
        if not self.SapModel:
            print("No hay conexión con SAP2000.")
            return []
        
        try:
            # Guardar unidades actuales
            current_units = self.SapModel.GetPresentUnits()
            
            # Cambiar a tonf-mm-C
            self.SapModel.SetPresentUnits(7)  # eUnits.tonf_mm_C
            
            # Calcular esquina inicial (inferior izquierda)
            start_x = center_x - width / 2.0
            start_y = center_y - height / 2.0
            start_z = z
            
            # Dimensiones de cada celda
            dx = width / nx
            dy = height / ny
            
            created_areas = []
            
            print(f"Creando malla {nx}x{ny} de losa...")
            print(f"  Centro: ({center_x}, {center_y}, {z})")
            print(f"  Dimensiones: {width} x {height} mm")
            print(f"  Celda: {dx:.2f} x {dy:.2f} mm")
            print(f"  Sección: {shell_section}")
            
            # Crear cada celda de la malla
            for i in range(nx):
                for j in range(ny):
                    # Coordenadas de las 4 esquinas (en sentido antihorario)
                    x0 = start_x + i * dx
                    y0 = start_y + j * dy
                    
                    xs = [x0, x0 + dx, x0 + dx, x0]
                    ys = [y0, y0, y0 + dy, y0 + dy]
                    zs = [start_z, start_z, start_z, start_z]
                    
                    try:
                        # AddByCoord(NumberPoints, x, y, z, Name, PropName, UserName, CSys)
                        ret = self.SapModel.AreaObj.AddByCoord(4, xs, ys, zs, "", shell_section, "", "Global")
                        
                        # Manejo robusto del retorno (Regla de Oro)
                        ret_code = -1
                        area_name = ""
                        
                        if isinstance(ret, (list, tuple)):
                            ret_code = ret[-1]
                            if len(ret) > 1:
                                area_name = str(ret[0])
                        elif isinstance(ret, int):
                            ret_code = ret
                        
                        if ret_code == 0:
                            if area_name:
                                created_areas.append(area_name)
                        else:
                            print(f"  ⚠️ Error creando área en celda ({i},{j}): Código {ret_code}")
                            
                    except Exception as e:
                        print(f"  ⚠️ Excepción en celda ({i},{j}): {e}")
            
            print(f"✓ Se crearon {len(created_areas)} áreas de losa")
            
            # Refrescar vista
            try:
                self.SapModel.View.RefreshView(0, False)
            except:
                pass
            
            # Restaurar unidades originales
            self.SapModel.SetPresentUnits(current_units)
            
            return created_areas
            
        except Exception as e:
            print(f"Error en create_rectangular_slab_mesh: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.SapModel.SetPresentUnits(current_units)
            except:
                pass
            return []


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
