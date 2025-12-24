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


def sort_points_by_angle(SapModel, point_names, center=None):
	"""Ordena `point_names` por ángulo polar respecto a `center`.
	Si `center` es None, se calcula como la media de las coordenadas válidas.
	"""
	coords = []
	for pn in point_names:
		ok, coord = get_point_coord(SapModel, pn)
		if ok:
			coords.append((pn, coord[0], coord[1]))
		else:
			coords.append((pn, None, None))

	# calcular centro si no se entrega
	if center is None:
		xs = [c[1] for c in coords if c[1] is not None]
		ys = [c[2] for c in coords if c[2] is not None]
		if xs and ys:
			cx = sum(xs) / len(xs)
			cy = sum(ys) / len(ys)
		else:
			cx, cy = 0.0, 0.0
	else:
		cx, cy = float(center[0]), float(center[1])

	pts = []
	for pn, x, y in coords:
		if x is None:
			pts.append((pn, float('-inf')))
		else:
			ang = math.atan2(y - cy, x - cx)
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
	# Calcular centro promedio común para ordenar ambos anillos coherentemente
	xs = []
	ys = []
	for pn in inner_pts + outer_pts:
		ok, coord = get_point_coord(SapModel, pn)
		if ok:
			xs.append(coord[0])
			ys.append(coord[1])
	if xs and ys:
		center = (sum(xs) / len(xs), sum(ys) / len(ys))
	else:
		center = (0.0, 0.0)

	inner_sorted = sort_points_by_angle(SapModel, inner_pts, center=center)
	outer_sorted = sort_points_by_angle(SapModel, outer_pts, center=center)

	# Alineamiento rotacional: rotar outer_sorted para minimizar la diferencia angular
	def _angles_for(point_list):
		angs = []
		for pn in point_list:
			ok, coord = get_point_coord(SapModel, pn)
			if not ok:
				angs.append(None)
			else:
				angs.append(math.atan2(coord[1] - center[1], coord[0] - center[0]))
		return angs

	inner_angles = _angles_for(inner_sorted)
	outer_angles = _angles_for(outer_sorted)
	n = len(inner_angles)
	# función de diferencia angular mínima
	def ang_diff(a, b):
		d = abs(a - b) % (2 * math.pi)
		return min(d, 2 * math.pi - d)

	best_shift = 0
	best_score = float('inf')
	for shift in range(n):
		score = 0.0
		for i in range(n):
			a = inner_angles[i]
			b = outer_angles[(i + shift) % n]
			if a is None or b is None:
				score += 1e6
			else:
				score += ang_diff(a, b)
		if score < best_score:
			best_score = score
			best_shift = shift
	if best_shift != 0:
		outer_sorted = outer_sorted[best_shift:] + outer_sorted[:best_shift]
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

	# Lista de posiciones de centros de pernos: definir aquí (x, y, z) en mm
	n_pernos = 4
	H_col = 300.0
	B_col = 250.0
	bolt_centers = [
        (A/2.0, H_col/2.0, 0.0),
        (3*A/2.0, H_col/2.0, 0.0),
        (-A/2.0, H_col/2.0, 0.0),
        (-3*A/2.0, H_col/2.0, 0.0),
		(A/2.0, -H_col/2.0, 0.0),
        (3*A/2.0, -H_col/2.0, 0.0),
        (-A/2.0, -H_col/2.0, 0.0),
        (-3*A/2.0, -H_col/2.0, 0.0),
		]

	all_results = []
	circle_radius = bolt_dia / 2.0
	outer_half = float(B) / 2.0
	for idx, (cx, cy, cz) in enumerate(bolt_centers, start=1):
		# crear punto marcador del centro (etiqueta para identificar)
		center_name = None
		try:
			retc = SapModel.PointObj.AddCartesian(cx, cy, cz, "", f'CENTER_{idx}')
		except Exception:
			retc = SapModel.PointObj.AddCartesian(cx, cy, cz)
		if _ret_ok(retc):
			center_name = _created_name_from_ret(retc, fallback=f'CENTER_{idx}')
			print(f"[{idx}] Punto centro creado: {center_name} @ ({cx},{cy},{cz})")
		else:
			print(f"[{idx}] Error creando punto centro: codigo {retc[-1] if retc else 'N/A'}")

		# crear círculo y cuadrados centrados en (cx,cy,cz)
		circle_point_ids = create_circle_points(SapModel, circle_radius, num_points=8, z=cz, cx=cx, cy=cy, prefix=f'P_c{idx}_')
		print(f"[{idx}] Puntos del círculo creados en ({cx},{cy}):", circle_point_ids)

		square_point_ids = create_square_points(SapModel, B, z=cz, cx=cx, cy=cy, prefix=f'P_s_outer{idx}_')
		print(f"[{idx}] Puntos del cuadrado exterior creados en ({cx},{cy}):", square_point_ids)

		inner_half = (circle_radius + outer_half) / 2.0
		inner_side = inner_half * 2.0
		inner_square_point_ids = create_square_points(SapModel, inner_side, z=cz, cx=cx, cy=cy, prefix=f'P_s_inner{idx}_')
		print(f"[{idx}] Puntos del cuadrado interior creados en ({cx},{cy}):", inner_square_point_ids)

		ring_inner = create_ring_areas(SapModel, circle_point_ids, inner_square_point_ids, area_name_prefix=f'A_ring_in{idx}')
		print(f"[{idx}] Resultado creación áreas anillo interno:", ring_inner)
		ring_outer = create_ring_areas(SapModel, inner_square_point_ids, square_point_ids, area_name_prefix=f'A_ring_out{idx}')
		print(f"[{idx}] Resultado creación áreas anillo externo:", ring_outer)

		all_results.append({'center': (cx, cy, cz), 'ring_inner': ring_inner, 'ring_outer': ring_outer})

	try:
		SapModel.View.RefreshView(0, False)
		SapModel.View.RefreshWindow()
	except Exception:
		pass

