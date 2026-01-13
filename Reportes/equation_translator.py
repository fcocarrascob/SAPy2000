"""
UnicodeMath Builder - Sistema nativo de ecuaciones para Word.

Este módulo implementa UnicodeMath como formato nativo para ecuaciones,
eliminando la necesidad de traducción desde LaTeX.

UnicodeMath es el formato lineal nativo de Microsoft Word para ecuaciones.
Referencia: Unicode Technical Note 28 (UTN#28)
https://www.unicode.org/notes/tn28/

SINTAXIS UNICODEMATH:
- Fracciones: (numerador)/(denominador)
- Matrices: ■(a&b@c&d)
- Raíces: √(x) o √(n&x) para raíz n-ésima
- Eqarray: █(eq1@eq2@eq3) para ecuaciones alineadas
- Cases: ❴█(val1&cond1@val2&cond2) para funciones por partes
- Vectores: v⃗ o v̂
- Subíndices: x_n o x_(ab)
- Superíndices: x^2 o x^(ab)
- Texto: "texto entre comillas"
"""
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DICCIONARIO DE SÍMBOLOS UNICODEMATH
# =============================================================================
# Mapeo de comandos de autocorrección a caracteres Unicode.
# Compatible con la autocorrección de Word (ej: \alpha<espacio> → α)

