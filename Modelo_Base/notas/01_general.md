# Modelo Base — Descripción General

Este módulo genera automáticamente un modelo base en SAP2000 con materiales,
patrones de carga, espectros sísmicos NCh2369:2025, combinaciones de carga
y secciones de frame predefinidas.

---

## 1. Unidades

El modelo se inicializa en **Tonf, m, °C** (código SAP2000 = 12).

---

## 2. Materiales

Se crean 4 materiales con propiedades completas (isotrópicas, peso/masa y diseño):

| Material   | Tipo      | E [tonf/m²]  | Fy / f'c       | Uso típico                    |
|------------|-----------|-------------- |----------------|-------------------------------|
| A36        | Acero     | 20,389,019    | Fy = 25,310    | Perfiles estructurales        |
| A500_GrB   | Acero     | 20,389,019    | Fy = 32,341    | Tubos HSS                     |
| G30        | Hormigón  | 2,641,100     | f'c = 3,059    | Fundaciones, elementos mayores|
| G25        | Hormigón  | 2,410,900     | f'c = 2,549    | Pedestales, elementos menores |

> Los valores de E, Fy, f'c están en Tonf/m² (consistente con las unidades del modelo).

---

## 3. Patrones de Carga

Se crean 12 patrones de carga:

| Patrón  | Tipo SAP2000   | Peso Propio | Descripción                      |
|---------|----------------|-------------|----------------------------------|
| DEAD    | Dead (1)       | 1.2         | Carga muerta (incluye peso propio) |
| LIVE    | Live (3)       | 0.0         | Sobrecarga de uso                |
| ROOF    | Roof (11)      | 0.0         | Sobrecarga de techo              |
| SNOW    | Snow (7)       | 0.0         | Carga de nieve                   |
| EQX     | Quake (5)      | 0.0         | Sismo dirección X                |
| EQY     | Quake (5)      | 0.0         | Sismo dirección Y                |
| EQZ     | Quake (5)      | 0.0         | Sismo dirección vertical         |
| WINDX   | Wind (6)       | 0.0         | Viento dirección X               |
| WINDY   | Wind (6)       | 0.0         | Viento dirección Y               |
| TEMP    | Temperature (10)| 0.0        | Carga de temperatura             |
| SO      | Other (8)      | 0.0         | Sobrecarga de operación (industrial) |
| SA      | Other (8)      | 0.0         | Sobrecarga de almacenamiento     |

> **Nota**: El patrón DEAD tiene `self_wt = 1.2`. Esto es solo el multiplicador
> de peso propio del patrón; no confundir con el factor de carga LRFD.

---

## 4. Secciones de Frame

Se definen secciones de ejemplo en cada categoría:

**Perfiles I (W shapes)**

| Sección   | h [m]  | b [m]  | tf [m] | tw [m] | Material |
|-----------|--------|--------|--------|--------|----------|
| W200x46   | 0.203  | 0.203  | 0.011  | 0.007  | A36      |
| W310x97   | 0.308  | 0.305  | 0.015  | 0.009  | A36      |

**Tubos HSS (rectangulares)**

| Sección        | h [m]  | b [m]  | t [m]  | Material  |
|----------------|--------|--------|--------|-----------|
| HSS100x100x6   | 0.100  | 0.100  | 0.006  | A500_GrB  |
| HSS150x150x8   | 0.150  | 0.150  | 0.008  | A500_GrB  |

**Ángulos**

| Sección    | h [m]  | b [m]  | t [m]  | Material |
|------------|--------|--------|--------|----------|
| L50x50x5   | 0.050  | 0.050  | 0.005  | A36      |
| L75x75x6   | 0.075  | 0.075  | 0.006  | A36      |

**Canales**

| Sección    | h [m]  | b [m]  | tf [m] | tw [m] | Material |
|------------|--------|--------|--------|--------|----------|
| C100x10    | 0.100  | 0.050  | 0.009  | 0.006  | A36      |
| C150x15    | 0.150  | 0.075  | 0.011  | 0.007  | A36      |

> Estas secciones son de referencia. Se deben agregar las secciones
> reales del proyecto antes del análisis.

---

## 5. Espectros Sísmicos (NCh2369:2025)

### Parámetros de entrada (definidos en la GUI)

- **Zona sísmica** (1, 2, 3) → determina A₀ (0.28, 0.42, 0.56 g)
- **Tipo de suelo** (A-E) → determina S, r, T₀, p, q, T₁
- **Factor de importancia** (I)
- **Factores R** (Rx, Ry, Rv) y amortiguamientos (ξx, ξy, ξv)

### Espectros generados

