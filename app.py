import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from database import conectar, init_db
from geo_utils import validar_distancia

# Configuración inicial de página
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

# --- PALETA DE COLORES, CONTRASTE Y TAMAÑOS DE FUENTE ---
st.markdown("""
    <style>
    /* 1. FONDO GENERAL OSCURO Y TEXTO BLANCO */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Textos generales, títulos y métricas en blanco */
    div[data-testid="stMainBlockContainer"] h1,
    div[data-testid="stMainBlockContainer"] h2,
    div[data-testid="stMainBlockContainer"] h3,
    div[data-testid="stMainBlockContainer"] p,
    div[data-testid="stMainBlockContainer"] span,
    div[data-testid="stMainBlockContainer"] label {
        color: #FFFFFF !important;
    }

    /* 2. TABLAS Y DATAFRAMES (Texto blanco sobre contenedores oscuros) */
    [data-testid="stDataFrame"], 
    div[data-baseweb="table"], 
    div[role="grid"],
    div[role="grid"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Cabeceras de tablas */
    div[role="columnheader"], div[role="columnheader"] * {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
        font-weight: bold !important;
    }

    /* 3. PROTECCIÓN DE PESTAÑAS (TABS) */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        background-color: #1E293B !important;
        border-bottom: 2px solid #334155 !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 4px 8px !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 16px !important;
    }

    /* Pestaña Inactiva: Texto gris claro bien definido */
    div[data-testid="stTabs"] button[aria-selected="false"] *,
    div[data-testid="stTabs"] button[aria-selected="false"] p,
    div[data-testid="stTabs"] button[aria-selected="false"] span {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        font-weight: 600 !important;
    }

    /* Pestaña Activa: Celeste brillante con subrayado */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        border-bottom: 3px solid #0284C7 !important;
        background-color: transparent !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] *,
    div[data-testid="stTabs"] button[aria-selected="true"] p,
    div[data-testid="stTabs"] button[aria-selected="true"] span {
        color: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* Indicador nativo de Streamlit en celeste */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"] {
        background-color: #0284C7 !important;
    }

    /* 4. BARRA LATERAL (SIDEBAR) */
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #00afef !important;
    }

    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 5. BOTONES CELESTES */
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #38BDF8 !important;
        color: #0F172A !important;
    }

    /* 6. CONTROL GLOBAL DE TAMAÑO DE FUENTE (PERSONALIZABLE) */
    html, body, .stApp {
        font-size: 23px !important; /* Tamaño base de lectura */
    }

    h1, [data-testid="stHeader"] h1 {
        font-size: 2.2rem !important; /* Títulos (st.title) */
    }

    h2 {
        font-size: 1.6rem !important; /* Subtítulos (st.header) */
    }

    h3 {
        font-size: 1.4rem !important; /* Subsecciones (st.subheader) */
    }

    input, select, textarea, div[data-baseweb="select"] span {
        font-size: 18px !important; /* Texto dentro de inputs y selects */
    }

    label, [data-testid="stWidgetLabel"] p {
        font-size: 18px !important; /* Etiquetas encima de los inputs */
    }

    [data-testid="stDataFrame"], div[role="grid"] * {
        font-size: 18px !important; /* Texto interno de tablas y dataframes */
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] * {
        font-size: 18px !important; /* Texto de las pestañas */
    }

    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        font-size: 18px !important; /* Texto de botones */
    }
    </style>
""", unsafe_allow_html=True)


# --- FUNCIÓN OPTIMIZADA CON CACHÉ PARA CARGA INMEDIATA ---
@st.cache_data(ttl=60)
def obtener_lista_empleados():
    conn = conectar()
    df = pd.read_sql_query("SELECT email, nombre FROM empleados WHERE rol = 'Empleado'", conn)
    conn.close()
    return df

# --- AUTENTICACIÓN Y CONTROL DE SESIÓN ---
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = None

st.sidebar.title("🔐 Sesión de Usuario")

if st.session_state.usuario_autenticado is None:
    modo = st.sidebar.radio("Modo de acceso:", ["📲 Marcar Asistencia", "⚙️ Administración"])

    if modo == "📲 Marcar Asistencia":
        df_empleados = obtener_lista_empleados()

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

