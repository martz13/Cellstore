import sys
import os
from PySide6.QtWidgets import QApplication
from database.connection import setup_database_for_app, get_asset_path
from views.login_view import LoginWindow

def load_stylesheet(app):
    style_path = get_asset_path("styles/style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            qss_content = f.read()
        
        # 1. Obtenemos la ruta base absoluta de tus recursos
        base_path = get_asset_path("")
        
        # 2. Reemplazamos \ por / para que Qt lo entienda en Windows
        base_path_qss = base_path.replace("\\", "/")
        
        # Si la ruta base no termina en /, se la agregamos para evitar errores al concatenar
        if not base_path_qss.endswith("/"):
            base_path_qss += "/"

        # 3. Inyectamos la ruta absoluta temporal en el QSS
        # Cambiará url('assets/images...') a url('C:/Usuarios/Temp/_MEIxxx/assets/images...')
        qss_content = qss_content.replace("url('assets/", f"url('{base_path_qss}assets/")
        
        app.setStyleSheet(qss_content)
    else:
        print(f"[!] Advertencia: No se encontró el archivo style.qss en {style_path}")

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