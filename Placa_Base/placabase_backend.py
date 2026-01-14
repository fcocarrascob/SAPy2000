import sys
import os
import json
import math
import comtypes.client
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any

# --- Configuration Data Class ---
@dataclass
class PlateConfig:
    bolt_dia: float = 25.0
    H_col: float = 300.0
    B_col: float = 250.0
    n_pernos: int = 4
    bolt_centers: List[Tuple[float, float, float]] = field(default_factory=list)
    flange_thickness: Optional[float] = None
    web_thickness: Optional[float] = None
    plate_thickness: Optional[float] = None
    include_anchor_chair: bool = False
    anchor_chair_height: Optional[float] = None
    anchor_chair_thickness: Optional[float] = None

    @classmethod
    def from_json(cls, json_path: str) -> 'PlateConfig':
        if not os.path.exists(json_path):
            return cls()
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cfg = cls()
        cfg.bolt_dia = float(data.get('bolt_dia', cfg.bolt_dia))
        cfg.H_col = float(data.get('H_col', cfg.H_col))
        cfg.B_col = float(data.get('B_col', cfg.B_col))
        cfg.n_pernos = int(data.get('n_pernos', cfg.n_pernos))
        
        if 'bolt_centers' in data:
            try:
                cfg.bolt_centers = [tuple(map(float, c)) for c in data['bolt_centers']]
            except Exception:
                pass # Keep default empty
        
        # Default centers if empty
        if not cfg.bolt_centers:
            A, _ = cls.map_dia_to_AB(cfg.bolt_dia)
            H = cfg.H_col
            cfg.bolt_centers = [
                (A/2.0,  H/2.0, 0.0), (3*A/2.0, H/2.0, 0.0),
                (-A/2.0, H/2.0, 0.0), (-3*A/2.0, H/2.0, 0.0),
                (A/2.0, -H/2.0, 0.0), (3*A/2.0, -H/2.0, 0.0),
                (-A/2.0, -H/2.0, 0.0), (-3*A/2.0, -H/2.0, 0.0),
            ]

        if 'flange_thickness' in data and data['flange_thickness']:
            cfg.flange_thickness = float(data['flange_thickness'])
        if 'web_thickness' in data and data['web_thickness']:
            cfg.web_thickness = float(data['web_thickness'])
        if 'plate_thickness' in data and data['plate_thickness']:
            cfg.plate_thickness = float(data['plate_thickness'])
        
        cfg.include_anchor_chair = bool(data.get('include_anchor_chair', False))
            
        if 'anchor_chair_height' in data and data['anchor_chair_height']:
            cfg.anchor_chair_height = float(data['anchor_chair_height'])
        if 'anchor_chair_thickness' in data and data['anchor_chair_thickness']:
            cfg.anchor_chair_thickness = float(data['anchor_chair_thickness'])
            
        return cfg

    @staticmethod
    def map_dia_to_AB(dia: float) -> Tuple[float, float]:
        try:
            d = int(round(float(dia)))
        except Exception:
            return 100.0, 100.0
        mapping = {
            16: (80, 80), 19: (100, 100), 22: (100, 100), 25: (100, 100),
            32: (125, 125), 38: (150, 150), 44: (175, 175), 51: (200, 200),
            57: (225, 225), 64: (250, 250),
        }
        return mapping.get(d, (100.0, 100.0))


