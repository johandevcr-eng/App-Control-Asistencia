import math

def calcular_distancia_metros(lat1, lon1, lat2, lon2):
    """Calcula la distancia en metros entre dos puntos geográficos (Haversine)."""
    R = 6371000.0  # Radio de la Tierra en metros

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def validar_distancia(lat_usuario, lon_usuario, lat_sucursal, lon_sucursal, radio_tolerancia_m=150):
    """
    Evalúa si la ubicación del usuario está dentro del radio de tolerancia en metros
    respecto a la sucursal.
    """
    distancia_m = calcular_distancia_metros(lat_usuario, lon_usuario, lat_sucursal, lon_sucursal)
    es_valido = distancia_m <= radio_tolerancia_m
    return es_valido, distancia_m