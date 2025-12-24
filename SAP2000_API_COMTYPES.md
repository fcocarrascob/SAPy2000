# SAP2000 API con comtypes - Guía de Referencia

## Conexión COM con comtypes

```python
import comtypes.client

# Conectar a instancia activa de SAP2000
sap_object = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
sap_model = sap_object.SapModel
```

## Estructura de Retorno de Funciones

### ⚠️ IMPORTANTE: Orden de los valores retornados

Cuando se llaman funciones de la API de SAP2000 via `comtypes`, los valores se retornan como **listas** (no tuplas) con la siguiente estructura:

```
[valor_salida_1, valor_salida_2, ..., valor_salida_N, codigo_retorno]
```

- **El código de retorno está SIEMPRE al final** (`ret[-1]`)
- **Los valores de salida están en orden** (`ret[0]`, `ret[1]`, etc.)
- Un código de retorno `0` indica éxito

### ❌ Patrón INCORRECTO (común en documentación)

```python
ret = model.LoadPatterns.GetNameList(num_names, names)
if ret[0] != 0:  # ERROR: ret[0] NO es el código de retorno
    return []
num_names = ret[1]  # ERROR: los índices están desplazados
names = ret[2]
```

### ✅ Patrón CORRECTO

```python
ret = model.LoadPatterns.GetNameList(num_names, names)
# Estructura: [NumberNames, NamesArray, RetCode]
if ret[-1] != 0:  # Código de retorno al FINAL
    return []
num_names = ret[0]  # Primer valor de salida
names = list(ret[1]) if ret[1] else []  # Segundo valor de salida
```

## Ejemplos por Tipo de Función

### Funciones que retornan listas de nombres

```python
# LoadPatterns.GetNameList
ret = model.LoadPatterns.GetNameList(0, [])
# ret = [NumberNames, NamesArray, RetCode]
# ret[0] = 6 (cantidad)
# ret[1] = ('DEAD', 'LIVE', ...) (tupla de nombres)
# ret[-1] = 0 (éxito)

# LoadCases.GetNameList_1 (con filtro de tipo)
ret = model.LoadCases.GetNameList_1(0, [], case_type_filter)
# ret = [NumberNames, NamesArray, RetCode]

# RespCombo.GetNameList
ret = model.RespCombo.GetNameList(0, [])
# ret = [NumberNames, NamesArray, RetCode]
```

### Funciones que retornan un solo valor

```python
# LoadPatterns.GetLoadType
ret = model.LoadPatterns.GetLoadType(name, 0)
# ret = [PatternType, RetCode]
pattern_type = ret[0] if ret[-1] == 0 else 1

# LoadPatterns.GetSelfWtMultiplier
ret = model.LoadPatterns.GetSelfWtMultiplier(name, 0.0)
# ret = [SelfWTMultiplier, RetCode]
multiplier = ret[0] if ret[-1] == 0 else 0.0

# RespCombo.GetTypeOAPI
ret = model.RespCombo.GetTypeOAPI(name, 0)
# ret = [ComboType, RetCode]
combo_type = ret[0] if ret[-1] == 0 else 0

# RespCombo.GetNote
ret = model.RespCombo.GetNote(name, "")
# ret = [Note, RetCode]
note = ret[0] if ret[-1] == 0 else ""
```

### Funciones que retornan múltiples arrays

```python
# LoadCases.GetTypeOAPI_2
ret = model.LoadCases.GetTypeOAPI_2(name, 0, 0, 0, 0, 0)
# ret = [CaseType, SubType, DesignType, DesignTypeOpt, Auto, RetCode]
case_type = ret[0] if ret[-1] == 0 else 1

# LoadCases.StaticLinear.GetLoads
ret = model.LoadCases.StaticLinear.GetLoads(name, 0, [], [], [])
# ret = [NumberLoads, LoadType, LoadName, ScaleFactor, RetCode]
if ret[-1] == 0 and ret[0] > 0:
    num_loads = ret[0]
    load_types = ret[1]    # tupla/lista
    load_names = ret[2]    # tupla/lista
    scale_factors = ret[3] # tupla/lista

# RespCombo.GetCaseList
ret = model.RespCombo.GetCaseList(name, 0, [], [], [])
# ret = [NumberItems, CNameType, CName, ScaleFactor, RetCode]
if ret[-1] == 0 and ret[0] > 0:
    num_items = ret[0]
    case_types = ret[1]
    case_names = ret[2]
    scale_factors = ret[3]
```

### Funciones que solo retornan código

```python
# LoadPatterns.Add
ret = model.LoadPatterns.Add(name, pattern_type, self_weight, add_case)
# ret = RetCode (entero directo, no lista)
if ret != 0:
    raise Error("Falló")

# RespCombo.Add
ret = model.RespCombo.Add(name, combo_type)
# ret = RetCode

# LoadCases.Delete
ret = model.LoadCases.Delete(name)
# ret = RetCode
```

## Conversión de Tipos

Los arrays retornados suelen ser tuplas. Para trabajar con ellos como listas:

```python
names = list(ret[1]) if ret[1] else []
```

## Patrón de Validación Robusto

```python
def safe_get_names(model):
    ret = model.LoadPatterns.GetNameList(0, [])
    
    # Validar estructura
    if not isinstance(ret, (list, tuple)) or len(ret) < 3:
        return []
    
    # Validar código de retorno
    if ret[-1] != 0:
        return []
    
    # Extraer y convertir
    return list(ret[1]) if ret[1] else []
```

## Resumen Visual

```
Llamada API:  model.Something.GetSomething(param1, param2)
                            ↓
Retorno:      [salida1, salida2, ..., salidaN, ret_code]
                  ↑        ↑              ↑        ↑
               ret[0]   ret[1]    ret[N-1]    ret[-1]
                                              (siempre último)
```

## Notas Adicionales

1. **Siempre usar `ret[-1]`** para el código de retorno, así el código funciona sin importar cuántos valores retorne la función.

2. **Los parámetros de entrada** que se pasan a las funciones (como `0`, `[]`) son placeholders que comtypes requiere pero serán sobrescritos por los valores de retorno.

3. **Errores comunes**: Si una función "no retorna datos", probablemente estás leyendo `ret[0]` como código de retorno cuando en realidad es el primer valor de salida.
