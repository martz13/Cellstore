import sys
import os
from PySide6.QtWidgets import QApplication
from database.connection import setup_database_for_app, get_asset_path
from views.login_view import LoginWindow

def load_stylesheet(app):
    style_path = get_asset_path("styles/style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print("[!] Advertencia: No se encontró el archivo style.qss")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Prepara la base de datos (copia la original al SO si no existe)
    setup_database_for_app()
    
    # 2. Carga los estilos CSS (QSS)
    load_stylesheet(app)
    
    # 3. Inicia la ventana de Login
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec())