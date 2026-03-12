"""
UnicodeMath Builder - Sistema nativo de ecuaciones para Word.

Este módulo implementa UnicodeMath como formato nativo para ecuaciones,
eliminando la necesidad de traducción desde LaTeX.

Este archivo es la copia completa del traductor de ecuaciones (deprecated).
"""
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DICCIONARIO DE SÍMBOLOS UNICODEMATH
# =============================================================================
UNICODEMATH_SYMBOLS = {
	'\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\delta': 'δ',
	'\\epsilon': 'ε', '\\varepsilon': 'ε', '\\zeta': 'ζ', '\\eta': 'η', 
	'\\theta': 'θ', '\\vartheta': 'ϑ', '\\iota': 'ι', '\\kappa': 'κ',
	'\\lambda': 'λ', '\\mu': 'μ', '\\nu': 'ν', '\\xi': 'ξ',
	'\\pi': 'π', '\\varpi': 'ϖ', '\\rho': 'ρ', '\\varrho': 'ϱ',
	'\\sigma': 'σ', '\\varsigma': 'ς', '\\tau': 'τ', '\\upsilon': 'υ',
	'\\phi': 'φ', '\\varphi': 'ϕ', '\\chi': 'χ', '\\psi': 'ψ', '\\omega': 'ω',
	'\\Gamma': 'Γ', '\\Delta': 'Δ', '\\Theta': 'Θ', '\\Lambda': 'Λ',
	'\\Xi': 'Ξ', '\\Pi': 'Π', '\\Sigma': 'Σ', '\\Upsilon': 'Υ',
	'\\Phi': 'Φ', '\\Psi': 'Ψ', '\\Omega': 'Ω',
	'\\neq': '≠', '\\ne': '≠',           
	'\\geq': '≥', '\\ge': '≥',           
	'\\leq': '≤', '\\le': '≤',           
	'\\approx': '≈',                      
	'\\equiv': '≡',                       
	'\\sim': '∼',                         
	'\\propto': '∝',                      
	'\\ll': '≪', '\\gg': '≫',            
	'\\pm': '±', '\\mp': '∓',            
	'\\times': '×',                       
	'\\div': '÷',                         
	'\\cdot': '⋅',                        
	'\\bullet': '•',                      
	'\\star': '⋆',                        
	'\\circ': '∘',                        
	'\\oplus': '⊕', '\\ominus': '⊖',     
	'\\otimes': '⊗', '\\oslash': '⊘',    
	'\\infty': '∞',                       
	'\\partial': '∂',                     
	'\\nabla': '∇',                       
	'\\forall': '∀',                      
	'\\exists': '∃',                      
	'\\nexists': '∄',                     
	'\\in': '∈', '\\notin': '∉',         
	'\\ni': '∋',                          
	'\\subset': '⊂', '\\supset': '⊃',    
	'\\subseteq': '⊆', '\\supseteq': '⊇',
	'\\cup': '∪', '\\cap': '∩',          
	'\\emptyset': '∅',                    
	'\\neg': '¬',                         
	'\\wedge': '∧', '\\vee': '∨',        
	'\\therefore': '∴', '\\because': '∵', 
	'\\rightarrow': '→', '\\to': '→',    
	'\\leftarrow': '←', '\\gets': '←',   
	'\\leftrightarrow': '↔',              
	'\\Rightarrow': '⇒',                  
	'\\Leftarrow': '⇐',                   
	'\\Leftrightarrow': '⇔',              
	'\\uparrow': '↑', '\\downarrow': '↓', 
	'\\mapsto': '↦',                      
	'\\sum': '∑',                         
	'\\prod': '∏',                        
	'\\coprod': '∐',                      
	'\\int': '∫',                         
	'\\iint': '∬',                        
	'\\iiint': '∭',                       
	'\\oint': '∮',                        
	'\\bigcup': '⋃', '\\bigcap': '⋂',    
	'\\bigvee': '⋁', '\\bigwedge': '⋀',  
	'\\sqrt': '√',                        
	'\\cbrt': '∛',                        
	'\\qdrt': '∜',                        
	'\\lbrace': '❴', '\\rbrace': '❵',    
	'\\langle': '⟨', '\\rangle': '⟩',    
	'\\lceil': '⌈', '\\rceil': '⌉',      
	'\\lfloor': '⌊', '\\rfloor': '⌋',    
	'\\vbar': '|',                        
	'\\vec': '⃗',                         
	'\\hat': '̂',                          
	'\\bar': '̄',                          
	'\\dot': '̇',                          
	'\\ddot': '̈',                         
	'\\tilde': '̃',                        
	'\\overline': '¯',                    
	'\\angle': '∠',                       
	'\\measuredangle': '∡',               
	'\\perp': '⊥',                        
	'\\parallel': '∥',                    
	'\\triangle': '△',                    
	'\\square': '□',                      
	'\\ldots': '…',                       
	'\\cdots': '⋯',                       
	'\\vdots': '⋮',                       
	'\\ddots': '⋱',                       
	'\\prime': '′',                       
	'\\dprime': '″',                      
	'\\degree': '°',                      
	'\\matrix': '■',                      
	'\\eqarray': '█',                     
	'\\rect': '▭',                        
	'\\funcapply': '⁡',                   
}

