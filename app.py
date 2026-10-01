import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from database import conectar, init_db
from geo_utils import validar_distancia

# set_page_config debe ser el primer comando de Streamlit
st.set_page_config(
    page_title="Control de Asistencia OSARE", 
    page_icon="📍", 
    layout="wide",
    initial_sidebar_state="expanded"
)


ZONA_CR = ZoneInfo("America/Costa_Rica")

# Inicialización
init_db()
if not os.path.exists("fotos_fichaje"):
    os.makedirs("fotos_fichaje")

# --- INYECCIÓN DE ESTILOS CSS PARA OPTIMIZACIÓN MÓVIL Y UX ---
st.markdown("""
    <style>
    /* Estilos generales y tipografía */
    .stApp {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Tarjetas de métricas y contenedores ordenados */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
    }
    
    /* Ajustes para botones principales móviles */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }

    /* Tablas con scroll horizontal suave en móviles */
    div[data-testid="stDataFrame"] {
        width: 100%;
        overflow-x: auto;
    }

    /* Reducir márgenes superiores en móviles */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTENTICACIÓN Y CONTROL DE SESIÓN ---
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = None

st.sidebar.title("🔐 Sesión de Usuario")

# Si el usuario aún no ha iniciado sesión
if st.session_state.usuario_autenticado is None:
    modo = st.sidebar.radio("Modo de acceso:", ["📲 Marcar Asistencia", "⚙️ Administración"])

    if modo == "📲 Marcar Asistencia":
        conn = conectar()
        df_empleados = pd.read_sql_query("SELECT email, nombre FROM empleados WHERE rol = 'Empleado'", conn)
        conn.close()

        if df_empleados.empty:
            st.warning("No hay empleados registrados.")
        else:
            usuario_sel = st.sidebar.selectbox("Selecciona tu cuenta:", df_empleados["email"].tolist())
            pass_ingresada = st.sidebar.text_input("Contraseña:", type="password")

            if st.sidebar.button("Ingresar a Fichar", type="primary", width="stretch"):
                conn = conectar()
                res = pd.read_sql_query("SELECT * FROM empleados WHERE email = ? AND password = ?", conn, params=(usuario_sel, pass_ingresada))
                conn.close()

                if not res.empty:
                    st.session_state.usuario_autenticado = usuario_sel
                    st.session_state.datos_user = res.iloc[0]
                    st.session_state.rol_usuario = "Empleado"
                    st.rerun()
                else:
                    st.sidebar.error("Contraseña incorrecta.")

    elif modo == "⚙️ Administración":
        admin_email = st.sidebar.text_input("Correo Admin:")
        admin_pass = st.sidebar.text_input("Contraseña Admin:", type="password")

        if st.sidebar.button("Acceder a Panel", type="primary", width="stretch"):
            conn = conectar()
            res = pd.read_sql_query("SELECT * FROM empleados WHERE email = ? AND password = ? AND rol = 'Admin'", conn, params=(admin_email, admin_pass))
            conn.close()

            if not res.empty:
                st.session_state.usuario_autenticado = admin_email
                st.session_state.datos_user = res.iloc[0]
                st.session_state.rol_usuario = "Admin"
                st.rerun()
            else:
                st.sidebar.error("Credenciales de administrador inválidas.")

    st.stop()

# --- SESIÓN ACTIVA ---
datos_user = st.session_state.datos_user
usuario_sel = st.session_state.usuario_autenticado
rol_usuario = st.session_state.rol_usuario

st.sidebar.success(f"👤 **{datos_user['nombre']}**\n\n🛡️ **Rol:** {rol_usuario}")

if st.sidebar.button("🚪 Cerrar Sesión", width="stretch"):
    st.session_state.usuario_autenticado = None
    st.session_state.rol_usuario = None
    st.session_state.datos_user = None
    st.rerun()

# --- MENÚ DE NAVEGACIÓN SEGÚN ROL (TAREA 1) ---
if rol_usuario == "Admin":
    opciones_menu = ["📊 Dashboard Auditoría", "👥 Gestión de Sucursales y Empleados"]
else:
    opciones_menu = ["📍 Marcar Fichaje"]

seccion = st.sidebar.radio("Navegación:", opciones_menu)

# ==========================================
# SECCIÓN 1: MARCAR FICHAJE (EXCLUSIVO EMPLEADOS)
# ==========================================
if seccion == "📍 Marcar Fichaje":
    st.title("📲 Registro de Asistencia")
    st.caption("Verifica tu tipo de fichaje y asegúrate de dar permisos a la cámara y al GPS.")
    
    tipo_registro = st.radio("Tipo de Fichaje:", ["Entrada", "Salida"], horizontal=True)
    foto = st.camera_input("Toma tu fotografía para fichar")
    
    loc = get_geolocation()
    lat_actual, lon_actual = None, None
    
    if loc and 'coords' in loc:
        lat_actual = loc['coords']['latitude']
        lon_actual = loc['coords']['longitude']
        st.success(f"🌐 GPS Detectado: `{lat_actual:.6f}, {lon_actual:.6f}`")
    else:
        st.warning("⚠️ Permite el acceso a la ubicación en tu navegador/celular para continuar.")

    if st.button("Confirmar Marcación", type="primary", width="stretch"):
        if foto is None:
            st.error("Es obligatorio tomar la fotografía antes de fichar.")
        elif lat_actual is None or lon_actual is None:
            st.error("Ubicación GPS no detectada. Asegúrate de activar el GPS.")
        else:
            conn = conectar()
            query_suc = '''
                SELECT s.latitud, s.longitud, s.radio_m 
                FROM empleados e
                LEFT JOIN sucursales s ON e.nombre_sucursal = s.nombre
                WHERE e.email = ?
            '''
            res_suc = pd.read_sql_query(query_suc, conn, params=(usuario_sel,))
            conn.close()

            if not res_suc.empty and pd.notnull(res_suc.iloc[0]["latitud"]):
                lat_suc = res_suc.iloc[0]["latitud"]
                lon_suc = res_suc.iloc[0]["longitud"]
                radio_permitido = res_suc.iloc[0]["radio_m"]
            else:
                lat_suc = datos_user["lat_sucursal"]
                lon_suc = datos_user["lon_sucursal"]
                radio_permitido = 150

            es_valido, dist_m = validar_distancia(
                lat_actual, lon_actual, 
                lat_suc, lon_suc,
                radio_tolerancia_m=radio_permitido
            )
            
            timestamp = datetime.now(ZONA_CR).strftime("%Y%m%d_%H%M%S")
            nombre_foto = f"{usuario_sel}_{timestamp}.jpg"
            ruta_foto = os.path.join("fotos_fichaje", nombre_foto)
            
            with open(ruta_foto, "wb") as f:
                f.write(foto.getbuffer())
            
            fecha_hora_str = datetime.now(ZONA_CR).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO asistencia (email, fecha_hora, tipo, latitud, longitud, valido_gps, foto_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (usuario_sel, fecha_hora_str, tipo_registro, lat_actual, lon_actual, 1 if es_valido else 0, ruta_foto))
            conn.commit()
            conn.close()
            
            if es_valido:
                st.success(f"✅ Marcación registrada DENTRO DE ZONA (A {dist_m:.1f} m de la sucursal).")
            else:
                st.error(f"🚨 Marcación registrada FUERA DE ZONA (A {dist_m:.1f} m de la sucursal. Tolerancia: {radio_permitido}m).")

# ==========================================
# SECCIÓN 2: DASHBOARD AUDITORÍA (ADMIN)
# ==========================================
elif seccion == "📊 Dashboard Auditoría":
    st.title("📊 Dashboard de Control de Asistencia")
    
    conn = conectar()
    query = '''
        SELECT a.id, e.nombre, a.fecha_hora, a.tipo, a.valido_gps, a.latitud, a.longitud, a.foto_path
        FROM asistencia a 
        JOIN empleados e ON a.email = e.email
        ORDER BY a.id DESC
    '''
    df_asistencia = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_asistencia.empty:
        df_asistencia["Estado Zona"] = df_asistencia["valido_gps"].map({1: "🟢 Dentro de Zona", 0: "🔴 Fuera de Zona"})
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Total de Fichajes", len(df_asistencia))
        with col_m2:
            dentro_m = len(df_asistencia[df_asistencia["valido_gps"] == 1])
            st.metric("Dentro de Zona", f"{dentro_m} ({(dentro_m/len(df_asistencia))*100:.0f}%)")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Gráfico de Cumplimiento")
            st.bar_chart(df_asistencia["Estado Zona"].value_counts())
            
        with col2:
            st.subheader("Mapa de Geolocalización de Fichajes")
            
            # MAPA FOLIUM CON PUNTOS VERDES Y ROJOS (TAREA 2 & TAREA 4)
            lat_centro = df_asistencia["latitud"].mean()
            lon_centro = df_asistencia["longitud"].mean()
            
            m_audit = folium.Map(
                location=[lat_centro, lon_centro], 
                zoom_start=13,
                scrollWheelZoom=False  # Permite hacer scroll por la página sin atascarse
            )
            
            for _, row in df_asistencia.iterrows():
                # TAREA 4: Verde si está dentro de zona, Rojo si está fuera
                color_punto = "#28a745" if row["valido_gps"] == 1 else "#dc3545"
                texto_estado = "DENTRO DE ZONA" if row["valido_gps"] == 1 else "FUERA DE ZONA"
                
                popup_html = f"""
                <div style='font-family: sans-serif; font-size: 12px;'>
                    <b>Empleado:</b> {row['nombre']}<br>
                    <b>Tipo:</b> {row['tipo']}<br>
                    <b>Hora:</b> {row['fecha_hora']}<br>
                    <b>Estado:</b> <span style='color:{color_punto}; font-weight:bold;'>{texto_estado}</span>
                </div>
                """
                
                folium.CircleMarker(
                    location=[row["latitud"], row["longitud"]],
                    radius=8,
                    color=color_punto,
                    fill=True,
                    fill_color=color_punto,
                    fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=250)
                ).add_to(m_audit)
            
            # TAREA 2: Ajuste de dimensión del mapa para móviles
            st_folium(m_audit, height=300, width="100%", key="mapa_audit")
            
        st.subheader("Auditoría de Fichajes")
        st.dataframe(
            df_asistencia[["id", "nombre", "fecha_hora", "tipo", "Estado Zona", "latitud", "longitud"]], 
            width="stretch"
        )
        
        st.divider()
        st.subheader("📸 Ver Fotografía de Fichaje")
        id_sel = st.selectbox("Selecciona ID de Marcación para inspeccionar:", df_asistencia["id"].tolist())
        row_foto = df_asistencia[df_asistencia["id"] == id_sel].iloc[0]
        
        if row_foto["foto_path"] and os.path.exists(row_foto["foto_path"]):
            st.image(row_foto["foto_path"], caption=f"Fotografía de {row_foto['nombre']} - {row_foto['fecha_hora']}", width=320)
        else:
            st.info("No hay imagen asociada a esta marcación.")
    else:
        st.info("No hay registros de asistencia disponibles.")

# ==========================================
# SECCIÓN 3: GESTIÓN DE SUCURSALES Y EMPLEADOS (ADMIN)
# ==========================================
elif seccion == "👥 Gestión de Sucursales y Empleados":
    st.title("👥 Gestión de Sucursales y Empleados")
    
    tab_sucursales, tab_empleados = st.tabs(["🏬 Configurar Sucursal Fija", "👤 Registrar Empleado"])
    
    # -------------------------------------------------------------
    # TAB 1: SUCURSALES FIJAS
    # -------------------------------------------------------------
    with tab_sucursales:
        st.subheader("Configurar Nueva Sede")
        
        if "lat_sucursal_nueva" not in st.session_state:
            st.session_state.lat_sucursal_nueva = 9.850015
        if "lon_sucursal_nueva" not in st.session_state:
            st.session_state.lon_sucursal_nueva = -83.904938

        col_map, col_form_suc = st.columns([1.3, 1])
        
        with col_map:
            st.caption("Haz clic en el mapa para ubicar la posición fija de la sucursal:")
            m = folium.Map(
                location=[st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva], 
                zoom_start=15,
                scrollWheelZoom=False  # TAREA 2: Previene interrupciones al scrollear en celular
            )
            folium.Marker(
                [st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva],
                popup="Ubicación de Sede",
                icon=folium.Icon(color="red", icon="building", prefix="fa")
            ).add_to(m)
            
            # TAREA 2: Altura contenida para pantallas móviles
            map_data = st_folium(m, height=280, width="100%", key="mapa_sedes")
            
            if map_data and map_data.get("last_clicked"):
                n_lat = map_data["last_clicked"]["lat"]
                n_lon = map_data["last_clicked"]["lng"]
                if round(n_lat, 6) != round(st.session_state.lat_sucursal_nueva, 6) or round(n_lon, 6) != round(st.session_state.lon_sucursal_nueva, 6):
                    st.session_state.lat_sucursal_nueva = n_lat
                    st.session_state.lon_sucursal_nueva = n_lon
                    st.rerun()

        with col_form_suc:
            with st.form("form_nueva_sucursal"):
                nombre_suc = st.text_input("Nombre de la Sucursal:")
                radio_m = st.number_input("Radio de tolerancia (Metros):", min_value=50, max_value=5000, value=200, step=50)
                st.caption(f"📍 Coordenadas: `{st.session_state.lat_sucursal_nueva:.6f}, {st.session_state.lon_sucursal_nueva:.6f}`")
                
                btn_crear_suc = st.form_submit_button("Guardar Sucursal", type="primary", width="stretch")
                
                if btn_crear_suc:
                    if nombre_suc.strip():
                        conn = conectar()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO sucursales (nombre, latitud, longitud, radio_m)
                                VALUES (?, ?, ?, ?)
                            ''', (nombre_suc.strip(), st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva, radio_m))
                            conn.commit()
                            st.success(f"✅ Sucursal **{nombre_suc}** creada con radio de {radio_m}m.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Error: Ya existe una sucursal registrada con ese nombre.")
                        finally:
                            conn.close()
                    else:
                        st.error("Ingresa el nombre de la sucursal.")

        conn = conectar()
        df_suc = pd.read_sql_query("SELECT id, nombre, latitud, longitud, radio_m FROM sucursales", conn)
        conn.close()
        st.markdown("**Sucursales Fijas Registradas:**")
        st.dataframe(df_suc, width="stretch")

    # -------------------------------------------------------------
    # TAB 2: REGISTRAR EMPLEADO
    # -------------------------------------------------------------
    with tab_empleados:
        st.subheader("Asignar Empleado a Sucursal")
        
        conn = conectar()
        df_sucursales = pd.read_sql_query("SELECT * FROM sucursales", conn)
        conn.close()
        
        if df_sucursales.empty:
            st.warning("Crea una sucursal fija primero.")
        else:
            with st.form("form_empleado_fijo"):
                nuevo_email = st.text_input("Correo electrónico:")
                nuevo_nombre = st.text_input("Nombre completo:")
                nueva_password = st.text_input("Contraseña asignada:", type="password", value="1234")
                
                sucursal_seleccionada = st.selectbox("Seleccionar Sucursal asignada:", df_sucursales["nombre"].tolist())
                nuevo_rol = st.selectbox("Rol:", ["Empleado", "Admin"])
                
                btn_guardar_emp = st.form_submit_button("Guardar Empleado", type="primary", width="stretch")
                
                if btn_guardar_emp:
                    if nuevo_email and nuevo_nombre and nueva_password:
                        datos_suc = df_sucursales[df_sucursales["nombre"] == sucursal_seleccionada].iloc[0]
                        
                        conn = conectar()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO empleados (email, nombre, password, lat_sucursal, lon_sucursal, nombre_sucursal, rol)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (nuevo_email.strip(), nuevo_nombre.strip(), nueva_password, datos_suc["latitud"], datos_suc["longitud"], sucursal_seleccionada, nuevo_rol))
                            conn.commit()
                            st.success(f"✅ Empleado **{nuevo_nombre}** registrado con éxito.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Ya existe un usuario registrado con ese correo.")
                        finally:
                            conn.close()
                    else:
                        st.error("Completa todos los campos obligatorios.")

        st.divider()
        conn = conectar()
        df_emp = pd.read_sql_query("SELECT email, nombre, nombre_sucursal, lat_sucursal, lon_sucursal, rol FROM empleados", conn)
        conn.close()
        st.markdown("**Empleados Activos:**")
        st.dataframe(df_emp, width="stretch")