UNICODEMATH_SYMBOLS = {
    # --- Letras Griegas Minúsculas ---
    '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\delta': 'δ',
    '\\epsilon': 'ε', '\\varepsilon': 'ε', '\\zeta': 'ζ', '\\eta': 'η', 
    '\\theta': 'θ', '\\vartheta': 'ϑ', '\\iota': 'ι', '\\kappa': 'κ',
    '\\lambda': 'λ', '\\mu': 'μ', '\\nu': 'ν', '\\xi': 'ξ',
    '\\pi': 'π', '\\varpi': 'ϖ', '\\rho': 'ρ', '\\varrho': 'ϱ',
    '\\sigma': 'σ', '\\varsigma': 'ς', '\\tau': 'τ', '\\upsilon': 'υ',
    '\\phi': 'φ', '\\varphi': 'ϕ', '\\chi': 'χ', '\\psi': 'ψ', '\\omega': 'ω',
    
    # --- Letras Griegas Mayúsculas ---
    '\\Gamma': 'Γ', '\\Delta': 'Δ', '\\Theta': 'Θ', '\\Lambda': 'Λ',
    '\\Xi': 'Ξ', '\\Pi': 'Π', '\\Sigma': 'Σ', '\\Upsilon': 'Υ',
    '\\Phi': 'Φ', '\\Psi': 'Ψ', '\\Omega': 'Ω',
    
    # --- Operadores de Relación ---
    '\\neq': '≠', '\\ne': '≠',           # No igual
    '\\geq': '≥', '\\ge': '≥',           # Mayor o igual
    '\\leq': '≤', '\\le': '≤',           # Menor o igual
    '\\approx': '≈',                      # Aproximadamente
    '\\equiv': '≡',                       # Equivalente
    '\\sim': '∼',                         # Similar
    '\\propto': '∝',                      # Proporcional a
    '\\ll': '≪', '\\gg': '≫',            # Mucho menor/mayor
    
    # --- Operadores Binarios ---
    '\\pm': '±', '\\mp': '∓',            # Más/menos
    '\\times': '×',                       # Multiplicación
    '\\div': '÷',                         # División
    '\\cdot': '⋅',                        # Punto medio
    '\\bullet': '•',                      # Bullet
    '\\star': '⋆',                        # Estrella
    '\\circ': '∘',                        # Composición
    '\\oplus': '⊕', '\\ominus': '⊖',     # Suma/resta en círculo
    '\\otimes': '⊗', '\\oslash': '⊘',    # Producto/división en círculo
    
    # --- Símbolos Matemáticos ---
    '\\infty': '∞',                       # Infinito
    '\\partial': '∂',                     # Derivada parcial
    '\\nabla': '∇',                       # Nabla/gradiente
    '\\forall': '∀',                      # Para todo
    '\\exists': '∃',                      # Existe
    '\\nexists': '∄',                     # No existe
    '\\in': '∈', '\\notin': '∉',         # Pertenece/no pertenece
    '\\ni': '∋',                          # Contiene
    '\\subset': '⊂', '\\supset': '⊃',    # Subconjunto/superconjunto
    '\\subseteq': '⊆', '\\supseteq': '⊇',
    '\\cup': '∪', '\\cap': '∩',          # Unión/intersección
    '\\emptyset': '∅',                    # Conjunto vacío
    '\\neg': '¬',                         # Negación
    '\\wedge': '∧', '\\vee': '∨',        # Y/O lógico
    '\\therefore': '∴', '\\because': '∵', # Por lo tanto/porque
    
    # --- Flechas ---
    '\\rightarrow': '→', '\\to': '→',    # Flecha derecha
    '\\leftarrow': '←', '\\gets': '←',   # Flecha izquierda
    '\\leftrightarrow': '↔',              # Flecha doble
    '\\Rightarrow': '⇒',                  # Implica
    '\\Leftarrow': '⇐',                   # Es implicado por
    '\\Leftrightarrow': '⇔',              # Si y solo si
    '\\uparrow': '↑', '\\downarrow': '↓', # Flechas verticales
    '\\mapsto': '↦',                      # Mapea a
    
    # --- Operadores N-arios ---
    '\\sum': '∑',                         # Sumatoria
    '\\prod': '∏',                        # Productoria
    '\\coprod': '∐',                      # Coproducto
    '\\int': '∫',                         # Integral
    '\\iint': '∬',                        # Integral doble
    '\\iiint': '∭',                       # Integral triple
    '\\oint': '∮',                        # Integral de contorno
    '\\bigcup': '⋃', '\\bigcap': '⋂',    # Unión/intersección grande
    '\\bigvee': '⋁', '\\bigwedge': '⋀',  # Or/And grande
    
    # --- Raíces (caracteres especiales) ---
    '\\sqrt': '√',                        # Raíz cuadrada
    '\\cbrt': '∛',                        # Raíz cúbica
    '\\qdrt': '∜',                        # Raíz cuarta
    
    # --- Delimitadores ---
    '\\lbrace': '❴', '\\rbrace': '❵',    # Llaves escalables
    '\\langle': '⟨', '\\rangle': '⟩',    # Ángulos
    '\\lceil': '⌈', '\\rceil': '⌉',      # Techo
    '\\lfloor': '⌊', '\\rfloor': '⌋',    # Piso
    '\\vbar': '|',                        # Barra vertical (separador)
    
    # --- Acentos/Modificadores (como comandos) ---
    '\\vec': '⃗',                         # Vector (flecha sobre)
    '\\hat': '̂',                          # Gorro
    '\\bar': '̄',                          # Barra sobre
    '\\dot': '̇',                          # Punto sobre
    '\\ddot': '̈',                         # Dos puntos sobre
    '\\tilde': '̃',                        # Tilde
    '\\overline': '¯',                    # Línea sobre
    
    # --- Símbolos Geométricos ---
    '\\angle': '∠',                       # Ángulo
    '\\measuredangle': '∡',               # Ángulo medido
    '\\perp': '⊥',                        # Perpendicular
    '\\parallel': '∥',                    # Paralelo
    '\\triangle': '△',                    # Triángulo
    '\\square': '□',                      # Cuadrado
    
    # --- Puntuación y Espaciado ---
    '\\ldots': '…',                       # Puntos suspensivos bajos
    '\\cdots': '⋯',                       # Puntos suspensivos centrados
    '\\vdots': '⋮',                       # Puntos verticales
    '\\ddots': '⋱',                       # Puntos diagonales
    '\\prime': '′',                       # Prima
    '\\dprime': '″',                      # Doble prima
    '\\degree': '°',                      # Grado
    
    # --- Caracteres Especiales UnicodeMath ---
    '\\matrix': '■',                      # Inicio de matriz
    '\\eqarray': '█',                     # Array de ecuaciones
    '\\rect': '▭',                        # Rectángulo/caja
    '\\funcapply': '⁡',                   # Aplicación de función (invisible)
}