SYMBOLS_PALETTE = {
	"Griegas Minúsculas": {
		"\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
		"\\epsilon": "ε", "\\zeta": "ζ", "\\eta": "η", "\\theta": "θ",
		"\\lambda": "λ", "\\mu": "μ", "\\nu": "ν", "\\xi": "ξ",
		"\\pi": "π", "\\rho": "ρ", "\\sigma": "σ", "\\tau": "τ",
		"\\varphi": "φ", "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω"
	},
	"Griegas Mayúsculas": {
		"\\Gamma": "Γ", "\\Delta": "Δ", "\\Theta": "Θ", "\\Lambda": "Λ",
		"\\Xi": "Ξ", "\\Pi": "Π", "\\Sigma": "Σ", "\\Phi": "Φ",
		"\\Psi": "Ψ", "\\Omega": "Ω"
	},
	"Operadores": {
		"\\neq": "≠", "\\geq": "≥", "\\leq": "≤",
		"\\approx": "≈", "\\pm": "±", "\\times": "×",
		"\\div": "÷", "\\cdot": "⋅", "\\infty": "∞"
	},
	"Flechas": {
		"\\to": "→", "\\leftarrow": "←", "\\leftrightarrow": "↔",
		"\\Rightarrow": "⇒", "\\iff": "⇔", "\\mapsto": "↦"
	},
	"N-arios": {
		"\\sum": "∑", "\\prod": "∏", "\\int": "∫",
		"\\iint": "∬", "\\oint": "∮"
	},
	"Estructuras": {
		"\\frac{a}{b}": "fracción",
		"\\sqrt{x}": "raíz",
		"\\sqrt[n]{x}": "raíz n",
		"\\begin{pmatrix}a&b\\\\c&d\\end{pmatrix}": "matriz",
		"\\begin{aligned}a&=b\\\\c&=d\\end{aligned}": "aligned",
		"\\begin{cases}x&\\text{if }y\\\\z&\\text{else}\\end{cases}": "cases"
	}
}

EQUATION_TEMPLATES = {
	"Factor R* (NCh2369)": {
		"code": "R^* = \\begin{cases} 1 & R=1 \\\\ R & R\\neq 1, T^* \\geq C_r T_1 \\\\ 1.5+(R-1.5)\\frac{T^*}{C_r T_1} & R\\neq 1, T^* < C_r T_1 \\\\ \\end{cases}",
		"description": "Factor de modificación de respuesta estructural"
	},
	"Espectro Horizontal": {
		"code": "S_a(T_H) = \\frac{I \\cdot S_{aH}(T_H)}{R^*} \\left( \\frac{0.05}{\\xi} \\right)^{0.4}",
		"description": "Espectro de diseño horizontal NCh2369"
	}
}


