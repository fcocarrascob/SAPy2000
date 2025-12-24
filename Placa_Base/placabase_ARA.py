import comtypes.client
import math

# Conectar al helper y obtener SapModel de la instancia activa
helper = comtypes.client.CreateObject('SAP2000v1.Helper')
helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
try:
	mySapObject = helper.GetObject("CSI.SAP2000.API.SapObject")
	SapModel = mySapObject.SapModel
	print("Conexión exitosa a la instancia abierta.")
except Exception as e:
	raise RuntimeError("No se encontró ninguna instancia de SAP2000 ejecutándose.") from e


def _ret_ok(ret):
	try:
		return bool(ret and ret[-1] == 0)
	except Exception:
		return False


def _created_name_from_ret(ret, fallback=None):
	if not ret:
		return fallback
	if len(ret) >= 2:
		created = ret[0] or fallback
		if isinstance(created, (list, tuple)) and len(created) > 0:
			return created[0]
		return created
	return fallback


def create_circle_points(SapModel, radius, num_points=8, z=0.0, cx=0.0, cy=0.0, prefix='P_c'):
	"""Crea puntos en un círculo centrado en (cx,cy, z). Mantiene compatibilidad con el argumento `z`.
	Devuelve lista de nombres.
	"""
	point_names = []
	for j in range(num_points):
		angle = j * (360.0 / num_points)
		x = float(cx) + radius * math.cos(math.radians(angle))
		y = float(cy) + radius * math.sin(math.radians(angle))
		suggested = f"{prefix}{j+1}"
		try:
			ret = SapModel.PointObj.AddCartesian(x, y, z, "", suggested)
		except Exception:
			ret = SapModel.PointObj.AddCartesian(x, y, z)
		if _ret_ok(ret):
			name = _created_name_from_ret(ret, fallback=suggested)
			point_names.append(name)
		else:
			point_names.append(None)
			print(f"Error creando punto circular #{j+1}: código {ret[-1] if ret else 'N/A'}")
	return point_names


def create_square_points(SapModel, side_length, z=0.0, cx=0.0, cy=0.0, prefix='P_s'):
	"""Crea 8 puntos de un cuadrado centrado en (cx,cy) a altura `z`.
	Orden: arriba-izq, arriba-centro, arriba-der, derecha-centro, abajo-der, abajo-centro, abajo-izq, izquierda-centro
	"""
	half = float(side_length) / 2.0
	coords = [
		(-half,  half),
		( 0.0,   half),
		( half,  half),
		( half,  0.0),
		( half, -half),
		( 0.0,  -half),
		(-half, -half),
		(-half,  0.0),
	]
	point_names = []
	for i, (dx, dy) in enumerate(coords, start=1):
		x = float(cx) + float(dx)
		y = float(cy) + float(dy)
		suggested = f"{prefix}{i}"
		try:
			ret = SapModel.PointObj.AddCartesian(x, y, z, "", suggested)
		except Exception:
			ret = SapModel.PointObj.AddCartesian(x, y, z)
		if _ret_ok(ret):
			name = _created_name_from_ret(ret, fallback=suggested)
			point_names.append(name)
		else:
			point_names.append(None)
			print(f"Error al crear punto de cuadrado #{i}: código {ret[-1] if ret else 'N/A'}")
	return point_names


def get_point_coord(SapModel, point_name):
	try:
		ret = SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0)
	except Exception:
		return False, (None, None, None)
	if not _ret_ok(ret):
		return False, (None, None, None)
	return True, (ret[0], ret[1], ret[2])


def sort_points_by_angle(SapModel, point_names):
	pts = []
	for pn in point_names:
		ok, coord = get_point_coord(SapModel, pn)
		if not ok:
			pts.append((pn, float('-inf')))
		else:
			x, y, _ = coord
			ang = math.atan2(y, x)
			pts.append((pn, ang))
	pts.sort(key=lambda t: t[1])
	return [p[0] for p in pts]


def create_area_by_point_names(SapModel, point_name_list, area_user_name=''):
	try:
		ret = SapModel.AreaObj.AddByPoint(len(point_name_list), point_name_list, area_user_name)
	except Exception:
		try:
			ret = SapModel.AreaObj.AddByPoint(len(point_name_list), point_name_list, area_user_name)
		except Exception as e:
			print(f"Error llamando AreaObj.AddByPoint: {e}")
			return False, None, None
	ok = _ret_ok(ret)
	created_name = None
	if ok:
		created_name = _created_name_from_ret(ret, fallback=area_user_name)
	else:
		print(f"Error creando área con puntos {point_name_list}: código {ret[-1] if ret else 'N/A'}")
	return ok, created_name, ret


def create_ring_areas(SapModel, inner_pts, outer_pts, area_name_prefix='A_r'):
	if len(inner_pts) != len(outer_pts):
		print("Error: inner_pts y outer_pts deben tener la misma cantidad de puntos.")
		return []
	inner_sorted = sort_points_by_angle(SapModel, inner_pts)
	outer_sorted = sort_points_by_angle(SapModel, outer_pts)
	n = len(inner_sorted)
	results = []
	for i in range(n):
		p1 = inner_sorted[i]
		p2 = inner_sorted[(i+1) % n]
		p3 = outer_sorted[(i+1) % n]
		p4 = outer_sorted[i]
		area_pts = [p1, p2, p3, p4]
		area_name = f"{area_name_prefix}_{i+1}"
		ok, created_name, ret = create_area_by_point_names(SapModel, area_pts, area_name)
		results.append((created_name or area_name, ok))
	return results


if __name__ == '__main__':
	# parámetros mínimos para crear los anillos
	bolt_dia = 25.0
	# mapeo simple para B (igual que en placabase_std)
	if bolt_dia == 16:
		A = 80; B = 80
	elif bolt_dia == 19:
		A = 100; B = 100
	elif bolt_dia == 22:
		A = 100; B = 100
	elif bolt_dia == 25:
		A = 100; B = 100
	elif bolt_dia == 32:
		A = 125; B = 125
	elif bolt_dia == 38:
		A = 150; B = 150
	elif bolt_dia == 44:
		A = 175; B = 175
	elif bolt_dia == 51:
		A = 200; B = 200
	elif bolt_dia == 57:
		A = 225; B = 225
	elif bolt_dia == 64:
		A = 250; B = 250
	else:
		A = 100; B = 100

	circle_radius = bolt_dia / 2.0
	circle_point_ids = create_circle_points(SapModel, circle_radius, num_points=8, z=0.0, prefix='P_c')
	print("Puntos del círculo creados:", circle_point_ids)

	outer_half = float(B) / 2.0
	square_point_ids = create_square_points(SapModel, B, z=0.0, prefix='P_s_outer')
	print("Puntos del cuadrado exterior creados:", square_point_ids)

	inner_half = (circle_radius + outer_half) / 2.0
	inner_side = inner_half * 2.0
	inner_square_point_ids = create_square_points(SapModel, inner_side, z=0.0, prefix='P_s_inner')
	print("Puntos del cuadrado interior creados:", inner_square_point_ids)

	ring_inner = create_ring_areas(SapModel, circle_point_ids, inner_square_point_ids, area_name_prefix='A_ring_in')
	print("Resultado creación áreas anillo interno:", ring_inner)
	ring_outer = create_ring_areas(SapModel, inner_square_point_ids, square_point_ids, area_name_prefix='A_ring_out')
	print("Resultado creación áreas anillo externo:", ring_outer)

	try:
		SapModel.View.RefreshView(0, False)
		SapModel.View.RefreshWindow()
	except Exception:
		pass

