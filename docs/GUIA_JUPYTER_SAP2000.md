# Guía: Interacción con SAP2000 API en Jupyter Notebooks

## Filosofía de Trabajo

Jupyter Notebooks es ideal para **desarrollo iterativo** con SAP2000 porque permite:
- Probar funciones individuales celda por celda
- Ver resultados inmediatos
- Documentar el proceso mientras desarrollas
- Construir funciones complejas de forma incremental

---

## 1. Configuración Inicial (Celda de Setup)

Siempre inicia tu notebook con una celda de conexión que puedas reutilizar:

```python
# Celda 1: Conexión a SAP2000 (ejecutar una sola vez)
import comtypes.client

# Conectar a instancia activa de SAP2000
SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
SapModel = SapObject.SapModel

# Verificar conexión
print(f"✅ Conectado a SAP2000")
print(f"📁 Modelo: {SapModel.GetModelFilename()}")
```

> **Tip:** Mantén SAP2000 abierto con un modelo antes de ejecutar esta celda.

---

## 2. Patrón para Probar Funciones Individuales

### La Regla de Oro: Desempaquetar Retornos

```python
# ⚠️ INCORRECTO - Estilo VBA
ret = SapModel.PointObj.GetCoordCartesian(point_name, x, y, z)

# ✅ CORRECTO - Estilo Python comtypes
ret = SapModel.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0)
# ret = [x, y, z, RetCode]
if ret[-1] == 0:
    x, y, z = ret[0], ret[1], ret[2]
    print(f"Punto en: ({x}, {y}, {z})")
```

### Template para Explorar Funciones

```python
# Celda de prueba individual
def test_funcion():
    """Probar una función específica de la API"""
    
    # Llamar a la función con valores dummy para parámetros ByRef
    ret = SapModel.XXXX.YourFunction(param1, param2, 0, [], "")
    
    # Debug: Ver qué retorna
    print(f"Retorno completo: {ret}")
    print(f"Tipo: {type(ret)}")
    print(f"Longitud: {len(ret) if hasattr(ret, '__len__') else 'N/A'}")
    
    # Verificar éxito
    if ret[-1] == 0:
        print("✅ Función exitosa")
        # Extraer valores útiles
        return ret[:-1]  # Todo excepto RetCode
    else:
        print(f"❌ Error código: {ret[-1]}")
        return None

# Ejecutar prueba
resultado = test_funcion()
```

---

## 3. Flujo de Trabajo Iterativo

### Paso 1: Crear Funciones Atómicas

Cada celda = una operación simple y probada:

```python
# Celda: Crear un punto
def crear_punto(nombre, x, y, z):
    """Crea un punto en el modelo"""
    ret = SapModel.PointObj.AddCartesian(x, y, z, "", nombre)
    if ret[-1] == 0:
        print(f"✅ Punto '{ret[0]}' creado en ({x}, {y}, {z})")
        return ret[0]  # Nombre asignado
    else:
        print(f"❌ Error: {ret[-1]}")
        return None

# Probar
p1 = crear_punto("P1", 0, 0, 0)
p2 = crear_punto("P2", 5, 0, 0)
```

```python
# Celda: Crear material
def crear_material_concreto(nombre, fc_mpa):
    """Crea material de concreto"""
    # Primero agregar material genérico
    ret = SapModel.PropMaterial.AddMaterial(
        nombre,      # Name
        1,           # eMatType.Concrete = 1
        "Chile",     # Region
        "Concrete",  # Standard
        "fc28"       # Grade
    )
    if ret[-1] != 0:
        print(f"❌ Error creando material: {ret[-1]}")
        return None
    
    print(f"✅ Material '{nombre}' creado")
    return nombre

# Probar
mat = crear_material_concreto("H30", 30)
```

### Paso 2: Acumular Funciones Probadas

Una vez que las funciones individuales funcionan, combínalas:

```python
# Celda: Diccionario de funciones probadas
FUNCIONES_PROBADAS = {
    'crear_punto': crear_punto,
    'crear_material': crear_material_concreto,
    # Agregar más a medida que las pruebas
}
```

### Paso 3: Crear Función Orquestadora

```python
# Celda: Función que combina operaciones probadas
def crear_portico_simple(L, H, seccion, material):
    """
    Crea un pórtico simple usando funciones ya probadas
    
    L: Luz del pórtico (m)
    H: Altura (m)
    """
    resultados = {}
    
    # 1. Crear puntos (función ya probada)
    resultados['p1'] = crear_punto("Base1", 0, 0, 0)
    resultados['p2'] = crear_punto("Base2", L, 0, 0)
    resultados['p3'] = crear_punto("Top1", 0, 0, H)
    resultados['p4'] = crear_punto("Top2", L, 0, H)
    
    # 2. Crear material (función ya probada)
    resultados['material'] = crear_material_concreto(material, 30)
    
    # 3. Crear elementos frame (agregar cuando esté probada)
    # resultados['col1'] = crear_columna(...)
    
    return resultados

# Probar la función combinada
portico = crear_portico_simple(6, 3, "COL40x40", "H30")
print(portico)
```

---

## 4. Patrones Útiles para Jupyter

### Patrón: Celda de Limpieza

```python
# Celda: Limpiar modelo para re-probar
def limpiar_modelo():
    """Borra todo y deja modelo en blanco"""
    ret = SapModel.File.NewBlank()
    if ret == 0:
        print("🧹 Modelo limpiado")
    return ret

# Ejecutar antes de re-probar
limpiar_modelo()
```

### Patrón: Celda de Verificación Visual

