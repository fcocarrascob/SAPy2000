# Diagrama de flujo: placabase_ARA.py — Interacción con API SAP2000

El siguiente diagrama muestra el flujo principal de llamadas a la API de SAP2000 desde `placabase_ARA.py`, incluyendo puntos de decisión (verificación de retorno), intentos de variantes de firma COM y bucles por centros de pernos.

```mermaid
flowchart TD
  Start([Inicio])
  H["Crear helper<br/>CreateObject SAP2000v1.Helper"]
  Q["QueryInterface -> cHelper"]
  G["GetObject<br/>CSI.SAP2000.API.SapObject"]
  SM["Obtener SapModel<br/>mySapObject.SapModel"]
  CFG["Leer config JSON<br/>placabase_ARA_config.json si existe"]
  UT["Funciones utilitarias<br/>_ret_ok, _ret_code, _created_name_from_ret"]
  PROP["Crear o asegurar propiedades de área<br/>SetShell / SetShell_1 / ensure_plate_prop"]
  LOOP["Por cada bolt_center definido"]
  AddCenter["PointObj.AddCartesian<br/>crear punto centro"]
  CreateCircle["create_circle_points<br/>PointObj.AddCartesian x N"]
  CreateOuterSquare["create_square_points outer<br/>PointObj.AddCartesian"]
  CreateInnerSquare["create_square_points inner<br/>PointObj.AddCartesian"]
  RingInner["create_ring_areas<br/>inner=circle, outer=inner_square<br/>AreaObj.AddByPoint o AddByCoord"]
  RingOuter["create_ring_areas<br/>inner=inner_square, outer=outer_square<br/>AreaObj.AddByPoint o AddByCoord"]
  LinkArea["Crear área especial A_outer_link<br/>si hay suficientes centros"]
  DivideArea["EditArea.Divide('A_outer_link', 1, 0, [], n_pernos*4, 10)"]
  REF["View.RefreshView o RefreshWindow"]
  Summary["Imprimir resumen y contadores"]
  End([Fin])

  Start --> H --> Q --> G --> SM --> UT --> CFG --> PROP --> LOOP
  LOOP --> AddCenter --> CreateCircle --> CreateOuterSquare --> CreateInnerSquare
  CreateInnerSquare --> RingInner --> RingOuter
  RingOuter --> LOOP
  LOOP --> LinkArea --> DivideArea --> REF --> Summary --> End

  subgraph CheckRet["Verificación de retorno COM"]
    C1["Comprobar retorno<br/>_ret_code o _ret_ok"]
    C2["Si rc = 0 usar nombre creado<br/>_created_name_from_ret"]
    C3["Si rc != 0 imprimir advertencia y seguir"]
    C1 --> C2
    C1 --> C3
  end
  AddCenter --> CheckRet
  CreateCircle --> CheckRet
  CreateOuterSquare --> CheckRet
  CreateInnerSquare --> CheckRet
  RingInner --> CheckRet
  RingOuter --> CheckRet


```

**Mapa rápido de funciones a nodos del diagrama**

- **Conexión y modelo:** `helper = CreateObject(...)`, `helper.QueryInterface(...)`, `helper.GetObject(...)` → nodo `H`, `Q`, `G`, `SM`.
- **Utilidades:** `_ret_ok`, `_ret_code`, `_created_name_from_ret` → nodo `UT` y `CheckRet`.
- **Configuración:** lectura de `placabase_ARA_config.json` → `CFG`.
- **Propiedades de área:** `ensure_plate_prop`, `PropArea.SetShell`, `PropArea.SetShell_1` → `PROP` y `Fallbacks`.
- **Puntos y áreas:** `PointObj.AddCartesian`, `create_circle_points`, `create_square_points`, `AreaObj.AddByPoint`, `AreaObj.AddByCoord` → `AddCenter`, `CreateCircle`, `CreateOuterSquare`, `RingInner`, `RingOuter`.
- **Edición:** `EditArea.Divide` con múltiples firmas intentadas → `DivideArea`.
- **Interfaz visual:** `SapModel.View.RefreshView`, `SapModel.View.RefreshWindow` → `REF`.
- **Resumen:** `print` finales con contadores → `Summary`.

Si quieres, puedo:

- Generar un PNG/SVG del diagrama (requiere que tengas una herramienta Mermaid instalada localmente o usar un renderer en línea). 
- Añadir más nodos detallando cada intento de firma COM con los argumentos exactos (p.ej. lista completa de `attempts` en `add_area_by_coord`).

Archivo creado: [Placa_Base/docs/placabase_ARA_flow.md](Placa_Base/docs/placabase_ARA_flow.md)