| Función           | Dirección    | Factor escala | Desplaz. período | R*             |
|-------------------|--------------|---------------|-------------------|----------------|
| SaH_{zona}{suelo} | Horizontal X | 1.0           | 1.0×T             | Sí             |
| SaH_{zona}{suelo} | Horizontal Y | 1.0           | 1.0×T             | Sí             |
| SaV_{zona}{suelo} | Vertical     | 0.7           | 1.7×T             | No (R directo) |

- **R\*** (reducción corregida): Para T < 0.16·R·T₁, se interpola linealmente de 1.5 a R.
- **Corrección por amortiguamiento**: Factor (0.05/ξ)^0.4
- Los espectros se definen como funciones `User` en SAP2000 y se asignan a Load Cases tipo Response Spectrum.
- El factor de escala del caso RS es **g = 9.81** (el espectro ya incluye R).

### Casos de carga creados

| Caso | Tipo             | Función    | Dirección | Amort. |
|------|------------------|------------|-----------|--------|
| EQX  | Response Spectrum | SaH_...    | U1        | ξx     |
| EQY  | Response Spectrum | SaH_...    | U2        | ξy     |
| EQZ  | Response Spectrum | SaV_...    | U3        | ξv     |

---

## 6. Combinaciones de Carga

### 6.1 Combinaciones NCh2369 (Regla 100/30/30)

Combinaciones lineales de los casos RS para la regla direccional:

| Combo | EQX | EQY | EQZ |
|-------|-----|-----|-----|
| E1    | 1.0 | 0.3 | 0.3 |
| E2    | 0.3 | 1.0 | 0.3 |
| E3    | 0.3 | 0.3 | 1.0 |

### 6.2 Combinaciones LRFD

Incluyen los 7 casos básicos de NCh3171 más combinaciones industriales NCh2369:

| Caso | Descripción                           | Variantes        |
|------|---------------------------------------|------------------|
| 1    | 1.4D                                  | ±T               |
| 2    | 1.2D + 1.6L + 0.5(R o S)             | R/S, ±T          |
| 3a   | 1.2D + 1.6(R o S) + L                | R/S, ±T          |
| 3b   | 1.2D + 1.6(R o S) + 0.8W             | R/S, ±WX/WY, ±T  |
| 4    | 1.2D + 1.6W + L + 0.5(R o S)         | R/S, ±WX/WY, ±T  |
| 6    | 0.9D + 1.6W                           | ±WX/WY, ±T       |
| NCh  | 1.2D + 0.25L + SO + SA ± E(1,2,3)    | ±E, ±T           |
| NCh  | 0.9D + SA ± E(1,2,3)                  | ±E, ±T           |

### 6.3 Combinaciones ASD

| Caso | Descripción                           | Variantes          |
|------|---------------------------------------|--------------------|
| 1    | D                                     | ±T                 |
| 2    | D + L                                 | ±T                 |
| 3    | D + (R o S)                           | R/S, ±T            |
| 4    | D + 0.75L + 0.75(R o S)              | R/S, ±T            |
| 5a   | D + W                                 | ±WX/WY, ±T         |
| 6a   | D + 0.75W + 0.75L + 0.75(R o S)      | R/S, ±WX/WY, ±T   |
| 7    | 0.6D + W                              | ±WX/WY, ±T         |
| NCh  | D + 0.1875L + 0.75SO + 0.75SA ± 0.7E | ±E(1,2,3), ±T     |
| NCh  | D + 0.75SA ± 0.7E                     | ±E(1,2,3), ±T     |

### 6.4 Envolventes

| Envolvente | Tipo     | Contenido                       |
|------------|----------|---------------------------------|
| ENV_LRFD   | Envelope | Todas las combinaciones LRFD    |
| ENV_ASD    | Envelope | Todas las combinaciones ASD     |

> Las combinaciones LRFD y ASD se marcan automáticamente como
> combos de diseño para acero y hormigón en SAP2000.

---

## 7. Resumen del Proceso

El backend ejecuta los siguientes pasos en orden:

1. Inicializar modelo nuevo (Tonf-m-C)
2. Crear archivo en blanco
3. Configurar materiales (A36, A500_GrB, G30, G25)
4. Crear 12 patrones de carga
5. Definir secciones de frame de ejemplo
6. Calcular y asignar espectros sísmicos (H-X, H-Y, V)
7. Crear combinaciones (NCh + LRFD + ASD)
8. Crear envolventes (ENV_LRFD, ENV_ASD)

> **Importante**: El modelo se crea EN BLANCO (sin geometría).
> La grilla, elementos y cargas se deben definir manualmente
> después de ejecutar el Modelo Base.