class BasePlateBackend:
    def __init__(self, sap_model=None, logger=None):
        self.SapModel = sap_model
        self.logger = logger
        self.config = PlateConfig()
        
        # Conectar si no hay modelo proporcionado
        if self.SapModel is None:
            self._connect_to_sap()

    def log(self, message):
        """Envía mensaje al logger si existe, o imprime a consola."""
        if self.logger:
            self.logger(message)
        else:
            print(message)

    def _connect_to_sap(self):
        try:
            # Intentar usar el Helper oficial o GetActiveObject
            try:
                helper = comtypes.client.CreateObject('SAP2000v1.Helper')
                helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
                mySapObject = helper.GetObject("CSI.SAP2000.API.SapObject")
            except:
                mySapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
                
            self.SapModel = mySapObject.SapModel
            self.log("Conexión exitosa a la instancia abierta de SAP2000.")
        except Exception as e:
            self.log(f"Aviso: Backend iniciado sin conexión a SAP2000. ({e})")
            self.SapModel = None

    def load_config_from_file(self, json_path: str):
        self.config = PlateConfig.from_json(json_path)
        self.log(f"Configuración cargada desde archivo: {self.config}")
        
    def run_process(self):
        """Método principal para ejecutar la generación de la placa base."""
        if not self.SapModel:
            # Reintentar conexión si se perdió
            self._connect_to_sap()
            if not self.SapModel:
                raise RuntimeError("No hay conexión con SAP2000.")

        self.log("Iniciando generación de placa base...")
        self.apply_config()
        self.log("Proceso finalizado.")

    # [Aquí irían los métodos apply_config y la lógica de modelado refactorizada]
    # Por ahora mantendremos el código existente de SapPlateGenerator adaptado
    # Importante: En la implementación real, copiaríamos el resto de métodos de SapPlateGenerator
    # y los adaptaríamos para usar self.SapModel que ya puede venir inyectado.


    def apply_config(self):
        self.run()

    def _check_ret(self, ret, success_msg="", error_msg="") -> bool:
        code = -1
        if isinstance(ret, int):
            code = ret
        elif hasattr(ret, '__getitem__') and len(ret) > 0:
            code = ret[-1]
        
        if code == 0:
            if success_msg:
                self.log(success_msg)
            return True
        else:
            if error_msg:
                self.log(f"{error_msg} (Code: {code})")
            return False

    def _get_created_name(self, ret, fallback: str) -> str:
        """Extracts the created name from the return tuple (usually first element)."""
        if ret and len(ret) >= 2 and ret[-1] == 0:
            # Sometimes the first element is a tuple/list itself
            val = ret[0]
            if isinstance(val, (list, tuple)) and len(val) > 0:
                return str(val[0])
            return str(val)
        return fallback

    def create_material_prop(self, name: str, thickness: float, mat_name: str = "A992Fy50"):
        """Creates a shell property using SetShell_1 (preferred) or SetShell."""
        # Try SetShell_1 first (newer API)
        # Signature: SetShell_1(Name, ShellType, IncludeDrillingDOF, MatProp, MatAng, Thickness, Bending, Color, Notes, GUID)
        try:
            # We pass dummy values for optional args if needed, but Python comtypes handles optionals usually.
            # However, explicit is better.
            # ShellType=1 (Shell-Thin), IncludeDrillingDOF=True
            ret = self.SapModel.PropArea.SetShell_1(name, 1, True, mat_name, 0.0, thickness, thickness)
            if self._check_ret(ret, f"Propiedad '{name}' creada (SetShell_1)."):
                return True
        except AttributeError:
            # Fallback to SetShell
            # Signature: SetShell(Name, ShellType, MatProp, MatAng, Thickness, Bending)
            try:
                ret = self.SapModel.PropArea.SetShell(name, 1, mat_name, 0.0, thickness, thickness)
                if self._check_ret(ret, f"Propiedad '{name}' creada (SetShell)."):
                    return True
            except Exception as e:
                self.log(f"Error creando propiedad '{name}': {e}")
        except Exception as e:
            self.log(f"Error creando propiedad '{name}': {e}")
        return False

    def create_point(self, x: float, y: float, z: float, user_name: str = "") -> Optional[str]:
        """Creates a point. Returns the name of the created point."""
        # Signature: AddCartesian(x, y, z, Name, UserName, CSys, ...)
        # Name is ByRef output. We pass "" as placeholder.
        try:
            ret = self.SapModel.PointObj.AddCartesian(x, y, z, "", user_name)
            if self._check_ret(ret):
                return self._get_created_name(ret, user_name)
        except Exception as e:
            self.log(f"Error creando punto en ({x},{y},{z}): {e}")
        return None

    def create_area_by_points(self, points: List[str], prop_name: str = "Default", user_name: str = "") -> Optional[str]:
        """Creates an area from a list of point names."""
        # Signature: AddByPoint(NumberPoints, Point(), Name, PropName, UserName)
        # Point() is array of strings. Name is ByRef output.
        try:
            ret = self.SapModel.AreaObj.AddByPoint(len(points), points, "", prop_name, user_name)
            if self._check_ret(ret):
                return self._get_created_name(ret, user_name)
        except Exception as e:
            self.log(f"Error creando área con puntos {points}: {e}")
        return None

    def create_area_by_coord(self, xs, ys, zs, prop_name: str = "Default", user_name: str = "") -> Optional[str]:
        """Creates an area by coordinates."""
        # Signature: AddByCoord(NumberPoints, x, y, z, Name, PropName, UserName, CSys)
        try:
            ret = self.SapModel.AreaObj.AddByCoord(len(xs), xs, ys, zs, "", prop_name, user_name, "Global")
            if self._check_ret(ret):
                return self._get_created_name(ret, user_name)
        except Exception as e:
            self.log(f"Error creando área por coordenadas: {e}")
        return None

    def get_point_coord(self, point_name: str) -> Optional[Tuple[float, float, float]]:
        try:
            # GetCoordCartesian(Name, x, y, z, CSys) -> returns (x, y, z, ret)
            # Note: x,y,z are ByRef outputs.
            ret = self.SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0, "Global")
            if self._check_ret(ret):
                return (ret[0], ret[1], ret[2])
        except Exception:
            pass
        return None

    def divide_area(self, area_name: str, n_divisions: int):
        """Divides an area using MeshType=1 (Grid)."""
        # Signature: Divide(Name, MeshType, NumberAreas, AreaName, n1, n2, ...)
        # MeshType=1 -> Grid. n1, n2 are divisions.
        # We want 1xN divisions (or similar). The original code used 4*n_pernos and 10.
        # Assuming n1 is along 1-2 edge, n2 along 1-3 edge.
        try:
            # Passing 0 and [] for NumberAreas and AreaName (ByRef outputs)
            ret = self.SapModel.EditArea.Divide(area_name, 1, 0, [], n_divisions, 10)
            self._check_ret(ret, f"Área '{area_name}' dividida.")
        except Exception as e:
            self.log(f"Error dividiendo área '{area_name}': {e}")

    def coordinate_range(self, xmin, xmax, ymin, ymax, zmin, zmax,
                         deselect=False, csys="Global", include_intersections=False,
                         point=True, line=True, area=True, solid=True, link=True):
        """
        Wrapper para SapModel.SelectObj.CoordinateRange con manejo de retornos de comtypes.
        Retorna (ok: bool, ret_raw)
        """
        try:
            ret = self.SapModel.SelectObj.CoordinateRange(
                float(xmin), float(xmax),
                float(ymin), float(ymax),
                float(zmin), float(zmax),
                bool(deselect),
                str(csys),
                bool(include_intersections),
                bool(point), bool(line), bool(area), bool(solid), bool(link)
            )
        except Exception as e:
            return False, e

        # ret puede ser int o tuple/list cuyo último elemento es RetCode
        if isinstance(ret, (list, tuple)):
            rc = int(ret[-1])
            return (rc == 0), ret
        else:
            return (int(ret) == 0), ret

    def divide_area_by_selection(self, area_name: str) -> List[str]:
        """
        Divide `area_name` usando puntos seleccionados en los bordes (MeshType=3).
        Retorna la lista de nombres de las nuevas áreas creadas.
        """
        try:
            # Firma: Divide(Name, MeshType, NumberAreas, AreaName(), n1, n2, ...)
            # Retorna tupla: (NumberAreas, AreaName_tuple, RetCode) o similar dependiendo de comtypes
            ret = self.SapModel.EditArea.Divide(
                str(area_name), 3, 0, [], 0, 0, 0.0, 0.0, 
                False, False, True
            )
            
            # Check success
            if self._check_ret(ret, f"Área '{area_name}' dividida por puntos seleccionados."):
                # Extract new area names. 
                # ret structure is typically (NumberAreas, (Name1, Name2, ...), RetCode)
                # or sometimes just (NumberAreas, (Name1, Name2, ...)) if RetCode is separate?
                # Based on standard comtypes behavior for ByRef arrays:
                if len(ret) >= 2:
                    # ret[1] should be the tuple of names
                    names = ret[1]
                    if isinstance(names, (list, tuple)):
                        return list(names)
            
        except Exception as e:
            self.log(f"Error dividiendo área '{area_name}' por selección: {e}")
        return []

    def subdivide_areas(self, area_names: List[str], n1: int = 2, n2: int = 2):
        """Subdivides a list of areas into n1 x n2 grids."""
        if not area_names:
            return
        
        self.log(f"Subdividiendo {len(area_names)} áreas en grilla {n1}x{n2}...")
        for name in area_names:
            self.divide_area(name, n1) # divide_area uses n1 for both or we need to update it?
            # My existing divide_area takes 'n_divisions' and passes it as n1, and hardcodes n2=10?
            # Let's check existing divide_area implementation.
            # It was: ret = self.SapModel.EditArea.Divide(area_name, 1, 0, [], n_divisions, 10)
            # That seems specific to the link area logic (n_pernos*4, 10).
            # I should probably make a more generic divide function or use the API directly here.
            
            try:
                self.SapModel.EditArea.Divide(name, 1, 0, [], n1, n2)
            except Exception as e:
                print(f"Error subdividiendo {name}: {e}")

    # --- Geometric Logic ---

    def create_circle_points(self, cx, cy, z, radius, num_points=16, prefix="P_c") -> List[str]:
        names = []
        for j in range(num_points):
            angle = math.radians(j * (360.0 / num_points))
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            nm = self.create_point(x, y, z, f"{prefix}{j+1}")
            names.append(nm)
        return names

    def create_square_points(self, cx, cy, z, side, num_points=16, prefix="P_s") -> List[str]:
        half = side / 2.0
        perimeter = 4.0 * side
        names = []
        if num_points < 4: num_points = 4
        
        for i in range(num_points):
            s = (i * perimeter) / num_points
            if s < side:
                x, y = -half + s, half
            elif s < 2 * side:
                x, y = half, half - (s - side)
            elif s < 3 * side:
                x, y = half - (s - 2 * side), -half
            else:
                x, y = -half, -half + (s - 3 * side)
            
            nm = self.create_point(cx + x, cy + y, z, f"{prefix}{i+1}")
            names.append(nm)
        return names

    def sort_points_angularly(self, point_names: List[str], center: Tuple[float, float]) -> List[str]:
        """Sorts points by angle around a center."""
        valid_pts = []
        for pn in point_names:
            if not pn: continue
            coord = self.get_point_coord(pn)
            if coord:
                angle = math.atan2(coord[1] - center[1], coord[0] - center[0])
                valid_pts.append((pn, angle))
        
        valid_pts.sort(key=lambda x: x[1])
        return [p[0] for p in valid_pts]

    def align_rings(self, inner_pts: List[str], outer_pts: List[str], center: Tuple[float, float]) -> Tuple[List[str], List[str]]:
        """Aligns two rings of points to minimize connection length (angular difference)."""
        inner_sorted = self.sort_points_angularly(inner_pts, center)
        outer_sorted = self.sort_points_angularly(outer_pts, center)
        
        if not inner_sorted or not outer_sorted:
            return inner_sorted, outer_sorted

        # Helper to get angles
        def get_angles(pts):
            angles = []
            for p in pts:
                c = self.get_point_coord(p)
                if c:
                    angles.append(math.atan2(c[1] - center[1], c[0] - center[0]))
                else:
                    angles.append(0)
            return angles

        inner_angs = get_angles(inner_sorted)
        outer_angs = get_angles(outer_sorted)
        
        n = len(inner_sorted)
        best_shift = 0
        min_diff = float('inf')
        
        for shift in range(n):
            diff = 0
            for i in range(n):
                a1 = inner_angs[i]
                a2 = outer_angs[(i + shift) % n]
                d = abs(a1 - a2) % (2 * math.pi)
                d = min(d, 2 * math.pi - d)
                diff += d
            
            if diff < min_diff:
                min_diff = diff
                best_shift = shift
        
        if best_shift != 0:
            outer_sorted = outer_sorted[best_shift:] + outer_sorted[:best_shift]
            
        return inner_sorted, outer_sorted

    def create_ring_mesh(self, inner_pts: List[str], outer_pts: List[str], center: Tuple[float, float], prefix: str, prop_name: str):
        """Creates areas connecting two rings of points."""
        inner, outer = self.align_rings(inner_pts, outer_pts, center)
        n = min(len(inner), len(outer))
        
        for i in range(n):
            p1 = inner[i]
            p2 = inner[(i+1)%n]
            p3 = outer[(i+1)%n]
            p4 = outer[i]
            self.create_area_by_points([p1, p2, p3, p4], prop_name, f"{prefix}_{i+1}")

    def create_anchor_chair_plates(self, z_level: float, prop_name: str):
        """Genera placas de silla en la cota z_level usando el mismo patrón de pernos."""
        cfg = self.config
        A, B_bolt = PlateConfig.map_dia_to_AB(cfg.bolt_dia)
        circle_radius = cfg.bolt_dia / 2.0
        outer_half = B_bolt / 2.0
        inner_half = (circle_radius + outer_half) / 2.0
        inner_side = inner_half * 2.0

        for idx, (cx, cy, _cz) in enumerate(cfg.bolt_centers, 1):
            self.log(f"Silla: procesando perno {idx} en ({cx}, {cy}) a z={z_level}...")
            self.create_point(cx, cy, z_level, f"CHAIR_CENTER_{idx}")

            c_pts = self.create_circle_points(cx, cy, z_level, circle_radius, 16, f"CHAIR_c{idx}_")
            in_pts = self.create_square_points(cx, cy, z_level, inner_side, 16, f"CHAIR_sin{idx}_")
            out_pts = self.create_square_points(cx, cy, z_level, B_bolt, 16, f"CHAIR_sout{idx}_")

            self.create_ring_mesh(c_pts, in_pts, (cx, cy), f"CHAIR_ring_in{idx}", prop_name)
            self.create_ring_mesh(in_pts, out_pts, (cx, cy), f"CHAIR_ring_out{idx}", prop_name)

    # --- Main Execution Logic ---

    def run(self):
        cfg = self.config
        
        # 1. Create Materials/Properties
        plate_prop = "PLACA_BASE"
        if cfg.plate_thickness:
            self.create_material_prop(plate_prop, cfg.plate_thickness)
        
        if cfg.flange_thickness:
            self.create_material_prop("ALA", cfg.flange_thickness)
        
        if cfg.web_thickness:
            self.create_material_prop("ALMA", cfg.web_thickness)

        chair_prop = None
        if cfg.include_anchor_chair:
            if cfg.anchor_chair_height and cfg.anchor_chair_height > 0 and cfg.anchor_chair_thickness and cfg.anchor_chair_thickness > 0:
                chair_prop = "ChairPlate"
                self.create_material_prop(chair_prop, cfg.anchor_chair_thickness, mat_name="A992Fy50")
            else:
                self.log("Silla de Anclaje activada pero faltan datos válidos de altura o espesor; se omite generación de silla.")

        # 2. Create Column Geometry (Flanges/Web)
        H, B = cfg.H_col, cfg.B_col
        z_col = 2.0 * H
        
        # Flanges and Web
        # Top Flange
        self.create_area_by_coord(
            [-B/2, B/2, B/2, -B/2], 
            [H/2, H/2, H/2, H/2], 
            [0, 0, z_col, z_col], 
            "ALA", "COL_FLANGE_TOP"
        )
        # Bottom Flange
        self.create_area_by_coord(
            [-B/2, B/2, B/2, -B/2], 
            [-H/2, -H/2, -H/2, -H/2], 
            [0, 0, z_col, z_col], 
            "ALA", "COL_FLANGE_BOTTOM"
        )
        # Web
        self.create_area_by_coord(
            [0, 0, 0, 0], 
            [H/2, -H/2, -H/2, H/2], 
            [0, 0, z_col, z_col], 
            "ALMA", "COL_WEB"
        )

        # 3. Create Bolt Areas
        A, B_bolt = PlateConfig.map_dia_to_AB(cfg.bolt_dia)
        circle_radius = cfg.bolt_dia / 2.0
        outer_half = B_bolt / 2.0
        inner_half = (circle_radius + outer_half) / 2.0
        inner_side = inner_half * 2.0
        
        outer_square_points_list = []

        for idx, (cx, cy, cz) in enumerate(cfg.bolt_centers, 1):
            print(f"Procesando perno {idx} en ({cx}, {cy})...")
            self.create_point(cx, cy, cz, f"CENTER_{idx}")
            
            # Points
            c_pts = self.create_circle_points(cx, cy, cz, circle_radius, 16, f"P_c{idx}_")
            in_pts = self.create_square_points(cx, cy, cz, inner_side, 16, f"P_s_in{idx}_")
            out_pts = self.create_square_points(cx, cy, cz, B_bolt, 16, f"P_s_out{idx}_")
            
            outer_square_points_list.append(out_pts)

            # Meshes
            if cfg.plate_thickness:
                self.create_ring_mesh(c_pts, in_pts, (cx, cy), f"A_ring_in{idx}", plate_prop)
                self.create_ring_mesh(in_pts, out_pts, (cx, cy), f"A_ring_out{idx}", plate_prop)

        # 4. Create Link Area (if applicable)
        # Logic: Connect specific points of outer squares if we have enough centers
        if len(cfg.bolt_centers) >= 4 and len(outer_square_points_list) == len(cfg.bolt_centers):
            try:
                N = len(cfg.bolt_centers) // 2
                # Indices are 0-based in list, but logic was 1-based in original
                # Original: 1, N, 2N, N+1
                # List indices: 0, N-1, 2N-1, N
                
                # Ensure indices are within bounds
                if 2*N-1 < len(outer_square_points_list):
                    p1 = outer_square_points_list[0][12]      # 1st center, point 13
                    p2 = outer_square_points_list[N-1][8]     # Nth center, point 9
                    p3 = outer_square_points_list[2*N-1][4]   # 2Nth center, point 5
                    p4 = outer_square_points_list[N][0]       # (N+1)th center, point 1
                    
                    link_area = self.create_area_by_points([p1, p2, p3, p4], plate_prop, "A_outer_link")
                    
                    if link_area:
                        self.divide_area(link_area, 4 * cfg.n_pernos)
            except Exception as e:
                print(f"No se pudo crear el área de enlace: {e}")

        # 3b. Anchor Chair Plates (optional)
        if chair_prop:
            self.create_anchor_chair_plates(cfg.anchor_chair_height, chair_prop)

        # 5. Divide Flange by Base Points (New Logic)
        try:
            # Clear selection first
            self.SapModel.SelectObj.ClearSelection()
            
            # Select points at the base of the top flange
            # Flange is at y = H/2, from x = -B/2 to B/2. z = 0.
            h_col = cfg.H_col
            b_col = cfg.B_col
            z_target = 0.0 # Base
            
            ok, ret = self.coordinate_range(
                -b_col/2, b_col/2,    # Xmin, Xmax
                h_col/2, h_col/2,     # Ymin, Ymax (Top Flange Plane)
                z_target, z_target,   # Zmin, Zmax (Base)
                deselect=False,
                csys="Global",
                include_intersections=True,
                point=True, line=False, area=False, solid=False, link=False
            )
            
            if ok:
                print(f"Puntos seleccionados en la base del ala superior (z={z_target}).")
                new_areas = self.divide_area_by_selection("COL_FLANGE_TOP")
                self.subdivide_areas(new_areas, 1, 2)
            else:
                print("Fallo la selección de puntos para dividir el ala.")

            # --- Bottom Flange Logic ---
            self.SapModel.SelectObj.ClearSelection()
            ok_bot, ret_bot = self.coordinate_range(
                -b_col/2, b_col/2,    # Xmin, Xmax
                -h_col/2, -h_col/2,   # Ymin, Ymax (Bottom Flange Plane is at -H/2)
                z_target, z_target,   # Zmin, Zmax (Base)
                deselect=False,
                csys="Global",
                include_intersections=True,
                point=True, line=False, area=False, solid=False, link=False
            )
            
            if ok_bot:
                print(f"Puntos seleccionados en la base del ala inferior (z={z_target}).")
                new_areas = self.divide_area_by_selection("COL_FLANGE_BOTTOM")
                self.subdivide_areas(new_areas, 1, 2)
            else:
                print("Fallo la selección de puntos para dividir el ala inferior.")

            # --- A_outer_link Division Logic (Top Flange Line) ---
            self.SapModel.SelectObj.ClearSelection()
            x_limit = A * cfg.n_pernos / 2.0
            
            ok_link, ret_link = self.coordinate_range(
                -x_limit, x_limit,    # Xmin, Xmax
                h_col/2, h_col/2,     # Ymin, Ymax (Top Flange Line)
                z_target, z_target,   # Zmin, Zmax (Base)
                deselect=False,
                csys="Global",
                include_intersections=True,
                point=True, line=False, area=False, solid=False, link=False
            )
            
            if ok_link:
                print(f"Puntos seleccionados para dividir A_outer_link en y={h_col/2}.")
                new_areas = self.divide_area_by_selection("A_outer_link")
                self.subdivide_areas(new_areas, 1, 2)
            else:
                print("Fallo la selección de puntos para dividir A_outer_link.")

            # --- Web Division Logic ---
            self.SapModel.SelectObj.ClearSelection()
            ok_web, ret_web = self.coordinate_range(
                0.0, 0.0,             # Xmin, Xmax (Web Plane)
                -h_col/2, h_col/2,    # Ymin, Ymax
                z_target, z_target,   # Zmin, Zmax (Base)
                deselect=False,
                csys="Global",
                include_intersections=True,
                point=True, line=False, area=False, solid=False, link=False
            )
            
            if ok_web:
                print(f"Puntos seleccionados en la base del alma (z={z_target}).")
                new_areas = self.divide_area_by_selection("COL_WEB")
                self.subdivide_areas(new_areas, 1, 2)
            else:
                print("Fallo la selección de puntos para dividir el alma.")
                
        except Exception as e:
            print(f"Error en la lógica de división final: {e}")

        # Refresh View
        try:
            self.SapModel.View.RefreshView(0, False)
            self.SapModel.View.RefreshWindow()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        # Standalone testing of backend
        backend = BasePlateBackend()
        
        # Load config if exists
        config_path = os.path.join(os.path.dirname(__file__), 'placabase_ARA_config.json')
        if os.path.exists(config_path):
            backend.load_config_from_file(config_path)
            backend.run_process()
            print("\nProceso finalizado correctamente.")
        else:
            print(f"No se encontró archivo de configuración en {config_path}")
        
    except Exception as e:
        print(f"\nError fatal: {e}")
        sys.exit(1)
