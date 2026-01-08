# Instrucciones para GitHub Copilot - SAP2000 API con comtypes

Estás trabajando en un proyecto de Python que interactúa con la API de SAP2000 (CSI OAPI) utilizando la librería `comtypes`.

## Reglas Críticas de Implementación

### 1. Manejo de Retornos (La Regla de Oro)
La API de SAP2000 está diseñada para lenguajes que soportan parámetros `ByRef` (como VBA o C#). En Python con `comtypes`, el comportamiento es diferente:

*   **NO** asumas que los parámetros de entrada se modifican in-place.
*   Las funciones retornan una **TUPLA** o **LISTA** que contiene todos los valores de salida definidos como `ByRef` en la documentación original, seguidos por el valor de retorno de la función.
*   **El último elemento** de la lista de retorno es SIEMPRE el código de estado (`RetCode`). `0` significa éxito.

### 2. Patrón de Código Obligatorio

**Incorrecto (Estilo VBA/C#):**
```python
# NO HACER ESTO: Asumir que ret es solo el código de error
ret = SapModel.Func(param_in, param_out)
if ret != 0: ...
```

**Correcto (Estilo Python comtypes):**
```python
# HACER ESTO: Desempaquetar o acceder por índice
# La firma en Python suele requerir pasar argumentos dummy para los parámetros de salida
ret = SapModel.Func(param_in, 0, []) 

# ret es [ValorSalida1, ValorSalida2, ..., RetCode]

if ret[-1] == 0: # Verificar éxito (último elemento)
    resultado_1 = ret[0]
    resultado_2 = ret[1]
else:
    print(f"Error en la función, código: {ret[-1]}")
```

### 3. Listas y Arrays
Los arrays retornados por `comtypes` suelen ser tuplas inmutables. Si necesitas modificarlos, conviértelos a lista explícitamente: `list(ret[0])`.

### 4. Conexión
Prefiere siempre conectarte a una instancia activa usando `comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")` en lugar de iniciar una nueva, a menos que se especifique lo contrario.
 
### 5. Organización actual del proyecto

Trabajamos por módulos; cada módulo tiene su propia GUI y su backend (interfaz y lógica separados). Este patrón permite desarrollar, probar y mantener cada parte de forma independiente.

Mantén las reglas anteriores (manejo de retornos, listas/arrays y conexión) al implementar cada módulo.

**Futuro:** se planea integrar todos los módulos en una sola ventana con pestañas para una experiencia de usuario unificada. Diseñar cada módulo con clara separación GUI/backend facilita migrar a esa interfaz con pestañas.

### 6. Documentación de la API

La documentación y ejemplos de la API de SAP2000 están disponibles en la carpeta `API` del repositorio (ver [API] (API) para más detalles).