```python
# Celda: Refrescar vista para ver cambios
def refrescar_vista():
    """Actualiza la vista de SAP2000"""
    SapModel.View.RefreshView(0, False)
    print("🔄 Vista actualizada")

refrescar_vista()
```

### Patrón: Wrapper con Logging

```python
# Celda: Decorator para debug
from functools import wraps

def debug_sap(func):
    """Decorator para mostrar info de funciones SAP"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"📞 Llamando: {func.__name__}")
        print(f"   Args: {args[1:]}")  # Excluir self si aplica
        resultado = func(*args, **kwargs)
        print(f"   Retorno: {resultado}")
        return resultado
    return wrapper

# Uso
@debug_sap
def mi_funcion_sap(param1, param2):
    return SapModel.XXX.YYY(param1, param2, 0, [])
```

### Patrón: Celda de Estado del Modelo

```python
# Celda: Ver estado actual del modelo
def estado_modelo():
    """Muestra resumen del modelo actual"""
    # Contar puntos
    ret_pts = SapModel.PointObj.Count()
    
    # Contar frames
    ret_frames = SapModel.FrameObj.Count()
    
    # Contar areas
    ret_areas = SapModel.AreaObj.Count()
    
    print("📊 Estado del Modelo:")
    print(f"   Puntos: {ret_pts}")
    print(f"   Frames: {ret_frames}")
    print(f"   Areas: {ret_areas}")

estado_modelo()
```

---

## 5. Estructura Recomendada del Notebook

```
📓 Mi_Modelo_SAP2000.ipynb
│
├── 🔷 Sección 1: Configuración
│   ├── Celda 1.1: Imports y conexión
│   └── Celda 1.2: Funciones de utilidad
│
├── 🔷 Sección 2: Funciones Atómicas (Sandbox)
│   ├── Celda 2.1: Prueba - Crear puntos
│   ├── Celda 2.2: Prueba - Crear materiales
│   ├── Celda 2.3: Prueba - Crear secciones
│   └── Celda 2.N: Prueba - ...
│
├── 🔷 Sección 3: Funciones Consolidadas
│   ├── Celda 3.1: Módulo de geometría
│   ├── Celda 3.2: Módulo de materiales
│   └── Celda 3.3: Módulo de cargas
│
├── 🔷 Sección 4: Pipeline Principal
│   └── Celda 4.1: Función crear_modelo_completo()
│
└── 🔷 Sección 5: Ejecución
    ├── Celda 5.1: Limpiar modelo
    ├── Celda 5.2: Ejecutar pipeline
    └── Celda 5.3: Verificar resultados
```

---

## 6. Tips Avanzados

### Usar Markdown para Documentar

Entre celdas de código, usa celdas Markdown para:
- Documentar qué hace cada función
- Anotar parámetros de la API que descubras
- Guardar notas sobre errores encontrados

### Exportar a Módulo Python

Cuando una función esté lista, muévela a un archivo `.py`:

```python
# Celda: Exportar función probada
codigo = '''
def crear_punto(SapModel, nombre, x, y, z):
    """Crea un punto en el modelo - PROBADA ✅"""
    ret = SapModel.PointObj.AddCartesian(x, y, z, "", nombre)
    return ret[0] if ret[-1] == 0 else None
'''

with open('mis_funciones_sap.py', 'a') as f:
    f.write(codigo + '\n\n')
print("📝 Función exportada a mis_funciones_sap.py")
```

### Guardar Sesión de Pruebas

```python
# Celda: Guardar log de pruebas
import json
from datetime import datetime

log_pruebas = {
    'fecha': datetime.now().isoformat(),
    'funciones_probadas': list(FUNCIONES_PROBADAS.keys()),
    'estado_modelo': {
        'puntos': SapModel.PointObj.Count(),
        'frames': SapModel.FrameObj.Count()
    }
}

with open('log_pruebas.json', 'w') as f:
    json.dump(log_pruebas, f, indent=2)
```

---

## 7. Checklist de Desarrollo

- [ ] ¿La celda de conexión funciona?
- [ ] ¿Cada función maneja el retorno como tupla?
- [ ] ¿Verifico `ret[-1] == 0` para éxito?
- [ ] ¿Uso valores dummy para parámetros ByRef?
- [ ] ¿Documento qué retorna cada función?
- [ ] ¿Tengo celda de limpieza para re-probar?
- [ ] ¿Las funciones probadas están en el diccionario?
- [ ] ¿La función orquestadora usa solo funciones probadas?

---

## Ejemplo Completo Mínimo

```python
# === CELDA 1: SETUP ===
import comtypes.client
SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
SapModel = SapObject.SapModel
print("✅ Conectado")

# === CELDA 2: FUNCIONES ATÓMICAS ===
def punto(x, y, z, nombre=""):
    ret = SapModel.PointObj.AddCartesian(x, y, z, "", nombre)
    return ret[0] if ret[-1] == 0 else None

def frame(pi, pj, nombre=""):
    ret = SapModel.FrameObj.AddByPoint(pi, pj, "", nombre)
    return ret[0] if ret[-1] == 0 else None

# === CELDA 3: PROBAR ===
p1 = punto(0, 0, 0, "A")
p2 = punto(0, 0, 3, "B")
print(f"Puntos: {p1}, {p2}")

# === CELDA 4: COMBINAR ===
f1 = frame(p1, p2, "COL1")
print(f"Frame: {f1}")

# === CELDA 5: REFRESCAR ===
SapModel.View.RefreshView(0, False)
```

---

> **Recuerda:** El poder de Jupyter está en la iteración. No intentes escribir todo de una vez. Prueba → Verifica → Integra → Repite.
