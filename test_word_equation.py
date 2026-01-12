import sys
import os
import time

# Add root to path so we can import Reportes
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Reportes.word_service import WordService

def test_service_fix():
    print("Probando WordService.insert_equation corregido...")
    
    service = WordService()
    print("Conectando...")
    if not service.connect():
        print("No se pudo conectar a Word.")
        return

    print("Creando documento...")
    doc = service.create_new_document()
    service.insert_text_at_cursor("Prueba Fix WordService\n", style="Normal")
    
    equations = [
        "E = mc^2",
        "a^2 + b^2 = c^2",
        "x/y" # Simple fraction
    ]
    
    # Word Linear Format uses x/y usually. 
    # Let's add a standard linear one
    equations.append("x = (-b + \\sqrt(b^2 - 4ac)) / 2a")

    for eq in equations:
        print(f"Insertando ecuación: '{eq}'")
        success = service.insert_equation(eq)
        if success:
            print("  -> Éxito")
        else:
            print("  -> Fallo")
        
        service.insert_text_at_cursor("\n")

    print("\nFin de prueba. Verifique el documento abierto.")

if __name__ == "__main__":
    test_service_fix()
