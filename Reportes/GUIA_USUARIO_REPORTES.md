# Guía de Usuario: Generador de Memorias y Reportes

Este módulo permite generar memorias de cálculo profesionales en Microsoft Word integrando datos de SAP2000 y una librería de contenido técnico predefinido.

## Características Clave

1.  **Templates Inteligentes**: Genera la estructura completa del documento (portada, capítulos) con un clic.
2.  **Conexión en Vivo con SAP2000**: Extrae tablas (Materiales, Patrones, Secciones) al instante.
3.  **Librería de Snippets**: Base de datos de párrafos y fórmulas reutilizables.
4.  **Editor de Ecuaciones Nativo**: Escribe fórmulas matemáticas complejas usando sintaxis UnicodeMath y las visualiza perfectamente en Word.

---

## Interfaz Principal

La pestaña "Memorias (Word)" se divide en tres secciones:

### 1. Generar Estructura Base
Selecciona un **Template** (archivo `.json`) y haz clic en **"Generar Documento Nuevo"**. Esto abrirá Word y creará el "esqueleto" del informe.
*   **Gestión de Templates**: Puedes añadir tus propias plantillas en la carpeta `Reportes/templates/`.

### 2. Datos desde SAP2000
Botones rápidos para insertar tablas resumen extraídas directamente del modelo abierto en SAP2000.
*   **Materiales**: Propiedades de materiales definidos.
*   **Secc. Frame**: Listado de perfiles utilizados.
*   **Patrones Carga**: Definiciones de carga estática.
*   **Combinaciones**: Resumen de combos de diseño.

*Nota: La inserción ocurre en la posición actual del cursor en Word.*

### 3. Librería de Contenido (Snippets)
Aquí gestionas bloques de conocimiento reutilizables (definiciones sísmicas, fórmulas normativas, descripciones de carga).

*   **Categoría**: Filtra los snippets (ej: "Cargas Estáticas", "Diseño Sísmico").
*   **Lista**: Selecciona un elemento.
*   **Insertar en Cursor**: Pega el contenido en Word.
*   **Editar/Nuevo/Eliminar**: Gestiona tu librería directamente desde la app.

---

## Editor de Snippets y Ecuaciones

Al crear o editar un snippet, accedes a un potente editor por bloques.

### Tipos de Bloque
*   **Heading**: Títulos y subtítulos (Niveles 1-6).
*   **Text**: Párrafos de texto normal.
    *   **Tip**: Puedes escribir ecuaciones dentro del texto ("Inline") encerrándolas entre signos peso. Ejemplo: `La tensión $ \sigma $ es máxima.`
*   **Equation**: Bloque exclusivo para fórmulas matemáticas centradas.
*   **Table**: Tablas de datos con encabezados y filas editables. Permite agregar/eliminar filas y columnas dinámicamente.

### Uso del "Ribbon" de Ecuaciones
El editor cuenta con una barra de herramientas visual para insertar estructuras matemáticas sin memorizar códigos:

*   **Estructuras**: Fracciones, Raíces, Potencias, Paréntesis.
*   **Cálculo**: Sumatorias, Integrales, Límites.
*   **Operadores**: Símbolos de relación, flechas, lógica.
*   **Matrices**: Plantillas para matrices, vectores y sistemas de ecuaciones.

### Sintaxis UnicodeMath
El sistema usa **UnicodeMath** (estándar de Word). Aunque el Ribbon lo hace automático, puedes escribir manualmente:

| Estructura | Código | Resultado Visual |
| :--- | :--- | :--- |
| Fracción | `(a)/(b)` | $\frac{a}{b}$ |
| Raíz | `\sqrt(x)` o `√(x)` | $\sqrt{x}$ |
| Potencia | `x^2` | $x^2$ |
| Subíndice | `x_i` | $x_i$ |
| Matriz | `\matrix(1&0@0&1)` | $\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$ |
| Griega | `\alpha`, `\beta`, `\Sigma` | $\alpha, \beta, \Sigma$ |

---

## Gestión de Archivos

*   **Librería**: Los snippets se guardan en `Reportes/library/*.json`.
*   **Backups**: Antes de cualquier modificación o eliminación, el sistema crea una copia de seguridad en `Reportes/library/.backups/`.
