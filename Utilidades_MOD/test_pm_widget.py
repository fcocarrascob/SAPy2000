"""
Test rápido para verificar el widget P-M2-M3 simplificado.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Agregar el padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Utilidades_MOD.app_utils_gui import PMWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Crear widget standalone
    window = PMWidget()
    window.setWindowTitle("Test - P-M2-M3 Simplificado")
    window.resize(1200, 700)
    
    # Cargar datos de prueba automáticamente
    test_file = Path(__file__).parent / "P_M2_M3.txt"
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = f.read()
        window.txt_input.setPlainText(test_data)
        window.combo_tipo.setCurrentText("P-M3")  # Seleccionar P-M3
        print("✅ Datos de prueba cargados (formato multi-curva)")
        print("📊 Presione el botón 'Procesar y Graficar'")
        print("📝 Debería graficar automáticamente curvas 1 (0°) y 13 (180°)")
        print("")
        print("🔄 Cambie a 'P-M2' para ver curvas 7 (90°) y 19 (270°)")
    
    window.show()
    sys.exit(app.exec())
