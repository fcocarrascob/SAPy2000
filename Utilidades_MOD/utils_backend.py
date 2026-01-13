import comtypes.client
import sys
import math

class SapUtils:
    def __init__(self, sap_model=None):
        """
        Inicializa la utilidad.
        
        Args:
            sap_model: Objeto SapModel opcional ya conectado.
        """
        self.SapModel = sap_model
        # Intentamos conectar al inicializar solo si no nos pasaron un modelo
        if self.SapModel is None:
            self._connect_to_sap()

    def _connect_to_sap(self):
        try:
            # Intentar conectar a una instancia activa
            # GetActiveObject puede lanzar excepción si no encuentra el objeto
            SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            self.SapModel = SapObject.SapModel
            print("Conexión exitosa a la instancia abierta de SAP2000.")
            return self.SapModel
        except Exception as e:
            print(f"Aviso: No se pudo conectar automáticamente a SAP2000: {e}")
            self.SapModel = None
            return None

    def create_mesh_by_coord(self, width, length, nx, ny, start_x=0.0, start_y=0.0, start_z=0.0, plane="XY", prop_name="Default"):
        """
        Crea una malla rectangular de áreas usando AddByCoord en el plano especificado.
        
        Args:
            width (float): Dimensión 1 (X en XY/XZ, Y en YZ).
            length (float): Dimensión 2 (Y en XY, Z en XZ/YZ).
            nx (int): Número de divisiones en Dimensión 1.
            ny (int): Número de divisiones en Dimensión 2.
            start_x, start_y, start_z (float): Coordenadas de la esquina origen.
            plane (str): Plano de dibujo ("XY", "XZ", "YZ").
            prop_name (str): Nombre de la propiedad de área a asignar.
            
        Returns:
            list: Lista de nombres de las áreas creadas.
        """
        if self.SapModel is None:
            # Intentar reconectar si se perdió
            if self._connect_to_sap() is None:
                print("No hay conexión con SAP2000.")
                return []

        created_areas = []
        
        # Asegurar tipos
        try:
            width = float(width)
            length = float(length)
            nx = int(nx)
            ny = int(ny)
            start_x = float(start_x)
            start_y = float(start_y)
            start_z = float(start_z)
        except ValueError as e:
            print(f"Error en conversión de tipos: {e}")
            return []

        d1 = width / nx
        d2 = length / ny
        
        print(f"Generando malla {nx}x{ny} en plano {plane} (d1={d1:.2f}, d2={d2:.2f})...")
        
        # Bloquear pantalla para mejorar rendimiento (opcional, pero recomendado para muchas operaciones)
        # self.SapModel.SetModelIsLocked(False) 
        
        for i in range(nx):
            for j in range(ny):
                # Coordenadas locales 2D (u, v)
                u0 = i * d1
                v0 = j * d2
                
                # 4 esquinas en local 2D (antihorario)
                us = [u0, u0 + d1, u0 + d1, u0]
                vs = [v0, v0, v0 + d2, v0 + d2]
                
                xs, ys, zs = [], [], []
                
                for k in range(4):
                    u, v = us[k], vs[k]
                    if plane.upper() == "XY":
                        xs.append(start_x + u)
                        ys.append(start_y + v)
                        zs.append(start_z)
                    elif plane.upper() == "XZ":
                        xs.append(start_x + u)
                        ys.append(start_y)
                        zs.append(start_z + v)
                    elif plane.upper() == "YZ":
                        xs.append(start_x)
                        ys.append(start_y + u)
                        zs.append(start_z + v)
                
                try:
                    # AddByCoord(NumberPoints, x, y, z, Name, PropName, UserName, CSys)
                    # En Python comtypes, los parámetros ByRef de salida se retornan en una tupla.
                    # La firma esperada retorna: [Name, RetCode] (o similar, dependiendo de la versión exacta de la API y comtypes)
                    # Nota: AddByCoord retorna 0 si es exitoso como último elemento.
                    
                    ret = self.SapModel.AreaObj.AddByCoord(4, xs, ys, zs, "", prop_name, "", "Global")
                    
                    # Manejo robusto del retorno (Regla de Oro)
                    # ret puede ser un int (solo código) o una tupla/lista
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
                        print(f"Error creando área en celda ({i},{j}): Código {ret_code}")
                        
                except Exception as e:
                    print(f"Excepción en celda ({i},{j}): {e}")
                    
        print(f"Se crearon {len(created_areas)} áreas en {plane}.")
        
        # Refrescar vista
        try:
            self.SapModel.View.RefreshView(0, False)
        except:
            pass
        
        return created_areas

    # --- Funciones Auxiliares de Geometría y Creación ---

    def create_point(self, x, y, z, name=""):
        """Crea un punto en SAP2000 y retorna su nombre."""
        try:
            # AddCartesian(x, y, z, Name, UserName, CSys, ...)
            # Retorna [Name, RetCode]
            ret = self.SapModel.PointObj.AddCartesian(x, y, z, "", name, "Global")
            if isinstance(ret, (list, tuple)) and ret[-1] == 0:
                return str(ret[0])
            elif isinstance(ret, int) and ret == 0:
                # Caso raro donde no devuelve nombre, pero asumimos éxito (no ideal)
                return name 
        except Exception as e:
            print(f"Error creando punto ({x},{y},{z}): {e}")
        return None

    def create_area_by_points(self, points, prop_name="Default"):
        """Crea un área dada una lista de nombres de puntos."""
        try:
            # AddByPoint(NumberPoints, PointNames, Name, PropName, UserName)
            ret = self.SapModel.AreaObj.AddByPoint(len(points), points, "", prop_name, "")
            if isinstance(ret, (list, tuple)) and ret[-1] == 0:
                return str(ret[0])
        except Exception as e:
            print(f"Error creando área con puntos {points}: {e}")
        return None

    def _get_shape_coords_2d(self, shape_type, center_u, center_v, dim, num_points):
        """
        Genera coordenadas 2D (u, v) para una forma dada.
        shape_type: 'Círculo' o 'Cuadrado'
        dim: Diámetro (si es círculo) o Lado (si es cuadrado)
        """
        coords = []
        radius = dim / 2.0
        
        # Pre-calculation for square (equidistant spacing)
        # Perimeter = 4 * dim
        # Step = Perimeter / num_points
        perimeter = 4.0 * dim
        step = perimeter / float(num_points) if num_points > 0 else 0
        
        for i in range(num_points):
            if shape_type.lower() == "círculo":
                # Ángulo en radianes
                angle = 2 * math.pi * i / num_points
                u = center_u + radius * math.cos(angle)
                v = center_v + radius * math.sin(angle)
                coords.append((u, v))
                
            elif shape_type.lower() == "cuadrado":
                # Equidistant walking along perimeter
                # Start at Angle 0 (Right Middle) -> (radius, 0) relative to center
                # CCW direction: Up -> Left -> Down -> Right -> Up
                
                current_dist = i * step
                
                u_local = 0.0
                v_local = 0.0
                
                # Phase 1: Right edge, moving UP (from 0 to radius)
                if current_dist < radius:
                    u_local = radius
                    v_local = current_dist
                # Phase 2: Top edge, moving LEFT
                elif current_dist < radius + dim:
                    rem = current_dist - radius
                    u_local = radius - rem
                    v_local = radius
                # Phase 3: Left edge, moving DOWN
                elif current_dist < radius + 2*dim:
                    rem = current_dist - (radius + dim)
                    u_local = -radius
                    v_local = radius - rem
                # Phase 4: Bottom edge, moving RIGHT
                elif current_dist < radius + 3*dim:
                    rem = current_dist - (radius + 2*dim)
                    u_local = -radius + rem
                    v_local = -radius
                # Phase 5: Right edge, moving UP (from -radius to 0)
                else:
                    rem = current_dist - (radius + 3*dim)
                    u_local = radius
                    v_local = -radius + rem
                
                u = center_u + u_local
                v = center_v + v_local
                coords.append((u, v))
                
        return coords

    def create_hole_mesh(self, 
                         outer_shape, outer_dim, 
                         inner_shape, inner_dim, 
                         num_angular, num_radial, 
                         origin_x, origin_y, origin_z, 
                         plane="XY", prop_name="Default"):
        """
        Crea una malla con orificio (o transición de formas) interpolando entre dos anillos.
        
        Args:
            outer_shape (str): "Círculo" o "Cuadrado".
            outer_dim (float): Dimensión externa (Lado o Diámetro).
            inner_shape (str): "Círculo" o "Cuadrado".
            inner_dim (float): Dimensión interna (Lado o Diámetro).
            num_angular (int): Número de puntos por anillo.
            num_radial (int): Número de subdivisiones radiales (anillos de áreas).
            origin_x, origin_y, origin_z (float): Coordenada de la esquina de referencia (bounding box).
            plane (str): "XY", "XZ", "YZ".
            prop_name (str): Propiedad de área.
        """
        if self.SapModel is None:
            if self._connect_to_sap() is None:
                return []

        print(f"Generando malla con orificio: {inner_shape} -> {outer_shape} en {plane}...")
        
        # 1. Definir centro local (u, v) relativo al origen (esquina)
        # Asumimos que el origen es la esquina inferior izquierda del bounding box externo
        center_u = outer_dim / 2.0
        center_v = outer_dim / 2.0
        
        # Crear nodo en el centro
        if plane.upper() == "XY":
            cx = origin_x + center_u
            cy = origin_y + center_v
            cz = origin_z
        elif plane.upper() == "XZ":
            cx = origin_x + center_u
            cy = origin_y
            cz = origin_z + center_v
        elif plane.upper() == "YZ":
            cx = origin_x
            cy = origin_y + center_u
            cz = origin_z + center_v
        else:
            cx, cy, cz = origin_x, origin_y, origin_z
            
        self.create_point(cx, cy, cz)
        
        # 2. Generar coordenadas locales 2D para anillo interno y externo
        inner_coords = self._get_shape_coords_2d(inner_shape, center_u, center_v, inner_dim, num_angular)
        outer_coords = self._get_shape_coords_2d(outer_shape, center_u, center_v, outer_dim, num_angular)
        
        # 3. Generar anillos intermedios y crear puntos en SAP2000
        # all_rings_points[r][i] guardará el nombre del punto
        all_rings_points = [] 
        
        # Total de anillos de puntos = num_radial + 1
        # r=0 es interno, r=num_radial es externo
        
        for r in range(num_radial + 1):
            fraction = r / float(num_radial) if num_radial > 0 else 1.0
            ring_points = []
            
            for i in range(num_angular):
                u_in, v_in = inner_coords[i]
                u_out, v_out = outer_coords[i]
                
                # Interpolación lineal
                u = u_in + (u_out - u_in) * fraction
                v = v_in + (v_out - v_in) * fraction
                
                # Transformar a Global 3D según plano
                if plane.upper() == "XY":
                    gx = origin_x + u
                    gy = origin_y + v
                    gz = origin_z
                elif plane.upper() == "XZ":
                    gx = origin_x + u
                    gy = origin_y
                    gz = origin_z + v
                elif plane.upper() == "YZ":
                    gx = origin_x
                    gy = origin_y + u
                    gz = origin_z + v
                else:
                    gx, gy, gz = origin_x, origin_y, origin_z
                
                # Crear punto
                p_name = self.create_point(gx, gy, gz)
                if p_name:
                    ring_points.append(p_name)
                else:
                    # Fallback si falla crear punto (no debería pasar)
                    ring_points.append("")
            
            all_rings_points.append(ring_points)
            
        # 4. Crear Áreas conectando anillos
        created_areas = []
        
        for r in range(num_radial):
            inner_ring = all_rings_points[r]
            outer_ring = all_rings_points[r+1]
            
            # Verificar que tenemos puntos válidos
            if not inner_ring or not outer_ring:
                continue
                
            for i in range(num_angular):
                # Conectar 4 puntos: 
                # P1(inner, i) -> P2(inner, i+1) -> P3(outer, i+1) -> P4(outer, i)
                # Sentido antihorario usualmente
                
                p1 = inner_ring[i]
                p2 = inner_ring[(i+1) % num_angular]
                p3 = outer_ring[(i+1) % num_angular]
                p4 = outer_ring[i]
                
                if all([p1, p2, p3, p4]):
                    aname = self.create_area_by_points([p1, p2, p3, p4], prop_name)
                    if aname:
                        created_areas.append(aname)
        
        print(f"Se crearon {len(created_areas)} áreas con orificio.")
        try:
            self.SapModel.View.RefreshView(0, False)
        except:
            pass
            
        return created_areas

    def get_selected_point_coords(self):
        """
        Retorna las coordenadas (x, y, z) del primer punto seleccionado.
        Retorna None si no hay conexión o no hay puntos seleccionados.
        """
        if self.SapModel is None:
            if self._connect_to_sap() is None:
                return None
        
        # 1. Obtener objetos seleccionados
        # GetSelected(NumberItems, ObjectTypes, ObjectNames)
        try:
            ret_sel = self.SapModel.SelectObj.GetSelected(0, [], [])
            # ret_sel[-1] es RetCode
            if ret_sel[-1] != 0: 
                return None
            
            num_items = ret_sel[0]
            if num_items == 0: 
                return None
            
            # Los arrays suelen venir en ret_sel[1] y ret_sel[2]
            obj_types = ret_sel[1]
            obj_names = ret_sel[2]
            
            point_name = None
            
            # Buscar el primer objeto de tipo 1 (PointObject)
            for i in range(num_items):
                # Asegurar que sea entero, a veces viene como int, a veces smallint
                if int(obj_types[i]) == 1:
                    point_name = obj_names[i]
                    break
            
            if not point_name:
                return None
                
            # 2. Obtener coordenadas
            # GetCoordCartesian(Name, x, y, z, CSys)
            ret_coord = self.SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0, "Global")
            
            if ret_coord[-1] == 0:
                # Retorna [x, y, z, RetCode]
                return {
                    "name": point_name,
                    "x": ret_coord[0],
                    "y": ret_coord[1],
                    "z": ret_coord[2]
                }
                
        except Exception as e:
            print(f"Error obteniendo selección: {e}")
            
        return None
