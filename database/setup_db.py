import sqlite3
import sys

# Cambia esto:
def create_database(db_name='database/cellstore.db'):
    try:
        # Conectar a la base de datos (se crea si no existe)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        print(f"[-] Conectado exitosamente a SQLite: {db_name}")

        # Activar claves foráneas (importante en SQLite para integridad)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Definición del esquema SQL completo
        sql_schema = """
        -- 1. Configuración de la Empresa (Datos CellStore)
        CREATE TABLE IF NOT EXISTS datos_empresa (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nombre TEXT NOT NULL DEFAULT 'CELL STORE TECHNOLOGY',
            direccion TEXT NOT NULL DEFAULT 'Av. independencia #27, plaza los arcos, villa cuauhtémoc',
            telefono TEXT NOT NULL DEFAULT '+52 722 158 0353',
            slogan TEXT NOT NULL DEFAULT '"Todo en una solución"' -- NUEVO: Campo de Slogan
        );

        -- Insertar datos por defecto
        INSERT OR IGNORE INTO datos_empresa (id) VALUES (1);

        -- 2. Usuarios
        -- 2. Usuarios
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1 -- NUEVO: Control de borrado lógico
        );

        -- 3. Cotizaciones (Maestro)
        CREATE TABLE IF NOT EXISTS cotizaciones_maestro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cliente_nombre TEXT NOT NULL,
            cliente_telefono TEXT NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')), 
            total_inversion REAL NOT NULL DEFAULT 0,
            total_precio_final REAL NOT NULL DEFAULT 0,
            total_ganancia REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            metodo_pago TEXT, 
            monto_adelanto REAL NOT NULL DEFAULT 0,
            monto_restante REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        -- 4. Cotizaciones (Detalle)
        CREATE TABLE IF NOT EXISTS cotizaciones_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotizacion_id INTEGER NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            trabajo_a_realizar TEXT NOT NULL,
            observaciones TEXT,
            inversion_pieza REAL NOT NULL,
            precio_cliente REAL NOT NULL,
            ganancia_neta REAL NOT NULL,
            FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones_maestro(id) ON DELETE CASCADE
        );

        -- 5. Otros Gastos
        CREATE TABLE IF NOT EXISTS otros_gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        -- 6. Displays (Enrique Luna)
        CREATE TABLE IF NOT EXISTS inventario_displays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            precio_mayorista REAL NOT NULL,
            precio_publico REAL NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        );

        -- 7. Movimientos (Log)
        CREATE TABLE IF NOT EXISTS movimientos_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            accion TEXT NOT NULL, 
            id_referencia INTEGER,
            tipo_referencia TEXT,
            fecha_hora TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        -- 8. Historial de Ventas de Displays
        CREATE TABLE IF NOT EXISTS ventas_displays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            display_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            total REAL NOT NULL,
            tipo_precio TEXT NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (display_id) REFERENCES inventario_displays(id)
        );

        -- TRIGGERS

        -- Calcular restante al insertar
        CREATE TRIGGER IF NOT EXISTS calcular_restante_insert 
        AFTER INSERT ON cotizaciones_maestro
        BEGIN
            UPDATE cotizaciones_maestro 
            SET monto_restante = NEW.total_precio_final - NEW.monto_adelanto
            WHERE id = NEW.id;
        END;

        -- Calcular restante al actualizar
        CREATE TRIGGER IF NOT EXISTS calcular_restante_update
        AFTER UPDATE OF total_precio_final, monto_adelanto ON cotizaciones_maestro
        BEGIN
            UPDATE cotizaciones_maestro 
            SET monto_restante = NEW.total_precio_final - NEW.monto_adelanto
            WHERE id = NEW.id;
        END;

        -- Log nueva cotización
        CREATE TRIGGER IF NOT EXISTS log_nueva_cotizacion
        AFTER INSERT ON cotizaciones_maestro
        BEGIN
            INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
            VALUES (NEW.usuario_id, 'Creó nueva cotización ID: ' || NEW.id, NEW.id, 'COTIZACION');
        END;

        -- Log nuevo gasto
        CREATE TRIGGER IF NOT EXISTS log_nuevo_gasto
        AFTER INSERT ON otros_gastos
        BEGIN
            INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
            VALUES (NEW.usuario_id, 'Registró gasto por $' || NEW.monto, NEW.id, 'GASTO');
        END;
        """

        # Ejecutar el script SQL
        cursor.executescript(sql_schema)
        conn.commit()
        print("[+] Base de datos y tablas creadas exitosamente.")

        # Crear un usuario de prueba (opcional, para que puedas programar el login)
                # Crear usuarios iniciales
        usuarios_iniciales = [
            ('Enrique Luna', 'joseluc0103@gmail.com', 'Cambiame123'),
            ('Yael Fernandez', 'teof37267@gmail.com', 'Cambiame123')
        ]
        
        for nombre, correo, contrasena in usuarios_iniciales:
            try:
                cursor.execute("INSERT INTO usuarios (nombre, correo, contrasena) VALUES (?, ?, ?)", 
                               (nombre, correo, contrasena))
                print(f"[+] Usuario creado: {nombre} ({correo})")
            except sqlite3.IntegrityError:
                print(f"[!] Usuario ya existe: {correo}")
                pass
        
        conn.commit()

    except sqlite3.Error as e:
        print(f"[!] Error al crear la base de datos: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()
            print("[-] Conexión a SQLite cerrada.")

if __name__ == '__main__':
    create_database()