# =============================================================================
# PALETA DE SÍMBOLOS PARA LA UI
# =============================================================================
# Organizada por categorías para el editor visual

SYMBOLS_PALETTE = {
    "Griegas Minúsculas": {
        "α": "α", "β": "β", "γ": "γ", "δ": "δ",
        "ε": "ε", "ζ": "ζ", "η": "η", "θ": "θ",
        "λ": "λ", "μ": "μ", "ν": "ν", "ξ": "ξ",
        "π": "π", "ρ": "ρ", "σ": "σ", "τ": "τ",
        "φ": "φ", "χ": "χ", "ψ": "ψ", "ω": "ω"
    },
    "Griegas Mayúsculas": {
        "Γ": "Γ", "Δ": "Δ", "Θ": "Θ", "Λ": "Λ",
        "Ξ": "Ξ", "Π": "Π", "Σ": "Σ", "Φ": "Φ",
        "Ψ": "Ψ", "Ω": "Ω"
    },
    "Operadores": {
        "≠": "≠", "≥": "≥", "≤": "≤",
        "≈": "≈", "±": "±", "×": "×",
        "÷": "÷", "⋅": "⋅", "∞": "∞"
    },
    "Flechas": {
        "→": "→", "←": "←", "↔": "↔",
        "⇒": "⇒", "⇔": "⇔", "↦": "↦"
    },
    "N-arios": {
        "∑": "∑", "∏": "∏", "∫": "∫",
        "∬": "∬", "∮": "∮"
    },
    "Estructuras": {
        "(a)/(b)": "fracción",
        "√()": "raíz",
        "√(n&x)": "raíz n",
        "\\matrix(a&b@c&d)": "matriz",
        "█(eq1@eq2)": "eqarray",
        "❴█()": "cases"
    }
}


# =============================================================================
# TEMPLATES DE ECUACIONES EN UNICODEMATH
# =============================================================================
# Plantillas predefinidas para ingeniería estructural

