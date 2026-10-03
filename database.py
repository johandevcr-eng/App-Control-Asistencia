import sqlite3

def conectar():
    return sqlite3.connect("asistencia.db")

def init_db():
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Tabla de Sucursales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sucursales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            radio_m INTEGER DEFAULT 150
        )
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO sucursales (nombre, latitud, longitud, radio_m)
        VALUES ('Sede OSARE', 9.850015, -83.904938, 200)
    ''')

    # 2. Tabla de Empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            email TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            password TEXT NOT NULL DEFAULT '1234',
            lat_sucursal REAL NOT NULL,
            lon_sucursal REAL NOT NULL,
            nombre_sucursal TEXT,
            rol TEXT CHECK(rol IN ('Admin', 'Empleado')) NOT NULL,
            tipo_corte TEXT DEFAULT 'Quincenal',
            tipo_turno TEXT DEFAULT 'Diurno (8h)',
            marcas_diarias INTEGER DEFAULT 2
        )
    ''')
    
    # Migraciones para agregar columnas si la tabla ya existía
    columnas_nuevas = [
        ("tipo_corte", "TEXT DEFAULT 'Quincenal'"),
        ("tipo_turno", "TEXT DEFAULT 'Diurno (8h)'"),
        ("marcas_diarias", "INTEGER DEFAULT 2")
    ]
    for col, decl in columnas_nuevas:
        try:
            cursor.execute(f"ALTER TABLE empleados ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass # La columna ya existe

    cursor.execute('''
        INSERT OR IGNORE INTO empleados (email, nombre, password, lat_sucursal, lon_sucursal, nombre_sucursal, rol, tipo_corte, tipo_turno, marcas_diarias)
        VALUES ('admin@empresa.com', 'Administrador', 'admin123', 9.850015, -83.904938, 'Sede OSARE', 'Admin', 'Quincenal', 'Diurno (8h)', 2)
    ''')
    
    # 3. Tabla de Asistencia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            fecha_hora TEXT,
            tipo TEXT,
            latitud REAL,
            longitud REAL,
            valido_gps INTEGER,
            foto_path TEXT,
            FOREIGN KEY(email) REFERENCES empleados(email)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de datos inicializada correctamente con campos de planilla y turnos.")