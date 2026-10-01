import sqlite3

conn = sqlite3.connect("asistencia.db")
cursor = conn.cursor()

# Actualizar las coordenadas de la sucursal del empleado 'PRUEBA' o todos los empleados
cursor.execute('''
    UPDATE empleados 
    SET lat_sucursal = 9.864100, lon_sucursal = -83.914100, nombre_sucursal = 'Sucursal Central'
''')

conn.commit()
conn.close()
print("✅ Coordenadas de empleados actualizadas a la ubicación actual (9.8641, -83.9141).")