EQUATION_TEMPLATES = {
    "Factor R* (NCh2369)": {
        "code": "R^*=❴█(1&R=1@R&R≠1, T^*≥C_r T_1@1.5+(R-1.5)(T^*)/(C_r T_1)&R≠1, T^*<C_r T_1)",
        "description": "Factor de modificación de respuesta estructural"
    },
    "Espectro Horizontal": {
        "code": "S_a(T_H)=(I⋅S_(aH)(T_H))/(R^*)⋅((0.05)/(ξ))^0.4",
        "description": "Espectro de diseño horizontal NCh2369"
    },
    "Espectro Vertical": {
        "code": "S_a(T_V)=(I⋅S_(aV)(T_V))/(R_V)⋅((0.05)/(ξ_V))^0.4",
        "description": "Espectro de diseño vertical NCh2369"
    },
    "Combinación LRFD": {
        "code": "U=1.2D+1.6L+0.5(L_r \" or \" S \" or \" R)",
        "description": "Combinación de carga LRFD típica"
    },
    "Fracción": {
        "code": "(a+b)/(c+d)",
        "description": "Plantilla de fracción"
    },
    "Raíz cuadrada": {
        "code": "√(a^2+b^2)",
        "description": "Plantilla de raíz cuadrada"
    },
    "Raíz n-ésima": {
        "code": "√(n&x)",
        "description": "Plantilla de raíz n-ésima"
    },
    "Sumatoria": {
        "code": "∑_(i=1)^n x_i",
        "description": "Sumatoria con límites"
    },
    "Integral": {
        "code": "∫_a^b f(x)dx",
        "description": "Integral definida"
    },
    "Integral doble": {
        "code": "∬_D f(x,y)dA",
        "description": "Integral doble sobre región D"
    },
    "Límite": {
        "code": "lim_(n→∞) a_n",
        "description": "Límite con notación"
    },
    "Matriz 2x2": {
        "code": "■(a&b@c&d)",
        "description": "Matriz 2x2"
    },
    "Matriz 3x3": {
        "code": "■(a&b&c@d&e&f@g&h&i)",
        "description": "Matriz 3x3"
    },
    "Matriz con paréntesis": {
        "code": "(■(a&b@c&d))",
        "description": "Matriz con paréntesis"
    },
    "Matriz con corchetes": {
        "code": "[■(a&b@c&d)]",
        "description": "Matriz con corchetes"
    },
    "Cases (2 condiciones)": {
        "code": "f(x)=❴█(valor_1&condición_1@valor_2&condición_2)",
        "description": "Función por partes con 2 casos"
    },
    "Cases (3 condiciones)": {
        "code": "f(x)=❴█(v_1&cond_1@v_2&cond_2@v_3&cond_3)",
        "description": "Función por partes con 3 casos"
    },
    "Eqarray (Sistema)": {
        "code": "█(x+1&=2@1+2+3+y&=z@(3)/(x)&=6)",
        "description": "Sistema de ecuaciones alineadas"
    },
    "Vector": {
        "code": "v⃗",
        "description": "Notación de vector con flecha"
    },
    "Vector unitario": {
        "code": "û",
        "description": "Notación de vector unitario"
    },
    "Fórmula enmarcada": {
        "code": "▭((a)/(b))",
        "description": "Fórmula con recuadro"
    },
    "Corte basal mínimo": {
        "code": "Q_(0,min)=0.25(I⋅A_r⋅S)/(g)P",
        "description": "Corte basal mínimo NCh2369"
    },
    "Corte basal máximo": {
        "code": "Q_(0,max)=2.75(I⋅A_r⋅S)/(g(R+1))⋅((0.05)/(ξ))^0.4 P",
        "description": "Corte basal máximo NCh2369"
    }
}


# =============================================================================
# CLASE PRINCIPAL: UnicodeMathBuilder
# =============================================================================

