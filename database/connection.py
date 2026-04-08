import os
import sys
import sqlite3

# Importamos tu función creadora de la base de datos
from database.setup_db import create_database, actualizar_base_datos

def get_asset_path(relative_path):
    """Devuelve la ruta absoluta a los recursos (imágenes, estilos)."""
    try:
        base_path = sys._MEIPASS # Ruta temporal de PyInstaller
    except Exception:
        # Si estamos en desarrollo, subimos un nivel desde la carpeta 'database'
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

def get_db_path():
    """Devuelve la ruta de la BD con permisos de escritura del SO."""
    if sys.platform == 'win32':
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    else:
        app_data = os.path.join(os.path.expanduser('~'), '.local', 'share')
    
    db_dir = os.path.join(app_data, 'CellStoreApp')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'cellstore.db')

def setup_database_for_app():
    """Ejecuta el script SQL para crear la BD si no existe, o la actualiza si ya existe."""
    ruta_destino = get_db_path()
    
    if not os.path.exists(ruta_destino):
        print(f"[*] La base de datos no existe en el sistema. Creando una nueva...")
        create_database(ruta_destino)
        print(f"[-] Base de datos generada y lista en: {ruta_destino}")
    else:
        # SI EL ARCHIVO YA EXISTE, APLICAMOS LAS MIGRACIONES SIN BORRAR NADA
        print(f"[*] Base de datos encontrada. Comprobando actualizaciones...")
        actualizar_base_datos(ruta_destino)
        print(f"[-] Base de datos verificada y actualizada (si aplicaba).")

def get_connection():
    """Retorna la conexión a la base de datos escribible."""
    return sqlite3.connect(get_db_path())