st.sidebar.markdown(f"""
    <div style="background-color: #0369A1; padding: 12px; border-radius: 8px; color: white; text-align: left; margin-bottom: 20px;">
        <div style="margin-bottom: 4px;">👤 <b>{datos_user['nombre']}</b></div>
        <div>🛡️ <b>Rol:</b> {rol_usuario}</div>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Cerrar Sesión", width="stretch"):
    st.session_state.usuario_autenticado = None
    st.session_state.rol_usuario = None
    st.session_state.datos_user = None
    st.rerun()

# --- MENÚ DE NAVEGACIÓN SEGÚN ROL ---
if rol_usuario == "Admin":
    opciones_menu = ["📊 Dashboard y Planillas", "👥 Gestión de Sucursales y Empleados"]
else:
    opciones_menu = ["📍 Marcar Fichaje"]

seccion = st.sidebar.radio("Navegación:", opciones_menu)

# ==========================================
# SECCIÓN 1: MARCAR FICHAJE (EMPLEADOS)
# ==========================================
if seccion == "📍 Marcar Fichaje":
    st.title("📲 Registro de Asistencia")
    
    conn = conectar()
    res_user = pd.read_sql_query("SELECT * FROM empleados WHERE email = ?", conn, params=(usuario_sel,))
    conn.close()
    
    marcas_permitidas = int(res_user.iloc[0].get("marcas_diarias", 2)) if not res_user.empty else 2
    tipo_turno_user = res_user.iloc[0].get("tipo_turno", "Diurno (8h)") if not res_user.empty else "Diurno (8h)"
    
    st.info(f"📋 **Configuración de tu turno:** {tipo_turno_user} | **Marcas requeridas:** {marcas_permitidas} al día")
    
    if marcas_permitidas == 4:
        opciones_fichaje = ["1. Entrada Jornada", "2. Salida a Almuerzo", "3. Regreso de Almuerzo", "4. Salida Jornada"]
    else:
        opciones_fichaje = ["1. Entrada Jornada", "2. Salida Jornada"]
        
    tipo_registro = st.radio("Selecciona Tipo de Fichaje:", opciones_fichaje, horizontal=True)
    foto = st.camera_input("Toma tu fotografía para fichar")
    
    loc = get_geolocation()
    lat_actual, lon_actual = None, None
    
    if loc and 'coords' in loc:
        lat_actual = loc['coords']['latitude']
        lon_actual = loc['coords']['longitude']
        st.success(f"🌐 GPS Detectado: `{lat_actual:.6f}, {lon_actual:.6f}`")
    else:
        st.warning("⚠️ Permite el acceso a la ubicación en tu celular/navegador para fichar.")

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
                st.success(f"✅ Marcación **{tipo_registro}** registrada DENTRO DE ZONA ({dist_m:.1f} m).")
            else:
                st.error(f"🚨 Marcación **{tipo_registro}** registrada FUERA DE ZONA ({dist_m:.1f} m).")

# ==========================================
# SECCIÓN 2: DASHBOARD Y PLANILLAS (ADMIN)
# ==========================================
elif seccion == "📊 Dashboard y Planillas":
    st.title("📊 Control de Asistencia y Planilla")
    
    tab_auditoria, tab_planillas = st.tabs(["👁️ Auditoría de Fichajes", "💵 Cortes de Planilla"])
    
    with tab_auditoria:
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
                st.subheader("Cumplimiento de Zona")
                st.bar_chart(df_asistencia["Estado Zona"].value_counts())
                
            with col2:
                st.subheader("Geolocalización")
                lat_centro = df_asistencia["latitud"].mean()
                lon_centro = df_asistencia["longitud"].mean()
                
                m_audit = folium.Map(location=[lat_centro, lon_centro], zoom_start=13, scrollWheelZoom=False)
                for _, row in df_asistencia.iterrows():
                    color_punto = "#0284C7" if row["valido_gps"] == 1 else "#DC2626"
                    folium.CircleMarker(
                        location=[row["latitud"], row["longitud"]],
                        radius=7,
                        color=color_punto,
                        fill=True,
                        fill_color=color_punto,
                        popup=f"{row['nombre']} - {row['tipo']}"
                    ).add_to(m_audit)
                st_folium(m_audit, height=280, width="100%", key="mapa_audit")
                
            st.subheader("Registro General")
            st.dataframe(df_asistencia[["id", "nombre", "fecha_hora", "tipo", "Estado Zona"]], width="stretch")
            
            st.divider()
            st.subheader("📸 Ver Fotografía de Fichaje")
            id_sel = st.selectbox("Selecciona ID de Marcación:", df_asistencia["id"].tolist())
            row_foto = df_asistencia[df_asistencia["id"] == id_sel].iloc[0]
            if row_foto["foto_path"] and os.path.exists(row_foto["foto_path"]):
                st.image(row_foto["foto_path"], caption=f"Foto de {row_foto['nombre']} ({row_foto['fecha_hora']})", width=320)
        else:
            st.info("No hay registros de asistencia.")

    # TAB DE CORTES DE PLANILLA (SEMANAL Y QUINCENAL)
    with tab_planillas:
        st.subheader("🗓️ Cálculo y Reporte de Planilla")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            modalidad_filtro = st.selectbox("Filtrar por Modalidad de Corte:", ["Todas", "Semanal", "Quincenal"])
        with col_f2:
            fecha_ref = st.date_input("Fecha de Referencia del Corte:", datetime.now(ZONA_CR).date())
            
        conn = conectar()
        query_emp = "SELECT email, nombre, tipo_corte, tipo_turno, marcas_diarias FROM empleados WHERE rol = 'Empleado'"
        if modalidad_filtro != "Todas":
            query_emp += f" AND tipo_corte = '{modalidad_filtro}'"
        df_emp_corte = pd.read_sql_query(query_emp, conn)
        
        # Calcular rangos de fechas
        if modalidad_filtro == "Semanal":
            inicio_corte = fecha_ref - timedelta(days=fecha_ref.weekday())
            fin_corte = inicio_corte + timedelta(days=6)
        elif modalidad_filtro == "Quincenal":
            if fecha_ref.day <= 15:
                inicio_corte = fecha_ref.replace(day=1)
                fin_corte = fecha_ref.replace(day=15)
            else:
                inicio_corte = fecha_ref.replace(day=16)
                sig_mes = fecha_ref.replace(day=28) + timedelta(days=4)
                fin_corte = sig_mes - timedelta(days=sig_mes.day)
        else:
            inicio_corte = fecha_ref.replace(day=1)
            fin_corte = fecha_ref.replace(day=28)
            
        st.caption(f"📅 **Rango de Corte Estimado:** Del `{inicio_corte}` al `{fin_corte}`")
        
        query_asist = f"""
            SELECT a.email, a.fecha_hora, a.tipo 
            FROM asistencia a
            WHERE date(a.fecha_hora) >= '{inicio_corte}' AND date(a.fecha_hora) <= '{fin_corte}'
        """
        df_marcas_corte = pd.read_sql_query(query_asist, conn)
        conn.close()
        
        resumen_planilla = []
        for _, emp in df_emp_corte.iterrows():
            marcas_emp = df_marcas_corte[df_marcas_corte["email"] == emp["email"]]
            total_marcas = len(marcas_emp)
            
            resumen_planilla.append({
                "Empleado": emp["nombre"],
                "Correo": emp["email"],
                "Corte": emp["tipo_corte"],
                "Turno": emp["tipo_turno"],
                "Marcas Requeridas/Día": emp["marcas_diarias"],
                "Marcas Registradas en Periodo": total_marcas
            })
            
        df_resumen = pd.DataFrame(resumen_planilla)
        st.dataframe(df_resumen, width="stretch")

# ==========================================
# SECCIÓN 3: GESTIÓN DE SUCURSALES Y EMPLEADOS (ADMIN)
# ==========================================
elif seccion == "👥 Gestión de Sucursales y Empleados":
    st.title("👥 Gestión de Sucursales y Empleados")
    
    tab_sucursales, tab_empleados = st.tabs(["🏬 Configurar Sucursal Fija", "👤 Registrar y Configurar Empleado"])
    
    with tab_sucursales:
        st.subheader("Configurar Nueva Sede")
        
        if "lat_sucursal_nueva" not in st.session_state:
            st.session_state.lat_sucursal_nueva = 9.850015
        if "lon_sucursal_nueva" not in st.session_state:
            st.session_state.lon_sucursal_nueva = -83.904938

        col_map, col_form_suc = st.columns([1.3, 1])
        with col_map:
            m = folium.Map(location=[st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva], zoom_start=15, scrollWheelZoom=False)
            folium.Marker([st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva], popup="Sede").add_to(m)
            map_data = st_folium(m, height=280, width="100%", key="mapa_sedes")
            
            if map_data and map_data.get("last_clicked"):
                st.session_state.lat_sucursal_nueva = map_data["last_clicked"]["lat"]
                st.session_state.lon_sucursal_nueva = map_data["last_clicked"]["lng"]
                st.rerun()

        with col_form_suc:
            with st.form("form_nueva_sucursal"):
                nombre_suc = st.text_input("Nombre de la Sucursal:")
                radio_m = st.number_input("Radio tolerancia (Metros):", min_value=50, max_value=5000, value=200, step=50)
                btn_crear_suc = st.form_submit_button("Guardar Sucursal", type="primary", width="stretch")
                
                if btn_crear_suc and nombre_suc.strip():
                    conn = conectar()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO sucursales (nombre, latitud, longitud, radio_m) VALUES (?, ?, ?, ?)",
                                       (nombre_suc.strip(), st.session_state.lat_sucursal_nueva, st.session_state.lon_sucursal_nueva, radio_m))
                        conn.commit()
                        st.success(f"✅ Sucursal **{nombre_suc}** creada.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ya existe una sucursal con ese nombre.")
                    finally:
                        conn.close()

        conn = conectar()
        st.dataframe(pd.read_sql_query("SELECT id, nombre, latitud, longitud, radio_m FROM sucursales", conn), width="stretch")
        conn.close()

    with tab_empleados:
        st.subheader("Registrar Empleado con Configuración de Planilla")
        
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
                sucursal_seleccionada = st.selectbox("Seleccionar Sucursal:", df_sucursales["nombre"].tolist())
                nuevo_rol = st.selectbox("Rol:", ["Empleado", "Admin"])
                
                st.divider()
                st.markdown("**⚙️ Configuración de Planilla y Turno:**")
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    tipo_corte = st.selectbox("Tipo de Corte Planilla:", ["Quincenal", "Semanal"])
                with col_e2:
                    tipo_turno = st.selectbox("Tipo de Turno:", ["Diurno (8h)", "Mixto (7h)", "Nocturno (6h)", "Personalizado"])
                with col_e3:
                    marcas_diarias = st.selectbox("Marcas requeridas al día:", [2, 3, 4], index=0)
                
                btn_guardar_emp = st.form_submit_button("Guardar Empleado", type="primary", width="stretch")
                
                if btn_guardar_emp:
                    if nuevo_email and nuevo_nombre and nueva_password:
                        datos_suc = df_sucursales[df_sucursales["nombre"] == sucursal_seleccionada].iloc[0]
                        
                        conn = conectar()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO empleados (email, nombre, password, lat_sucursal, lon_sucursal, nombre_sucursal, rol, tipo_corte, tipo_turno, marcas_diarias)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (nuevo_email.strip(), nuevo_nombre.strip(), nueva_password, datos_suc["latitud"], datos_suc["longitud"], sucursal_seleccionada, nuevo_rol, tipo_corte, tipo_turno, marcas_diarias))
                            conn.commit()
                            
                            st.cache_data.clear()
                            
                            st.success(f"✅ Empleado **{nuevo_nombre}** registrado con corte {tipo_corte} y {marcas_diarias} marcas.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Ya existe un usuario con ese correo.")
                        finally:
                            conn.close()
                    else:
                        st.error("Completa todos los campos obligatorios.")

        st.divider()
        conn = conectar()
        df_emp = pd.read_sql_query("SELECT email, nombre, nombre_sucursal, rol, tipo_corte, tipo_turno, marcas_diarias FROM empleados", conn)
        conn.close()
        st.markdown("**Empleados Activos y Parametrización:**")
        st.dataframe(df_emp, width="stretch")