class UnicodeMathBuilder:
    """
    Constructor de expresiones UnicodeMath.
    
    Provee métodos para crear estructuras matemáticas complejas
    en sintaxis UnicodeMath nativa de Word.
    
    Uso:
        builder = UnicodeMathBuilder()
        frac = builder.fraction("a+b", "c+d")  # "(a+b)/(c+d)"
        matrix = builder.matrix([["a", "b"], ["c", "d"]])  # "■(a&b@c&d)"
    """
    
    def __init__(self):
        self._symbols = UNICODEMATH_SYMBOLS
    
    # -------------------------------------------------------------------------
    # Métodos de Construcción
    # -------------------------------------------------------------------------
    
    def fraction(self, numerator: str, denominator: str) -> str:
        """
        Crea una fracción.
        
        Args:
            numerator: Expresión del numerador
            denominator: Expresión del denominador
            
        Returns:
            str: "(numerator)/(denominator)"
        """
        return f"({numerator})/({denominator})"
    
    def sqrt(self, expression: str, index: str = None) -> str:
        """
        Crea una raíz.
        
        Args:
            expression: Expresión bajo la raíz
            index: Índice de la raíz (None para raíz cuadrada)
            
        Returns:
            str: "√(expression)" o "√(index&expression)"
        """
        if index is None:
            return f"√({expression})"
        elif index == "3":
            return f"∛({expression})"
        elif index == "4":
            return f"∜({expression})"
        else:
            return f"√({index}&{expression})"
    
    def matrix(self, rows: list) -> str:
        """
        Crea una matriz.
        
        Args:
            rows: Lista de listas con los elementos de la matriz
                  Ej: [["a", "b"], ["c", "d"]]
                  
        Returns:
            str: "\\matrix(a&b@c&d)"
        """
        row_strings = ["&".join(row) for row in rows]
        content = "@".join(row_strings)
        return f"\\matrix({content})"
    
    def pmatrix(self, rows: list) -> str:
        """Matriz con paréntesis."""
        return f"({self.matrix(rows)})"
    
    def bmatrix(self, rows: list) -> str:
        """Matriz con corchetes."""
        return f"[{self.matrix(rows)}]"
    
    def eqarray(self, equations: list) -> str:
        """
        Crea un array de ecuaciones alineadas.
        
        Args:
            equations: Lista de ecuaciones. Usar & para punto de alineación.
                       Ej: ["x+1&=2", "y&=3"]
                       
        Returns:
            str: "█(x+1&=2@y&=3)"
        """
        content = "@".join(equations)
        return f"█({content})"
    
    def cases(self, conditions: list) -> str:
        """
        Crea una función por partes (cases).
        
        Args:
            conditions: Lista de tuplas (valor, condición)
                        Ej: [("0", "x<0"), ("x", "x≥0")]
                        
        Returns:
            str: "❴█(0&x<0@x&x≥0)"
        """
        rows = [f"{val}&{cond}" for val, cond in conditions]
        content = "@".join(rows)
        return f"❴█({content})"
    
    def subscript(self, base: str, sub: str) -> str:
        """
        Crea un subíndice.
        
        Args:
            base: Expresión base
            sub: Expresión del subíndice
            
        Returns:
            str: "base_sub" o "base_(sub)" si sub tiene múltiples caracteres
        """
        if len(sub) == 1:
            return f"{base}_{sub}"
        return f"{base}_({sub})"
    
    def superscript(self, base: str, sup: str) -> str:
        """
        Crea un superíndice.
        
        Args:
            base: Expresión base
            sup: Expresión del superíndice
            
        Returns:
            str: "base^sup" o "base^(sup)" si sup tiene múltiples caracteres
        """
        if len(sup) == 1:
            return f"{base}^{sup}"
        return f"{base}^({sup})"
    
    def subsup(self, base: str, sub: str, sup: str) -> str:
        """Crea subíndice y superíndice combinados."""
        sub_part = f"_{sub}" if len(sub) == 1 else f"_({sub})"
        sup_part = f"^{sup}" if len(sup) == 1 else f"^({sup})"
        return f"{base}{sub_part}{sup_part}"
    
    def nary(self, operator: str, lower: str = None, upper: str = None, 
             expression: str = None) -> str:
        """
        Crea un operador n-ario (suma, integral, etc).
        
        Args:
            operator: Símbolo del operador (∑, ∫, ∏, etc)
            lower: Límite inferior
            upper: Límite superior
            expression: Expresión a operar
            
        Returns:
            str: Operador con límites y expresión
        """
        result = operator
        if lower:
            result += f"_({lower})" if len(lower) > 1 else f"_{lower}"
        if upper:
            result += f"^({upper})" if len(upper) > 1 else f"^{upper}"
        if expression:
            result += f" {expression}"
        return result
    
    def sum(self, lower: str = None, upper: str = None, expr: str = None) -> str:
        """Sumatoria: ∑"""
        return self.nary("∑", lower, upper, expr)
    
    def integral(self, lower: str = None, upper: str = None, expr: str = None) -> str:
        """Integral: ∫"""
        return self.nary("∫", lower, upper, expr)
    
    def product(self, lower: str = None, upper: str = None, expr: str = None) -> str:
        """Productoria: ∏"""
        return self.nary("∏", lower, upper, expr)
    
    def limit(self, variable: str, approaches: str, expr: str = None) -> str:
        """
        Crea un límite.
        
        Args:
            variable: Variable que tiende
            approaches: Valor al que tiende
            expr: Expresión del límite
            
        Returns:
            str: "lim_(variable→approaches) expr"
        """
        result = f"lim_({variable}→{approaches})"
        if expr:
            result += f" {expr}"
        return result
    
    def vector(self, name: str) -> str:
        """Crea un vector con flecha sobre el nombre."""
        return f"{name}⃗"
    
    def hat(self, name: str) -> str:
        """Crea un vector unitario con gorro."""
        return f"{name}̂"
    
    def overbar(self, expr: str) -> str:
        """Crea una barra sobre la expresión."""
        return f"({expr})̄"
    
    def boxed(self, expr: str) -> str:
        """Crea una expresión enmarcada."""
        return f"▭({expr})"
    
    def text(self, content: str) -> str:
        """Inserta texto literal en la ecuación."""
        return f'"{content}"'
    
    def apply_symbol(self, command: str) -> str:
        """
        Aplica un comando de símbolo y retorna el carácter Unicode.
        
        Args:
            command: Comando con backslash (ej: "\\alpha")
            
        Returns:
            str: Carácter Unicode correspondiente o el comando original si no existe
        """
        return self._symbols.get(command, command)
    
    def expand_symbols(self, expression: str) -> str:
        """
        Expande todos los comandos de símbolos en una expresión.
        
        Args:
            expression: Expresión con comandos \\symbol
            
        Returns:
            str: Expresión con símbolos Unicode
        """
        result = expression
        # Ordenar por longitud descendente para evitar reemplazos parciales
        sorted_symbols = sorted(self._symbols.items(), key=lambda x: -len(x[0]))
        for cmd, char in sorted_symbols:
            result = result.replace(cmd, char)
        return result
    
    # -------------------------------------------------------------------------
    # Métodos de Validación
    # -------------------------------------------------------------------------
    
    def validate(self, expression: str) -> tuple:
        """
        Valida la sintaxis de una expresión UnicodeMath.
        
        Args:
            expression: Expresión a validar
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        errors = []
        
        # Verificar paréntesis balanceados
        if not self._check_balanced(expression, '(', ')'):
            errors.append("Paréntesis () no balanceados")
        
        if not self._check_balanced(expression, '[', ']'):
            errors.append("Corchetes [] no balanceados")
        
        # Verificar delimitadores de matriz
        matrix_opens = expression.count('■(')
        eqarray_opens = expression.count('█(')
        cases_opens = expression.count('❴█(') + expression.count('❴')
        
        # Contar paréntesis de cierre que corresponden a estructuras
        # (esto es una heurística, no perfecta)
        
        # Verificar subíndices/superíndices huérfanos
        if re.search(r'[_^]\s*$', expression):
            errors.append("Subíndice o superíndice sin contenido al final")
        
        # Verificar fracciones mal formadas
        if re.search(r'\)\s*/\s*$', expression):
            errors.append("Fracción incompleta (falta denominador)")
        
        if re.search(r'^\s*/\s*\(', expression):
            errors.append("Fracción incompleta (falta numerador)")
        
        # Verificar comillas balanceadas para texto
        quote_count = expression.count('"')
        if quote_count % 2 != 0:
            errors.append('Comillas " no balanceadas para texto')
        
        if errors:
            return False, "; ".join(errors)
        
        return True, ""
    
    def _check_balanced(self, text: str, open_char: str, close_char: str) -> bool:
        """Verifica que los delimitadores estén balanceados."""
        count = 0
        for char in text:
            if char == open_char:
                count += 1
            elif char == close_char:
                count -= 1
            if count < 0:
                return False
        return count == 0
    
    # -------------------------------------------------------------------------
    # Métodos de Ayuda
    # -------------------------------------------------------------------------
    
    def get_symbols_palette(self) -> dict:
        """Retorna la paleta de símbolos organizada."""
        return SYMBOLS_PALETTE
    
    def get_templates(self) -> dict:
        """Retorna los templates de ecuaciones."""
        return EQUATION_TEMPLATES
    
    def get_syntax_help(self) -> str:
        """Retorna una guía rápida de sintaxis UnicodeMath."""
        return """