class UnicodeMathBuilder:
	def __init__(self):
		self._symbols = UNICODEMATH_SYMBOLS

	def fraction(self, numerator: str, denominator: str) -> str:
		return f"({numerator})/({denominator})"

	def sqrt(self, expression: str, index: str = None) -> str:
		if index is None:
			return f"√({expression})"
		elif index == "3":
			return f"∛({expression})"
		elif index == "4":
			return f"∜({expression})"
		else:
			return f"√({index}&{expression})"

	def matrix(self, rows: list) -> str:
		row_strings = ["&".join(row) for row in rows]
		content = "@".join(row_strings)
		return f"\\matrix({content})"

	def pmatrix(self, rows: list) -> str:
		return f"({self.matrix(rows)})"

	def bmatrix(self, rows: list) -> str:
		return f"[{self.matrix(rows)}]"

	def eqarray(self, equations: list) -> str:
		content = "@".join(equations)
		return f"█({content})"

	def cases(self, conditions: list) -> str:
		rows = [f"{val}&{cond}" for val, cond in conditions]
		content = "@".join(rows)
		return f"❴█({content})"

	def subscript(self, base: str, sub: str) -> str:
		if len(sub) == 1:
			return f"{base}_{sub}"
		return f"{base}_({sub})"

	def superscript(self, base: str, sup: str) -> str:
		if len(sup) == 1:
			return f"{base}^{sup}"
		return f"{base}^({sup})"

	def subsup(self, base: str, sub: str, sup: str) -> str:
		sub_part = f"_{sub}" if len(sub) == 1 else f"_({sub})"
		sup_part = f"^{sup}" if len(sup) == 1 else f"^({sup})"
		return f"{base}{sub_part}{sup_part}"

	def nary(self, operator: str, lower: str = None, upper: str = None, 
			 expression: str = None) -> str:
		result = operator
		if lower:
			result += f"_({lower})" if len(lower) > 1 else f"_{lower}"
		if upper:
			result += f"^({upper})" if len(upper) > 1 else f"^{upper}"
		if expression:
			result += f" {expression}"
		return result

	def sum(self, lower: str = None, upper: str = None, expr: str = None) -> str:
		return self.nary("∑", lower, upper, expr)

	def integral(self, lower: str = None, upper: str = None, expr: str = None) -> str:
		return self.nary("∫", lower, upper, expr)

	def product(self, lower: str = None, upper: str = None, expr: str = None) -> str:
		return self.nary("∏", lower, upper, expr)

	def limit(self, variable: str, approaches: str, expr: str = None) -> str:
		result = f"lim_({variable}→{approaches})"
		if expr:
			result += f" {expr}"
		return result

	def vector(self, name: str) -> str:
		return f"{name}⃗"

	def hat(self, name: str) -> str:
		return f"{name}̂"

	def overbar(self, expr: str) -> str:
		return f"({expr})̄"

	def boxed(self, expr: str) -> str:
		return f"▭({expr})"

	def text(self, content: str) -> str:
		return f'"{content}"'

	def apply_symbol(self, command: str) -> str:
		return self._symbols.get(command, command)

	def expand_symbols(self, expression: str) -> str:
		result = expression
		sorted_symbols = sorted(self._symbols.items(), key=lambda x: -len(x[0]))
		for cmd, char in sorted_symbols:
			result = result.replace(cmd, char)
		return result

	def validate(self, expression: str) -> tuple:
		errors = []
		if not self._check_balanced(expression, '(', ')'):
			errors.append("Paréntesis () no balanceados")
		if not self._check_balanced(expression, '[', ']'):
			errors.append("Corchetes [] no balanceados")
		if re.search(r'[_^]\s*$', expression):
			errors.append("Subíndice o superíndice sin contenido al final")
		if re.search(r'\)\s*/\s*$', expression):
			errors.append("Fracción incompleta (falta denominador)")
		if re.search(r'^\s*/\s*\(', expression):
			errors.append("Fracción incompleta (falta numerador)")
		quote_count = expression.count('"')
		if quote_count % 2 != 0:
			errors.append('Comillas " no balanceadas para texto')
		if errors:
			return False, "; ".join(errors)
		return True, ""

	def _check_balanced(self, text: str, open_char: str, close_char: str) -> bool:
		count = 0
		for char in text:
			if char == open_char:
				count += 1
			elif char == close_char:
				count -= 1
			if count < 0:
				return False
		return count == 0

	def get_symbols_palette(self) -> dict:
		return SYMBOLS_PALETTE

	def get_templates(self) -> dict:
		return EQUATION_TEMPLATES

	def get_syntax_help(self) -> str:
		return """
SINTAXIS UNICODEMATH PARA WORD
==============================

FRACCIONES:
  (numerador)/(denominador)
  Ejemplo: (a+b)/(c+d)
"""


builder = UnicodeMathBuilder()


def validate_equation(equation: str) -> tuple:
	return builder.validate(equation)


def expand_symbols(equation: str) -> str:
	return builder.expand_symbols(equation)


def get_symbols() -> dict:
	return builder.get_symbols_palette()


def get_templates() -> dict:
	return builder.get_templates()


def get_help() -> str:
	return builder.get_syntax_help()


def translate_equation(equation: str) -> str:
	return expand_symbols(equation)

translator = builder
EquationTranslator = UnicodeMathBuilder
