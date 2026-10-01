import sqlite3

conn = sqlite3.connect("asistencia.db")
cursor = conn.cursor()

# Verificar si la columna password existe, si no, crear o actualizar el registro
try:
    cursor.execute("ALTER TABLE empleados ADD COLUMN password TEXT DEFAULT '1234'")
    print("Columna 'password' agregada correctamente.")
except sqlite3.OperationalError:
    # La columna ya existe
    pass

# Establecer la contraseña del administrador
cursor.execute("UPDATE empleados SET password = ? WHERE email = ?", ('admin123', 'admin@empresa.com'))
conn.commit()
conn.close()

print("🔑 Credenciales actualizadas:")
print("   Correo: admin@empresa.com")
print("   Clave:  admin123")