SINTAXIS UNICODEMATH PARA WORD
==============================

FRACCIONES:
  (numerador)/(denominador)
  Ejemplo: (a+b)/(c+d)

RAÍCES:
  √(x)           Raíz cuadrada
  √(n&x)         Raíz n-ésima (n va primero)
  ∛(x)           Raíz cúbica
  ∜(x)           Raíz cuarta

SUBÍNDICES Y SUPERÍNDICES:
  x_i            Subíndice simple
  x_(ab)         Subíndice compuesto
  x^2            Superíndice simple
  x^(ab)         Superíndice compuesto
  x_i^2          Ambos

SÍMBOLOS GRIEGOS (usar directamente):
  α β γ δ θ λ μ π σ φ ω
  Δ Σ Ω (mayúsculas)
  
  O con autocorrección: \\alpha → α

OPERADORES:
  ≠  (no igual)     ≥  (mayor igual)    ≤  (menor igual)
  ⋅  (punto)        ×  (cruz)           ±  (más/menos)
  ∞  (infinito)     ≈  (aproximado)     →  (flecha)

MATRICES:
  ■(a&b@c&d)
  
  &  separa columnas
  @  separa filas

MATRIZ CON DELIMITADORES:
  (■(a&b@c&d))     Paréntesis
  [■(a&b@c&d)]     Corchetes

