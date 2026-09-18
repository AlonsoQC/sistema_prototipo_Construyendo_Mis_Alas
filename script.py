from datetime import date
import json
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
============================================================
CONFIGURACIÓN DE PÁGINA
============================================================
st.set_page_config(
page_title="Construyendo mis Alas - Sistema de Puntaje",
page_icon="🕊️",
layout="wide",
initial_sidebar_state="expanded",
)
============================================================
ESTILOS: fondo blanco, letras grandes y legibles, tarjetas
con color para que cada sección se distinga a simple vista.
============================================================
CUSTOM_CSS = """
<style>
/* Fondo blanco general y letra más grande para facilitar la lectura /
.stApp {
background-color: #FFFFFF !important;
color: #0F172A !important;
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
font-size: 1.02rem !important;
}
p, label, span, h1, h2, h3, h4, .stMarkdown, .stWidgetLabel label {
color: #0F172A !important;
font-weight: 600;
}
h1 {
color: #0284C7 !important;
font-weight: 800 !important;
}
/* Subtítulo debajo del título principal /
.subtitulo-app {
color: #475569 !important;
font-size: 1.15rem !important;
font-weight: 500 !important;
margin-top: -10px !important;
margin-bottom: 15px !important;
}
/* TARJETAS DE SECCIÓN /
.section-card {
background-color: #F0F9FF !important;
border-left: 6px solid #0284C7 !important;
border-radius: 10px !important;
padding: 14px 18px !important;
margin-bottom: 20px !important;
box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
}
.section-card-title {
color: #0369A1 !important;
font-size: 1.3rem !important;
font-weight: 700 !important;
margin: 0 !important;
}
/* Tarjeta de ayuda (color distinto para que se note que es opcional) /
.help-card {
background-color: #FEFCE8 !important;
border-left: 6px solid #EAB308 !important;
border-radius: 10px !important;
padding: 14px 18px !important;
margin-bottom: 16px !important;
}
/* CAMPOS INTERACTIVOS /
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
input,
.stSelectbox div[role="button"] {
background-color: #F1F5F9 !important;
border: 2px solid #CBD5E1 !important;
border-radius: 10px !important;
color: #0F172A !important;
font-weight: 600 !important;
font-size: 1.05rem !important;
}
div[data-baseweb="select"]:hover > div,
div[data-baseweb="input"]:hover > div,
input:focus {
border-color: #2563EB !important;
background-color: #E2E8F0 !important;
}
ul[role="listbox"] {
background-color: #FFFFFF !important;
border: 2px solid #CBD5E1 !important;
border-radius: 10px !important;
}
li[role="option"] {
color: #0F172A !important;
background-color: #FFFFFF !important;
font-weight: 600 !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
background-color: #E0F2FE !important;
color: #0369A1 !important;
}
/* PESTAÑAS /
.stTabs [data-baseweb="tab-list"] {
gap: 10px !important;
background-color: #F8FAFC !important;
padding: 10px !important;
border-radius: 12px !important;
border: 1px solid #E2E8F0 !important;
}
.stTabs [data-baseweb="tab"] {
background-color: #EDF2F7 !important;
border-radius: 8px !important;
border: 1px solid #CBD5E1 !important;
padding: 10px 18px !important;
box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
.stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
color: #334155 !important;
font-weight: 700 !important;
font-size: 1.05rem !important;
}
.stTabs [aria-selected="true"] {
background-color: #2563EB !important;
border-color: #1D4ED8 !important;
box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.4) !important;
}
.stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
color: #FFFFFF !important;
font-weight: 800 !important;
}
/* BOTONES DE OPCIÓN (RADIO) /
div[role="radiogroup"] {
background-color: #F8FAFC !important;
padding: 12px !important;
border-radius: 10px !important;
border: 1px solid #E2E8F0 !important;
gap: 15px !important;
}
div[role="radiogroup"] label {
background-color: #FFFFFF !important;
padding: 8px 14px !important;
border-radius: 8px !important;
border: 1px solid #CBD5E1 !important;
}
div[role="radiogroup"] label p {
color: #0F172A !important;
font-weight: 700 !important;
}
/* BOTONES DE ACCIÓN PRINCIPALES /
.stButton > button {
border-radius: 10px !important;
font-size: 1.08rem !important;
font-weight: 700 !important;
padding: 0.7rem 1.5rem !important;
border: none !important;
background-color: #2563EB !important;
box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important;
transition: transform 0.05s ease-in-out !important;
}
.stButton > button:hover {
transform: scale(1.02) !important;
}
.stButton > button p, .stButton > button span {
color: #FFFFFF !important;
}
/* Botón de eliminar en rojo para que se note que es una acción delicada /
.boton-peligro button {
background-color: #DC2626 !important;
}
/* Cajas de métricas /
div[data-testid="stMetric"] {
background-color: #F8FAFC !important;
border: 2px solid #E2E8F0 !important;
border-radius: 10px !important;
padding: 15px !important;
}
div[data-testid="stMetricValue"] {
font-size: 1.8rem !important;
font-weight: 800 !important;
color: #059669 !important;
}
/* Notificaciones /
.stSuccess {
background-color: #DCFCE7 !important;
border: 1px solid #86EFAC !important;
border-radius: 10px !important;
}
.stSuccess p, .stSuccess span {
color: #15803D !important;
}
/* Tarjeta de sesión activa en la barra lateral /
.tarjeta-sesion {
background-color: #E0F2FE;
padding: 14px 16px;
border-radius: 10px;
color: #0369A1;
font-weight: 700;
border: 1px solid #BAE6FD;
text-align: center;
margin-bottom: 10px;
}
/* Ocultar marca de agua técnica /
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
============================================================
MANEJO SEGURO DE BASE DE DATOS
============================================================
try:
DB_URL = st.secrets.get("DATABASE_URL", "")
except Exception:
DB_URL = os.getenv("DATABASE_URL", "")
DATA_FILE = "data_colegio.json"

@st.cache_resource
def get_db_engine():
if DB_URL:
url = DB_URL.replace("postgres://", "postgresql://")
return create_engine(url)
return None

def inicializar_db_nube(engine):
with engine.begin() as conn:
conn.execute(
text(
"""
CREATE TABLE IF NOT EXISTS colegio_datos (
id INT PRIMARY KEY,
datos JSONB NOT NULL
);
"""
)
)

def normalizar_datos(datos):
if "plan_semestres" not in datos:
datos["plan_semestres"] = []
if "calificaciones" not in datos:
datos["calificaciones"] = []
# Migración retrocompatible de alumnos -> beneficiarios
if "alumnos" in datos and "beneficiarios" not in datos:
datos["beneficiarios"] = datos.pop("alumnos")
if "beneficiarios" not in datos:
datos["beneficiarios"] = []
# Normalizar campo 'alumno' a 'beneficiario' en calificaciones
for c in datos.get("calificaciones", []):
if "alumno" in c and "beneficiario" not in c:
c["beneficiario"] = c.pop("alumno")
# Carpetas por defecto
if "carpetas" not in datos or not datos["carpetas"]:
datos["carpetas"] = ["Tareas", "Asistencia", "Exámenes"]
else:
for folder_def in ["Tareas", "Asistencia", "Exámenes"]:
if folder_def not in datos["carpetas"]:
datos["carpetas"].append(folder_def)
# Normalizar campo 'carpeta' en plan_semestres
for t in datos.get("plan_semestres", []):
if "carpeta" not in t or not t["carpeta"]:
t["carpeta"] = "Tareas"
return datos

def obtener_datos_defecto():
return {
"usuarios": {"admin": {"password": "admin123", "rol": "administrador"}},
"beneficiarios": [{"nombre": "Carlos Pérez", "semestre": 1}],
"carpetas": ["Tareas", "Asistencia", "Exámenes"],
"plan_semestres": [
{
"id": 1,
"semestre": 1,
"semana": 1,
"fecha": "2026-09-01",
"tarea": "Examen Diagnóstico",
"maximo": 100.0,
"carpeta": "Exámenes",
},
{
"id": 2,
"semestre": 1,
"semana": 2,
"fecha": "2026-09-08",
"tarea": "Proyecto Parcial 1",
"maximo": 100.0,
"carpeta": "Tareas",
},
],
"calificaciones": [
{"beneficiario": "Carlos Pérez", "tarea_id": 1, "puntaje": 90.0}
],
}

def cargar_datos():
engine = get_db_engine()
if engine:
try:
inicializar_db_nube(engine)
with engine.connect() as conn:
result = conn.execute(
text("SELECT datos FROM colegio_datos WHERE id = 1;")
).fetchone()
if result and result[0]:
return normalizar_datos(result[0])
else:
datos_defecto = obtener_datos_defecto()
guardar_datos(datos_defecto)
return datos_defecto
except Exception as e:
st.error(f"⚠️ No se pudo conectar con la base de datos en la nube: {e}")
# Respaldo local JSON
if os.path.exists(DATA_FILE):
with open(DATA_FILE, "r", encoding="utf-8") as f:
datos = json.load(f)
return normalizar_datos(datos)
else:
datos_defecto = obtener_datos_defecto()
with open(DATA_FILE, "w", encoding="utf-8") as f:
json.dump(datos_defecto, f, ensure_ascii=False, indent=4)
return datos_defecto

def guardar_datos(datos):
engine = get_db_engine()
if engine:
try:
datos_json = json.dumps(datos, ensure_ascii=False)
with engine.begin() as conn:
conn.execute(
text(
"""
INSERT INTO colegio_datos (id, datos)
VALUES (1, :datos::jsonb)
ON CONFLICT (id)
DO UPDATE SET datos = EXCLUDED.datos;
"""
),
{"datos": datos_json},
)
return
except Exception as e:
st.error(f"⚠️ No se pudo guardar en la nube, se guardó una copia local: {e}")
with open(DATA_FILE, "w", encoding="utf-8") as f:
json.dump(datos, f, ensure_ascii=False, indent=4)

def mostrar_mensaje_exito():
if "mensaje_exito" in st.session_state and st.session_state.mensaje_exito:
st.success(st.session_state.mensaje_exito)
st.toast(st.session_state.mensaje_exito)
del st.session_state["mensaje_exito"]

def emoji_avance(porcentaje):
"""Devuelve un emoji y una frase corta según qué tan avanzado va alguien."""
if porcentaje >= 90:
return "🟢", "¡Excelente avance!"
if porcentaje >= 60:
return "🟡", "Vas por buen camino."
if porcentaje > 0:
return "🟠", "Apenas comenzando, ¡sigue así!"
return "⚪", "Aún no hay puntajes registrados."

============================================================
APLICACIÓN PRINCIPAL
============================================================
def aplicacion_principal():
st.markdown(
"<h1>🕊️ Construyendo mis Alas</h1>"
"<p class='subtitulo-app'>Sistema sencillo para llevar el control de "
"tareas, calificaciones y avance de cada persona en el programa.</p>",
unsafe_allow_html=True,
)
if "db" not in st.session_state:
st.session_state.db = cargar_datos()
if "usuario_logueado" not in st.session_state:
st.session_state.usuario_logueado = None
if "rol_logueado" not in st.session_state:
st.session_state.rol_logueado = None
# --------------------------------------------------------
# PANTALLA DE INGRESO (no ha iniciado sesión)
# --------------------------------------------------------
if st.session_state.usuario_logueado is None:
col_login, col_ayuda = st.columns([2, 1])
with col_login:
st.markdown(
"<div class='section-card'>"
"<p class='section-card-title'>🔑 Ingreso al Sistema</p>"
"<p style='margin:5px 0 0 0;'>Elige una opción abajo para comenzar. "
"Es muy sencillo, solo sigue los pasos.</p>"
"</div>",
unsafe_allow_html=True,
)
mostrar_mensaje_exito()
opcion_auth = st.radio(
"¿Qué deseas hacer?",
["🚪 Ya tengo cuenta, quiero entrar", "🆕 Es mi primera vez, quiero crear una cuenta"],
horizontal=True,
key="auth_radio",
)
if opcion_auth.startswith("🚪"):
with st.form("form_login", clear_on_submit=False):
usuario = st.text_input(
"👤 Tu Nombre de Usuario",
key="login_user",
help="Escribe el nombre de usuario con el que te registraste.",
)
password = st.text_input(
"🔒 Tu Contraseña",
type="password",
key="login_pass",
)
entrar = st.form_submit_button("🚀 Entrar al Sistema", use_container_width=True)
if entrar:
usuarios = st.session_state.db["usuarios"]
if not usuario or not password:
st.warning("⚠️ Por favor completa tu usuario y contraseña.")
elif usuario in usuarios and usuarios[usuario]["password"] == password:
st.session_state.usuario_logueado = usuario
st.session_state.rol_logueado = usuarios[usuario]["rol"]
st.session_state.mensaje_exito = f"✅ ¡Bienvenido(a), {usuario}!"
st.rerun()
else:
st.error(
"❌ El usuario o la contraseña no son correctos. "
"Verifica que no tengan espacios de más y vuelve a intentar."
)
else:
with st.form("form_registro", clear_on_submit=False):
nuevo_usuario = st.text_input(
"👤 Elige tu Nombre de Usuario", key="reg_user"
)
nueva_pass = st.text_input(
"🔒 Elige una Contraseña", type="password", key="reg_pass"
)
rol = st.selectbox(
"📌 ¿Qué tipo de usuario serás?",
["consultor", "administrador"],
help=(
"Consultor: solo puede ver información. "
"Administrador: puede agregar y modificar datos."
),
key="reg_rol",
)
codigo_admin = ""
if rol == "administrador":
codigo_admin = st.text_input(
"🔑 Código Especial de Administrador",
type="password",
help="Pide este código a la persona encargada del sistema.",
key="reg_admin_code",
)
registrar = st.form_submit_button(
"✨ Registrar Mi Cuenta", use_container_width=True
)
if registrar:
if nuevo_usuario.strip() == "" or nueva_pass.strip() == "":
st.warning("⚠️ Por favor escribe un usuario y una contraseña.")
elif nuevo_usuario in st.session_state.db["usuarios"]:
st.warning("⚠️ Ese nombre de usuario ya existe. Intenta con otro.")
elif rol == "administrador" and codigo_admin != "123456789":
st.error("🚫 El código de administrador no es correcto.")
else:
st.session_state.db["usuarios"][nuevo_usuario] = {
"password": nueva_pass,
"rol": rol,
}
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = "✅ ¡Cuenta registrada exitosamente!"
st.balloons()
st.rerun()
with col_ayuda:
st.markdown(
"<div class='help-card'>"
"<p class='section-card-title' style='color:#A16207 !important;'>❓ ¿Necesitas ayuda?</p>"
"<p style='margin:8px 0 0 0;'>"
"<b>1.</b> Si ya tienes usuario, elige <i>'Ya tengo cuenta'</i> e ingresa.<br><br>"
"<b>2.</b> Si es tu primera vez, elige <i>'Es mi primera vez'</i> y llena el formulario.<br><br>"
"<b>3.</b> Si eres administrador, necesitas un código especial que te da "
"la persona encargada del sistema."
"</p></div>",
unsafe_allow_html=True,
)
return # No seguir dibujando el resto de la app hasta iniciar sesión
# --------------------------------------------------------
# BARRA LATERAL (usuario con sesión activa)
# --------------------------------------------------------
with st.sidebar:
st.markdown(
f"<div class='tarjeta-sesion'>👤 {st.session_state.usuario_logueado}"
f"<br>Rol: {st.session_state.rol_logueado.upper()}</div>",
unsafe_allow_html=True,
)
if st.button("🚪 Cerrar Sesión", use_container_width=True):
st.session_state.usuario_logueado = None
st.session_state.rol_logueado = None
st.rerun()
st.markdown("---")
with st.expander("❓ Guía rápida de la aplicación"):
st.markdown(
"- Beneficiario: la persona inscrita en el programa.
"
"- Semestre: el período o nivel en el que va cada persona.
"
"- Carpeta: un grupo de asignaciones, por ejemplo Tareas o Exámenes.
"
"- Asignación: una tarea, examen o actividad con un puntaje máximo.
"
"Usa las pestañas de arriba para moverte entre las secciones."
)
# --------------------------------------------------------
# INTERFAZ PRINCIPAL
# --------------------------------------------------------
mostrar_mensaje_exito()
tab_buscar_beneficiario, tab_buscar_semestre, tab_admin = st.tabs([
"🔍 Avance de una Persona",
"📚 Plan por Semestre",
"⚙️ Administración",
])
# ---------------------------------------------------------
# 1. BUSCADOR POR BENEFICIARIO
# ---------------------------------------------------------
with tab_buscar_beneficiario:
st.markdown(
"<div class='section-card'>"
"<p class='section-card-title'>📋 Calificaciones y Avance por Persona</p>"
"<p style='margin:3px 0 0 0;'>Elige el nombre de la persona para ver sus "
"tareas y qué tanto ha avanzado.</p>"
"</div>",
unsafe_allow_html=True,
)
nombres_beneficiarios = [b["nombre"] for b in st.session_state.db["beneficiarios"]]
if not nombres_beneficiarios:
st.info(
"🙂 Todavía no hay personas registradas. Pide a un administrador "
"que las agregue en la pestaña ⚙️ Administración."
)
else:
beneficiario_sel = st.selectbox(
"👉 Selecciona un Beneficiario:",
["-- Haz clic aquí para elegir --"] + nombres_beneficiarios,
key="select_ben_avance",
)
if beneficiario_sel != "-- Haz clic aquí para elegir --":
beneficiario_info = next(
b for b in st.session_state.db["beneficiarios"]
if b["nombre"] == beneficiario_sel
)
semestre_beneficiario = beneficiario_info["semestre"]
tareas_planeadas = [
t for t in st.session_state.db["plan_semestres"]
if t["semestre"] == semestre_beneficiario
]
st.markdown(
f"### Expediente de: {beneficiario_sel}
"
f"Pertenece al Semestre {semestre_beneficiario}"
)
st.write("")
if not tareas_planeadas:
st.info(
f"Aún no hay asignaciones configuradas para el Semestre "
f"{semestre_beneficiario}."
)
else:
reporte = []
pts_obtenidos_total = 0
pts_maximos_total = 0
for t in tareas_planeadas:
calif = next(
(
c for c in st.session_state.db["calificaciones"]
if c.get("beneficiario", c.get("alumno")) == beneficiario_sel
and c["tarea_id"] == t["id"]
),
None,
)
if calif is not None:
estado = "✅ Calificado"
puntaje_str = f"{calif['puntaje']} / {t['maximo']} pts"
pts_obtenidos_total += calif["puntaje"]
else:
estado = "⏳ Pendiente"
puntaje_str = f"0 / {t['maximo']} pts"
pts_maximos_total += t["maximo"]
reporte.append({
"Carpeta": f"📁 {t.get('carpeta', 'Tareas')}",
"Semana": f"Semana {t['semana']}",
"Fecha Estimada": t["fecha"],
"Nombre de la Asignación": t["tarea"],
"Estado": estado,
"Puntaje Logrado": puntaje_str,
})
df_reporte = pd.DataFrame(reporte)
st.dataframe(df_reporte, use_container_width=True, hide_index=True)
porcentaje = (
(pts_obtenidos_total / pts_maximos_total * 100)
if pts_maximos_total > 0 else 0
)
emoji, frase = emoji_avance(porcentaje)
col_m1, col_m2 = st.columns(2)
with col_m1:
st.metric(
"🎯 Puntaje Total Ganado",
f"{pts_obtenidos_total:.1f} / {pts_maximos_total:.1f} pts",
)
with col_m2:
st.metric("📊 Porcentaje de Avance", f"{porcentaje:.1f}%")
st.progress(min(int(porcentaje), 100), text=f"{emoji} {frase}")
# ---------------------------------------------------------
# 2. BUSCADOR POR SEMESTRE CON CARPETAS
# ---------------------------------------------------------
with tab_buscar_semestre:
st.markdown(
"<div class='section-card'>"
"<p class='section-card-title'>📅 Plan Completo de Asignaciones por Semestre</p>"
"<p style='margin:3px 0 0 0;'>Consulta las asignaciones del semestre, "
"organizadas por carpetas.</p>"
"</div>",
unsafe_allow_html=True,
)
semestres_disponibles = sorted(
set(
[b["semestre"] for b in st.session_state.db["beneficiarios"]]
[t["semestre"] for t in st.session_state.db["plan_semestres"]]
)
)
if not semestres_disponibles:
st.info("Todavía no hay semestres registrados en el sistema.")
else:
sem_sel = st.selectbox(
"👉 Elige el Semestre que deseas consultar:",
semestres_disponibles,
key="select_sem_consultar",
)
st.markdown(f"#### 📝 Asignaciones del Semestre {sem_sel}")
plan_sem = [
t for t in st.session_state.db["plan_semestres"]
if t["semestre"] == sem_sel
]
if not plan_sem:
st.info("No hay asignaciones registradas en este semestre todavía.")
else:
carpetas_en_sem = sorted(set(t.get("carpeta", "Tareas") for t in plan_sem))
tabs_carpetas = st.tabs([f"📁 {c}" for c in carpetas_en_sem])
for index, nombre_carpeta in enumerate(carpetas_en_sem):
with tabs_carpetas[index]:
tareas_carpeta = [
t for t in plan_sem
if t.get("carpeta", "Tareas") == nombre_carpeta
]
df_plan = pd.DataFrame(tareas_carpeta)[
["semana", "fecha", "tarea", "maximo"]
]
df_plan.columns = [
"Semana", "Fecha de Entrega",
"Nombre de la Asignación", "Puntaje Máximo",
]
st.table(df_plan.sort_values(by="Semana"))
st.markdown(f"#### 👥 Personas inscritas en el Semestre {sem_sel}")
beneficiarios_sem = [
b["nombre"] for b in st.session_state.db["beneficiarios"]
if b["semestre"] == sem_sel
]
if beneficiarios_sem:
st.write(", ".join(f"• {nombre}" for nombre in beneficiarios_sem))
else:
st.info("No hay personas inscritas en este semestre todavía.")
# ---------------------------------------------------------
# 3. PANEL DE ADMINISTRACIÓN
# ---------------------------------------------------------
with tab_admin:
if st.session_state.rol_logueado != "administrador":
st.error(
"🚫 Esta sección es solo para Administradores. "
"Si necesitas hacer cambios, pide a un administrador que te ayude "
"o registra una nueva cuenta de administrador."
)
else:
st.markdown(
"<div class='section-card'><p class='section-card-title'>⚙️ Centro de "
"Control y Administración</p><p style='margin:3px 0 0 0;'>Elige abajo "
"qué deseas gestionar. Todo se hace en tablas fáciles de editar.</p></div>",
unsafe_allow_html=True,
)
accion_admin = st.radio(
"👉 ¿Qué deseas administrar?",
[
"📁 Carpetas y Asignaciones",
"👥 Lista de Beneficiarios",
"💯 Asignar Puntajes",
],
horizontal=True,
key="select_accion_admin_main",
)
st.markdown("---")
# =====================================================
# OPCIÓN 1: CARPETAS Y ASIGNACIONES
# =====================================================
if accion_admin == "📁 Carpetas y Asignaciones":
st.markdown(
"<div class='section-card'><p class='section-card-title'>📁 Gestión "
"de Carpetas y Asignaciones</p><p style='margin:3px 0 0 0;'>Crea, "
"renombra o elimina carpetas, y edita las asignaciones directamente "
"en la tabla.</p></div>",
unsafe_allow_html=True,
)
carpetas_actuales = st.session_state.db.get(
"carpetas", ["Tareas", "Asistencia", "Exámenes"]
)
col_c1, col_c2 = st.columns(2)
with col_c1:
st.markdown("#### ➕ Crear Carpeta")
with st.form("form_crear_carpeta"):
nueva_carp_txt = st.text_input(
"Nombre de la nueva carpeta:",
key="input_crear_carpeta_nueva",
placeholder="Ej. Proyectos Finales",
)
crear_carp = st.form_submit_button(
"✨ Guardar Nueva Carpeta", use_container_width=True
)
if crear_carp:
nombre_f = nueva_carp_txt.strip()
if not nombre_f:
st.warning("⚠️ Escribe un nombre para la carpeta.")
elif nombre_f in carpetas_actuales:
st.warning("⚠️ Ya existe una carpeta con ese nombre.")
else:
st.session_state.db["carpetas"].append(nombre_f)
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = (
f"✅ Carpeta '📁 {nombre_f}' creada exitosamente."
)
st.rerun()
with col_c2:
st.markdown("#### ✏️ Renombrar o 🗑️ Eliminar Carpeta")
if carpetas_actuales:
carpeta_sel_gestion = st.selectbox(
"Selecciona la carpeta:",
carpetas_actuales,
key="select_carpeta_mod_gest",
)
nuevo_nombre_carp = st.text_input(
"Nuevo nombre para la carpeta:",
value=carpeta_sel_gestion,
key="input_nuevo_nombre_carpeta",
)
c_btn1, c_btn2 = st.columns(2)
with c_btn1:
if st.button("💾 Renombrar Carpeta", key="btn_renombrar_carpeta", use_container_width=True):
nom_ren = nuevo_nombre_carp.strip()
if not nom_ren:
st.warning("⚠️ El nombre no puede estar vacío.")
elif nom_ren in carpetas_actuales and nom_ren != carpeta_sel_gestion:
st.warning("⚠️ Ya existe otra carpeta con ese nombre.")
else:
idx = st.session_state.db["carpetas"].index(carpeta_sel_gestion)
st.session_state.db["carpetas"][idx] = nom_ren
for t in st.session_state.db.get("plan_semestres", []):
if t.get("carpeta") == carpeta_sel_gestion:
t["carpeta"] = nom_ren
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = f"✅ Carpeta renombrada a '📁 {nom_ren}'."
st.rerun()
with c_btn2:
st.markdown("<div class='boton-peligro'>", unsafe_allow_html=True)
confirmar_borrado = st.checkbox(
"Sí, quiero eliminarla", key="chk_confirmar_borrado_carpeta"
)
if st.button("🗑️ Eliminar Carpeta", key="btn_eliminar_carpeta", use_container_width=True):
if len(carpetas_actuales) <= 1:
st.error("🚫 Debes conservar al menos una carpeta en el sistema.")
elif not confirmar_borrado:
st.warning("⚠️ Marca la casilla de confirmación antes de eliminar.")
else:
st.session_state.db["carpetas"].remove(carpeta_sel_gestion)
carpeta_reemplazo = st.session_state.db["carpetas"][0]
for t in st.session_state.db.get("plan_semestres", []):
if t.get("carpeta") == carpeta_sel_gestion:
t["carpeta"] = carpeta_reemplazo
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = (
f"✅ Carpeta '📁 {carpeta_sel_gestion}' eliminada. "
f"Sus asignaciones pasaron a '📁 {carpeta_reemplazo}'."
)
st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("#### 📝 Tabla de Asignaciones por Carpeta")
st.caption(
"💡 Haz clic en cualquier celda para editarla directamente. "
"Para agregar una fila nueva, usa el signo '+' al final de la tabla."
)
filtro_carpeta_grilla = st.selectbox(
"📁 Filtrar asignaciones por carpeta:",
["-- Mostrar todas las carpetas --"] + carpetas_actuales,
key="select_filtro_carpeta_grilla",
)
plan_actual = st.session_state.db.get("plan_semestres", [])
if filtro_carpeta_grilla != "-- Mostrar todas las carpetas --":
plan_filtrado = [
t for t in plan_actual
if t.get("carpeta", "Tareas") == filtro_carpeta_grilla
]
else:
plan_filtrado = plan_actual
df_plan_edit = pd.DataFrame(plan_filtrado)
for col in ["id", "semestre", "semana", "fecha", "tarea", "maximo", "carpeta"]:
if col not in df_plan_edit.columns:
if col in ["semestre", "semana"]:
df_plan_edit[col] = 1
elif col == "maximo":
df_plan_edit[col] = 100.0
elif col == "carpeta":
default_c = (
filtro_carpeta_grilla
if filtro_carpeta_grilla != "-- Mostrar todas las carpetas --"
else (carpetas_actuales[0] if carpetas_actuales else "Tareas")
)
df_plan_edit[col] = default_c
else:
df_plan_edit[col] = None
if "fecha" in df_plan_edit.columns and not df_plan_edit.empty:
df_plan_edit["fecha"] = pd.to_datetime(
df_plan_edit["fecha"], errors="coerce"
).dt.date
opciones_semestres = list(range(1, 13))
grid_actividades = st.data_editor(
df_plan_edit,
column_config={
"id": st.column_config.NumberColumn("ID", disabled=True),
"semestre": st.column_config.SelectboxColumn(
"Semestre", options=opciones_semestres, required=True
),
"semana": st.column_config.NumberColumn(
"Semana", min_value=1, max_value=52, step=1, required=True
),
"fecha": st.column_config.DateColumn(
"Fecha de Entrega", format="DD/MM/YYYY", required=False
),
"tarea": st.column_config.TextColumn(
"Nombre de la Asignación", required=True
),
"maximo": st.column_config.NumberColumn(
"Puntos Máximos", min_value=1.0, max_value=1000.0, step=1.0, required=True
),
"carpeta": st.column_config.SelectboxColumn(
"Carpeta Destino", options=carpetas_actuales, required=True
),
},
num_rows="dynamic",
use_container_width=True,
key="editor_grid_plan_actividades_v8",
)
if st.button("💾 Guardar Cambios en las Asignaciones", key="btn_save_grid_actividades_v8", use_container_width=True):
ids_modificados = set()
nuevas_asignaciones_mod = []
next_id = max([t["id"] for t in plan_actual], default=0) + 1
for _, row in grid_actividades.iterrows():
nombre_asig = str(row["tarea"]).strip()
if nombre_asig and nombre_asig not in ("nan", "None"):
try:
sem_val = int(row["semestre"])
except Exception:
sem_val = 1
try:
sem_num = int(row["semana"])
except Exception:
sem_num = 1
try:
max_val = float(row["maximo"])
except Exception:
max_val = 100.0
if pd.notna(row["fecha"]) and str(row["fecha"]).strip() not in ("nan", "None", ""):
f_val = str(row["fecha"]).strip()
else:
f_val = ""
raw_c_val = str(row["carpeta"]).strip()
if raw_c_val in carpetas_actuales:
c_val = raw_c_val
elif filtro_carpeta_grilla != "-- Mostrar todas las carpetas --":
c_val = filtro_carpeta_grilla
else:
c_val = carpetas_actuales[0] if carpetas_actuales else "Tareas"
try:
row_id = int(row["id"])
if row_id <= 0 or pd.isna(row["id"]):
row_id = next_id
next_id += 1
except Exception:
row_id = next_id
next_id += 1
ids_modificados.add(row_id)
nuevas_asignaciones_mod.append({
"id": row_id,
"semestre": sem_val,
"semana": sem_num,
"fecha": f_val,
"tarea": nombre_asig,
"maximo": max_val,
"carpeta": c_val,
})
if filtro_carpeta_grilla != "-- Mostrar todas las carpetas --":
otras_asignaciones = [
t for t in plan_actual
if t.get("carpeta") != filtro_carpeta_grilla and t["id"] not in ids_modificados
]
lista_final_plan = otras_asignaciones + nuevas_asignaciones_mod
else:
lista_final_plan = nuevas_asignaciones_mod
st.session_state.db["plan_semestres"] = lista_final_plan
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = "✅ ¡Asignaciones guardadas correctamente!"
st.rerun()
# =====================================================
# OPCIÓN 2: BENEFICIARIOS
# =====================================================
elif accion_admin == "👥 Lista de Beneficiarios":
st.markdown(
"<div class='section-card'><p class='section-card-title'>✏️ Tabla de "
"Beneficiarios</p><p style='margin:3px 0 0 0;'>Agrega personas nuevas, "
"cambia su nombre o su semestre directamente en la tabla.</p></div>",
unsafe_allow_html=True,
)
df_ben_actual = pd.DataFrame(st.session_state.db.get("beneficiarios", []))
if df_ben_actual.empty:
df_ben_actual = pd.DataFrame(columns=["nombre", "semestre"])
st.caption("💡 Haz doble clic en cualquier celda para editarla.")
df_ben_editado = st.data_editor(
df_ben_actual,
column_config={
"nombre": st.column_config.TextColumn(
"Nombre Completo de la Persona", required=True
),
"semestre": st.column_config.SelectboxColumn(
"Semestre Cursando", options=list(range(1, 13)), required=True
),
},
num_rows="dynamic",
use_container_width=True,
key="ben_data_editor_v8",
)
if st.button("💾 Guardar Cambios de Beneficiarios", key="btn_save_grid_ben_v8", use_container_width=True):
nuevos_beneficiarios = []
for _, row in df_ben_editado.iterrows():
nom = str(row["nombre"]).strip()
if nom and nom != "nan":
try:
sem = int(row["semestre"])
except Exception:
sem = 1
nuevos_beneficiarios.append({"nombre": nom, "semestre": sem})
st.session_state.db["beneficiarios"] = nuevos_beneficiarios
guardar_datos(st.session_state.db)
st.session_state.mensaje_exito = "✅ ¡Lista de beneficiarios actualizada correctamente!"
st.rerun()
# =====================================================
# OPCIÓN 3: ASIGNAR PUNTAJES
# =====================================================
elif accion_admin == "💯 Asignar Puntajes":
st.markdown(
"<div class='section-card'><p class='section-card-title'>💯 Asignar o "
"Modificar Puntajes</p><p style='margin:3px 0 0 0;'>Sigue los 3 pasos "
"para registrar la calificación de una persona.</p></div>",
unsafe_allow_html=True,
)
lista_beneficiarios = [b["nombre"] for b in st.session_state.db.get("beneficiarios", [])]
if not lista_beneficiarios:
st.info(
"Primero debes registrar a una persona en la sección "
"👥 Lista de Beneficiarios."
)
else:
beneficiario_eval = st.selectbox(
"1️⃣ Selecciona a la Persona:",
lista_beneficiarios,
key="cal_ben_select_v8",
)
beneficiario_obj = next(
b for b in st.session_state.db["beneficiarios"]
if b["nombre"] == beneficiario_eval
)
sem_estudiante = beneficiario_obj["semestre"]
tareas_disponibles = [
t for t in st.session_state.db["plan_semestres"]
if t["semestre"] == sem_estudiante
]
if not tareas_disponibles:
st.warning(
f"⚠️ {beneficiario_eval} está en el Semestre {sem_estudiante}, "
"pero aún no hay asignaciones creadas para ese semestre. "
"Ve a 📁 Carpetas y Asignaciones para crearlas."
)
else:
opciones_tareas = {
f"📁 [{t.get('carpeta', 'Tareas')}] Sem {t['semana']} - "
f"{t['tarea']} (Máximo: {t['maximo']} pts)": t
for t in tareas_disponibles
}
tarea_seleccionada_label = st.selectbox(
"2️⃣ Selecciona la Asignación:",
list(opciones_tareas.keys()),
key="cal_act_select_v8",
)
tarea_obj = opciones_tareas[tarea_seleccionada_label]
calif_previa = next(
(
c for c in st.session_state.db["calificaciones"]
if (c.get("beneficiario") == beneficiario_eval or c.get("alumno") == beneficiario_eval)
and c["tarea_id"] == tarea_obj["id"]
),
None,
)
val_defecto = float(calif_previa["puntaje"]) if calif_previa else 0.0
puntaje_ingresado = st.number_input(
f"3️⃣ Ingresa el Puntaje Obtenido (Máximo posible: {tarea_obj['maximo']} pts)",
min_value=0.0,
max_value=float(tarea_obj["maximo"]),
value=val_defecto,
step=0.5,
key="pts_input_v8",
)
if st.button("💾 Guardar Puntaje", key="btn_save_calif_v8", use_container_width=True):
if calif_previa:
calif_previa["puntaje"] = puntaje_ingresado
st.session_state.mensaje_exito = (
f"✅ Puntaje actualizado a {puntaje_ingresado} pts para "
f"{beneficiario_eval} en '{tarea_obj['tarea']}'."
)
else:
st.session_state.db["calificaciones"].append({
"beneficiario": beneficiario_eval,
"tarea_id": tarea_obj["id"],
"puntaje": puntaje_ingresado,
})
st.session_state.mensaje_exito = (
f"✅ Puntaje registrado: {puntaje_ingresado} pts para "
f"{beneficiario_eval} en '{tarea_obj['tarea']}'."
)
guardar_datos(st.session_state.db)
st.rerun()

if __name__ == "__main__":
aplicacion_principal()