EQARRAY (ecuaciones alineadas):
  █(x+1&=2@y&=3)
  
  &  marca punto de alineación
  @  separa ecuaciones

CASES (funciones por partes):
  f(x)=❴█(0&x<0@x&x≥0)
  
  ❴  llave izquierda escalable

SUMATORIAS E INTEGRALES:
  ∑_(i=1)^n x_i
  ∫_a^b f(x)dx
  ∬_D f(x,y)dA

LÍMITES:
  lim_(n→∞) a_n

VECTORES:
  v⃗             Vector (v + ⃗)
  û             Vector unitario

TEXTO EN ECUACIONES:
  "texto"        Texto entre comillas

FÓRMULAS ENMARCADAS:
  ▭((a)/(b))     Fórmula en recuadro
"""


# =============================================================================
# INSTANCIA GLOBAL Y FUNCIONES HELPER
# =============================================================================

# Instancia global para uso conveniente
builder = UnicodeMathBuilder()


def validate_equation(equation: str) -> tuple:
    """
    Función helper para validar una ecuación.
    
    Args:
        equation: Ecuación en sintaxis UnicodeMath
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    return builder.validate(equation)


def expand_symbols(equation: str) -> str:
    """
    Función helper para expandir símbolos \\command a Unicode.
    
    Args:
        equation: Ecuación con comandos \\symbol
        
    Returns:
        str: Ecuación con símbolos Unicode expandidos
    """
    return builder.expand_symbols(equation)


def get_symbols() -> dict:
    """Función helper para obtener la paleta de símbolos."""
    return builder.get_symbols_palette()


def get_templates() -> dict:
    """Función helper para obtener los templates."""
    return builder.get_templates()


def get_help() -> str:
    """Función helper para obtener la guía de sintaxis."""
    return builder.get_syntax_help()


# Compatibilidad hacia atrás (deprecated)
def translate_equation(equation: str) -> str:
    """
    DEPRECATED: En UnicodeMath nativo no se necesita traducción.
    Solo expande símbolos \\command si los hay.
    """
    return expand_symbols(equation)


# Alias para compatibilidad
translator = builder
EquationTranslator = UnicodeMathBuilder  # Alias de clase
