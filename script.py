from datetime import date
import json
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN DE PÁGINA Y TEMA CLARO/ACCESIBLE ---
st.set_page_config(
    page_title="Construyendo mis Alas - Sistema de Puntaje",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS minuciosos para fondos sombreados en todas las secciones, entradas, selectores y botones
CUSTOM_CSS = """
<style>
    /* Fondo blanco general */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* Regla general para texto */
    p, label, span, h1, h2, h3, h4, .stMarkdown, .stWidgetLabel label {
        color: #0F172A !important;
        font-weight: 600;
    }

    /* Título Principal */
    h1 {
        color: #0284C7 !important;
        font-weight: 800 !important;
    }

    /* TARJETAS DE SECCIÓN Y SUBTÍTULOS SOMBREADOS */
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

    /* CAMPOS INTERACTIVOS SOMBREADOS Y VISIBLES */
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

    /* Hover y Foco */
    div[data-baseweb="select"]:hover > div, 
    div[data-baseweb="input"]:hover > div, 
    input:focus {
        border-color: #2563EB !important;
        background-color: #E2E8F0 !important;
    }

    /* Menú desplegable */
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

    /* PESTAÑAS SOMBREADAS */
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

    /* BOTONES DE OPCIÓN (RADIO) */
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

    /* BOTONES DE ACCIÓN PRINCIPALES */
    .stButton > button {
        border-radius: 10px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.5rem !important;
        border: none !important;
        background-color: #2563EB !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important;
    }
    
    .stButton > button p, .stButton > button span {
        color: #FFFFFF !important;
    }

    /* Cajas de métricas */
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

    /* Notificaciones */
    .stSuccess {
        background-color: #DCFCE7 !important;
        border: 1px solid #86EFAC !important;
        border-radius: 10px !important;
    }
    .stSuccess p, .stSuccess span {
        color: #15803D !important;
    }

    /* Ocultar marca de agua técnica */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- MANEJO SEGURO DE DATABASE ---
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
        text("""
                CREATE TABLE IF NOT EXISTS colegio_datos (
                    id INT PRIMARY KEY,
                    datos JSONB NOT NULL
                );
            """)
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

  # 1. Cargar desde PostgreSQL en la nube
  if engine:
    try:
      inicializar_db_nube(engine)
      with engine.connect() as conn:
        result = conn.execute(
            text("SELECT datos FROM colegio_datos WHERE id = 1;")
        ).fetchone()

      if result and result[0]:
        datos = result[0]
        return normalizar_datos(datos)
      else:
        datos_defecto = obtener_datos_defecto()
        guardar_datos(datos_defecto)
        return datos_defecto
    except Exception as e:
      st.error(f"Error en base de datos de la nube: {e}")

  # 2. Respaldo local JSON
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

  # 1. Guardar en la nube
  if engine:
    try:
      datos_json = json.dumps(datos, ensure_ascii=False)
      with engine.begin() as conn:
        conn.execute(
            text("""
                        INSERT INTO colegio_datos (id, datos) 
                        VALUES (1, :datos::jsonb)
                        ON CONFLICT (id) 
                        DO UPDATE SET datos = EXCLUDED.datos;
                    """),
            {"datos": datos_json},
        )
      return
    except Exception as e:
      st.error(f"Error al guardar en la nube: {e}")

  # 2. Guardar localmente
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=4)


def mostrar_mensaje_exito():
  if "mensaje_exito" in st.session_state and st.session_state.mensaje_exito:
    st.success(st.session_state.mensaje_exito)
    st.toast(st.session_state.mensaje_exito)
    del st.session_state["mensaje_exito"]


def aplicacion_principal():
  st.markdown(
      "<h1>🕊️ Sistema de Puntaje - Construyendo mis Alas</h1>",
      unsafe_allow_html=True,
  )

  if "db" not in st.session_state:
    st.session_state.db = cargar_datos()

  if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

  if "rol_logueado" not in st.session_state:
    st.session_state.rol_logueado = None

  # --- AUTENTICACIÓN ---
  if st.session_state.usuario_logueado is None:
    st.markdown(
        "<div class='section-card'>"
        "<p class='section-card-title'>🔑 Ingreso al Sistema</p>"
        "<p style='margin:5px 0 0 0;'>Selecciona una opción para comenzar de"
        " forma muy sencilla.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    mostrar_mensaje_exito()

    opcion_auth = st.radio(
        "¿Qué deseas hacer?",
        ["Entrar a mi cuenta", "Crear una cuenta nueva"],
        horizontal=True,
        key="auth_radio",
    )

    if opcion_auth == "Entrar a mi cuenta":
      col_in1, col_in2 = st.columns([1, 1])
      with col_in1:
        usuario = st.text_input("👤 Tu Nombre de Usuario", key="login_user")
        password = st.text_input(
            "🔒 Tu Contraseña", type="password", key="login_pass"
        )

        if st.button("🚀 Entrar al Sistema", key="btn_login"):
          usuarios = st.session_state.db["usuarios"]
          if usuario in usuarios and usuarios[usuario]["password"] == password:
            st.session_state.usuario_logueado = usuario
            st.session_state.rol_logueado = usuarios[usuario]["rol"]
            st.session_state.mensaje_exito = f"✅ ¡Bienvenido(a), {usuario}!"
            st.rerun()
          else:
            st.error("❌ El usuario o la contraseña no son correctos.")

    elif opcion_auth == "Crear una cuenta nueva":
      col_reg1, col_reg2 = st.columns([1, 1])
      with col_reg1:
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
                "Consultor: Solo para ver información. Administrador: Para"
                " modificar datos."
            ),
            key="reg_rol",
        )

        codigo_admin = ""
        if rol == "administrador":
          codigo_admin = st.text_input(
              "🔑 Código Especial de Administrador",
              type="password",
              help="Código secreto para administradores",
              key="reg_admin_code",
          )

        if st.button("✨ Registrar Mi Cuenta", key="btn_register"):
          if nuevo_usuario.strip() == "" or nueva_pass.strip() == "":
            st.warning("⚠️ Por favor escribe un usuario y una contraseña.")
          elif nuevo_usuario in st.session_state.db["usuarios"]:
            st.warning(
                "⚠️ Este nombre de usuario ya existe. Intenta con otro."
            )
          elif rol == "administrador" and codigo_admin != "123456789":
            st.error("🚫 El código de administrador no es correcto.")
          else:
            st.session_state.db["usuarios"][nuevo_usuario] = {
                "password": nueva_pass,
                "rol": rol,
            }
            guardar_datos(st.session_state.db)
            st.session_state.mensaje_exito = (
                "✅ ¡Cuenta registrada exitosamente!"
            )
            st.rerun()

  # --- INTERFAZ PRINCIPAL ---
  else:
    # Barra superior de usuario
    col_user, col_logout = st.columns([3, 1])
    with col_user:
      st.markdown(
          "<div style='background-color:#E0F2FE; padding:12px 18px;"
          " border-radius:10px; color:#0369A1; font-weight:bold;"
          " font-size:1.1rem; border: 1px solid #BAE6FD;'>👤 Sesión activa:"
          f" <b>{st.session_state.usuario_logueado}</b> | Rol:"
          f" <b>{st.session_state.rol_logueado.upper()}</b></div>",
          unsafe_allow_html=True,
      )
    with col_logout:
      if st.button("🚪 Cerrar Sesión", key="btn_logout"):
        st.session_state.usuario_logueado = None
        st.session_state.rol_logueado = None
        st.rerun()

    st.write("")
    mostrar_mensaje_exito()

    # NAVEGACIÓN PRINCIPAL CON ICONOS
    tab_buscar_beneficiario, tab_buscar_semestre, tab_admin = st.tabs([
        "🔍 Ver Avance por Persona",
        "📚 Ver Plan General por Semestre",
        "⚙️ Administración y Registro",
    ])

    # ---------------------------------------------------------
    # 1. BUSCADOR POR BENEFICIARIO
    # ---------------------------------------------------------
    with tab_buscar_beneficiario:
      st.markdown(
          "<div class='section-card'>"
          "<p class='section-card-title'>📋 Calificaciones y Avance por"
          " Persona</p>"
          "<p style='margin:3px 0 0 0;'>Selecciona el nombre de la persona para"
          " consultar sus puntajes.</p>"
          "</div>",
          unsafe_allow_html=True,
      )

      nombres_beneficiarios = [
          b["nombre"] for b in st.session_state.db["beneficiarios"]
      ]

      if nombres_beneficiarios:
        beneficiario_sel = st.selectbox(
            "👉 Selecciona un Beneficiario:",
            ["-- Haz clic aquí para elegir --"] + nombres_beneficiarios,
            key="select_ben_avance",
        )

        if beneficiario_sel != "-- Haz clic aquí para elegir --":
          beneficiario_info = next(
              b
              for b in st.session_state.db["beneficiarios"]
              if b["nombre"] == beneficiario_sel
          )
          semestre_beneficiario = beneficiario_info["semestre"]

          tareas_planeadas = [
              t
              for t in st.session_state.db["plan_semestres"]
              if t["semestre"] == semestre_beneficiario
          ]

          st.markdown(
              "<div style='background-color:#F1F5F9; padding:15px;"
              " border-radius:10px; border-left: 6px solid #2563EB;"
              " margin-top:10px;'><h3 style='margin:0; color:#1E293B;'>Expediente"
              f" de: <b>{beneficiario_sel}</b></h3><p style='margin:0;"
              " font-size:1.1rem; color:#475569;'>Pertenece al <b>Semestre"
              f" {semestre_beneficiario}</b></p></div>",
              unsafe_allow_html=True,
          )
          st.write("")

          if tareas_planeadas:
            reporte = []
            pts_obtenidos_total = 0
            pts_maximos_total = 0

            for t in tareas_planeadas:
              calif = next(
                  (
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c.get("beneficiario", c.get("alumno"))
                      == beneficiario_sel
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
            st.dataframe(df_reporte, use_container_width=True)

            col_m1, col_m2 = st.columns(2)
            with col_m1:
              st.metric(
                  "🎯 Puntaje Total Ganado",
                  f"{pts_obtenidos_total:.1f} / {pts_maximos_total:.1f} pts",
              )
            with col_m2:
              porcentaje = (
                  (pts_obtenidos_total / pts_maximos_total * 100)
                  if pts_maximos_total > 0
                  else 0
              )
              st.metric("📊 Porcentaje de Avance", f"{porcentaje:.1f}%")
          else:
            st.info(
                "Aún no hay asignaciones configuradas para el Semestre"
                f" {semestre_beneficiario}."
            )
      else:
        st.info("No hay beneficiarios registrados todavía.")

    # ---------------------------------------------------------
    # 2. BUSCADOR POR SEMESTRE CON CARPETAS
    # ---------------------------------------------------------
    with tab_buscar_semestre:
      st.markdown(
          "<div class='section-card'>"
          "<p class='section-card-title'>📅 Plan Completo de Asignaciones por"
          " Semestre</p>"
          "<p style='margin:3px 0 0 0;'>Consulta las asignaciones del semestre"
          " organizadas en sus carpetas.</p>"
          "</div>",
          unsafe_allow_html=True,
      )
      semestres_disponibles = sorted(
          list(
              set(
                  [
                      b["semestre"]
                      for b in st.session_state.db["beneficiarios"]
                  ]
                  + [
                      t["semestre"]
                      for t in st.session_state.db["plan_semestres"]
                  ]
              )
          )
      )

      if semestres_disponibles:
        sem_sel = st.selectbox(
            "👉 Elige el Semestre que deseas consultar:",
            semestres_disponibles,
            key="select_sem_consultar",
        )

        st.markdown(f"#### 📝 Asignaciones del Semestre {sem_sel}")
        plan_sem = [
            t
            for t in st.session_state.db["plan_semestres"]
            if t["semestre"] == sem_sel
        ]

        if plan_sem:
          carpetas_en_sem = sorted(
              list(set([t.get("carpeta", "Tareas") for t in plan_sem]))
          )

          tabs_carpetas = st.tabs([f"📁 {c}" for c in carpetas_en_sem])
          for index, nombre_carpeta in enumerate(carpetas_en_sem):
            with tabs_carpetas[index]:
              tareas_carpeta = [
                  t
                  for t in plan_sem
                  if t.get("carpeta", "Tareas") == nombre_carpeta
              ]
              df_plan = pd.DataFrame(tareas_carpeta)[
                  ["semana", "fecha", "tarea", "maximo"]
              ]
              df_plan.columns = [
                  "Semana",
                  "Fecha de Entrega",
                  "Nombre de la Asignación",
                  "Puntaje Máximo",
              ]
              st.table(df_plan.sort_values(by="Semana"))
        else:
          st.info("No hay asignaciones registradas en este semestre.")

        st.markdown(f"#### 👥 Personas inscritas en el Semestre {sem_sel}")
        beneficiarios_sem = [
            b["nombre"]
            for b in st.session_state.db["beneficiarios"]
            if b["semestre"] == sem_sel
        ]
        if beneficiarios_sem:
          st.write(
              ", ".join([f"• **{nombre}**" for nombre in beneficiarios_sem])
          )
        else:
          st.info("No hay personas inscritas en este semestre.")
      else:
        st.info("No hay semestres registrados en el sistema.")

    # ---------------------------------------------------------
    # 3. PANEL DE ADMINISTRACIÓN SIMPLIFICADO
    # ---------------------------------------------------------
    with tab_admin:
      if st.session_state.rol_logueado != "administrador":
        st.error("🚫 Esta sección requiere permisos de Administrador.")
      else:
        st.markdown(
            "<div class='section-card'><p class='section-card-title'>⚙️ Centro"
            " de Control y Administración</p><p style='margin:3px 0 0"
            " 0;'>Selecciona la sección que deseas gestionar. Toda la edición"
            " de asignaciones y carpetas se realiza de manera unificada en"
            " cuadrícula.</p></div>",
            unsafe_allow_html=True,
        )

        accion_admin = st.selectbox(
            "👉 Selecciona la sección a administrar:",
            [
                "📁 1. Administrar Carpetas y Asignaciones por Cuadrícula",
                "👥 2. Administrar Lista de Beneficiarios",
                "💯 3. Asignar Puntajes",
            ],
            key="select_accion_admin_main",
        )

        st.markdown("---")

        # =====================================================
        # OPCIÓN 1: CARPETAS Y ASIGNACIONES INTEGRADAS EN GRILLA
        # =====================================================
        if "📁 1. Administrar Carpetas" in accion_admin:
          st.markdown(
              "<div class='section-card'><p class='section-card-title'>📁"
              " Gestión Unificada de Carpetas y Asignaciones</p><p"
              " style='margin:3px 0 0 0;'>Crea, renombra o elimina carpetas, y"
              " edita directamente en la cuadrícula todas sus asignaciones por"
              " semestre.</p></div>",
              unsafe_allow_html=True,
          )

          carpetas_actuales = st.session_state.db.get(
              "carpetas", ["Tareas", "Asistencia", "Exámenes"]
          )

          # --- GESTIÓN DIRECTA DE CARPETAS ---
          col_c1, col_c2 = st.columns(2)

          with col_c1:
            st.markdown("#### ➕ Crear Carpeta")
            nueva_carp_txt = st.text_input(
                "Nombre de la nueva carpeta:", key="input_crear_carpeta_nueva"
            )
            if st.button(
                "✨ Guardar Nueva Carpeta", key="btn_crear_carpeta_nueva"
            ):
              nombre_f = nueva_carp_txt.strip()
              if not nombre_f:
                st.warning("⚠️ Escribe un nombre para la carpeta.")
              elif nombre_f in carpetas_actuales:
                st.warning("⚠️ Ya existe una carpeta con ese nombre.")
              else:
                st.session_state.db["carpetas"].append(nombre_f)
                guardar_datos(st.session_state.db)
                st.session_state.mensaje_exito = (
                    f"✅ Carpeta '📁 {nombre_f}' creada exitosamente. Ahora"
                    " puedes agregar asignaciones dentro de ella."
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
                if st.button(
                    "💾 Renombrar Carpeta", key="btn_renombrar_carpeta"
                ):
                  nom_ren = nuevo_nombre_carp.strip()
                  if not nom_ren:
                    st.warning("⚠️ El nombre no puede estar vacío.")
                  elif (
                      nom_ren in carpetas_actuales
                      and nom_ren != carpeta_sel_gestion
                  ):
                    st.warning("⚠️ Ya existe otra carpeta con ese nombre.")
                  else:
                    idx = st.session_state.db["carpetas"].index(
                        carpeta_sel_gestion
                    )
                    st.session_state.db["carpetas"][idx] = nom_ren

                    for t in st.session_state.db.get("plan_semestres", []):
                      if t.get("carpeta") == carpeta_sel_gestion:
                        t["carpeta"] = nom_ren

                    guardar_datos(st.session_state.db)
                    st.session_state.mensaje_exito = (
                        f"✅ Carpeta renombrada a '📁 {nom_ren}'."
                    )
                    st.rerun()

              with c_btn2:
                if st.button("🗑️ Eliminar Carpeta", key="btn_eliminar_carpeta"):
                  if len(carpetas_actuales) <= 1:
                    st.error(
                        "🚫 Debes conservar al menos una carpeta en el sistema."
                    )
                  else:
                    st.session_state.db["carpetas"].remove(carpeta_sel_gestion)
                    carpeta_reemplazo = st.session_state.db["carpetas"][0]

                    for t in st.session_state.db.get("plan_semestres", []):
                      if t.get("carpeta") == carpeta_sel_gestion:
                        t["carpeta"] = carpeta_reemplazo

                    guardar_datos(st.session_state.db)
                    st.session_state.mensaje_exito = (
                        f"✅ Carpeta '📁 {carpeta_sel_gestion}' eliminada. Sus"
                        f" asignaciones pasaron a '📁 {carpeta_reemplazo}'."
                    )
                    st.rerun()

          st.markdown("---")

          # --- EDICIÓN EN GRILLA DE TODAS LAS ASIGNACIONES POR CARPETA ---
          st.markdown(
              "#### 📝 Cuadrícula Directa de Asignaciones por Carpeta"
          )

          filtro_carpeta_grilla = st.selectbox(
              "📁 Filtrar asignaciones por carpeta:",
              ["-- Mostrar todas las carpetas --"] + carpetas_actuales,
              key="select_filtro_carpeta_grilla",
          )

          plan_actual = st.session_state.db.get("plan_semestres", [])

          if filtro_carpeta_grilla != "-- Mostrar todas las carpetas --":
            plan_filtrado = [
                t
                for t in plan_actual
                if t.get("carpeta", "Tareas") == filtro_carpeta_grilla
            ]
          else:
            plan_filtrado = plan_actual

          df_plan_edit = pd.DataFrame(plan_filtrado)

          # Garantizar columnas necesarias y tipos adecuados
          for col in [
              "id",
              "semestre",
              "semana",
              "fecha",
              "tarea",
              "maximo",
              "carpeta",
          ]:
            if col not in df_plan_edit.columns:
              if col in ["semestre", "semana"]:
                df_plan_edit[col] = 1
              elif col == "maximo":
                df_plan_edit[col] = 100.0
              elif col == "carpeta":
                default_c = (
                    filtro_carpeta_grilla
                    if filtro_carpeta_grilla != "-- Mostrar todas las carpetas --"
                    else (
                        carpetas_actuales[0] if carpetas_actuales else "Tareas"
                    )
                )
                df_plan_edit[col] = default_c
              else:
                df_plan_edit[col] = ""

          st.write(
              "💡 **Selecciona opciones en los desplegables (Semestre, Carpeta)"
              " para llenar más rápido. Para agregar una nueva asignación, haz"
              " clic en '+' al final de la tabla:**"
          )

          # Lista de semestres para opción rápida de selección
          opciones_semestres = list(range(1, 13))

          grid_actividades = st.data_editor(
              df_plan_edit,
              column_config={
                  "id": st.column_config.NumberColumn("ID", disabled=True),
                  "semestre": st.column_config.SelectboxColumn(
                      "Semestre", options=opciones_semestres, required=True
                  ),
                  "semana": st.column_config.NumberColumn(
                      "Semana",
                      min_value=1,
                      max_value=52,
                      step=1,
                      required=True,
                  ),
                  "fecha": st.column_config.TextColumn(
                      "Fecha de Entrega (AAAA-MM-DD)", required=True
                  ),
                  "tarea": st.column_config.TextColumn(
                      "Nombre de la Asignación", required=True
                  ),
                  "maximo": st.column_config.NumberColumn(
                      "Puntos Máximos",
                      min_value=1.0,
                      max_value=1000.0,
                      step=1.0,
                      required=True,
                  ),
                  "carpeta": st.column_config.SelectboxColumn(
                      "Carpeta Destino",
                      options=carpetas_actuales,
                      required=True,
                  ),
              },
              num_rows="dynamic",
              use_container_width=True,
              key="editor_grid_plan_actividades_v5",
          )

          if st.button(
              "💾 Guardar Cambios en las Asignaciones",
              key="btn_save_grid_actividades_v5",
          ):
            ids_modificados = set()
            nuevas_asignaciones_mod = []

            next_id = max([t["id"] for t in plan_actual], default=0) + 1

            for _, row in grid_actividades.iterrows():
              nombre_asig = str(row["tarea"]).strip()
              if nombre_asig and nombre_asig != "nan":
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

                f_val = (
                    str(row["fecha"]).strip()
                    if str(row["fecha"]).strip()
                    and str(row["fecha"]).strip() != "nan"
                    else str(date.today())
                )

                raw_c_val = str(row["carpeta"]).strip()
                if raw_c_val in carpetas_actuales:
                  c_val = raw_c_val
                elif filtro_carpeta_grilla != "-- Mostrar todas las carpetas --":
                  c_val = filtro_carpeta_grilla
                else:
                  c_val = (
                      carpetas_actuales[0] if carpetas_actuales else "Tareas"
                  )

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
              # Mantener asignaciones que pertenecían a OTRAS carpetas
              otras_asignaciones = [
                  t
                  for t in plan_actual
                  if t.get("carpeta") != filtro_carpeta_grilla
                  and t["id"] not in ids_modificados
              ]
              lista_final_plan = otras_asignaciones + nuevas_asignaciones_mod
            else:
              lista_final_plan = nuevas_asignaciones_mod

            st.session_state.db["plan_semestres"] = lista_final_plan
            guardar_datos(st.session_state.db)
            st.session_state.mensaje_exito = (
                "✅ ¡Asignaciones guardadas correctamente desde la cuadrícula!"
            )
            st.rerun()

        # =====================================================
        # OPCIÓN 2: BENEFICIARIOS EN CUADRÍCULA
        # =====================================================
        elif "👥 2. Administrar Lista de Beneficiarios" in accion_admin:
          st.markdown(
              "<div class='section-card'><p class='section-card-title'>✏️"
              " Cuadrícula de Beneficiarios</p><p style='margin:3px 0 0"
              " 0;'>Modifica nombres, cambia de semestre o agrega personas"
              " directamente en la cuadrícula.</p></div>",
              unsafe_allow_html=True,
          )

          df_ben_actual = pd.DataFrame(
              st.session_state.db.get("beneficiarios", [])
          )
          if df_ben_actual.empty:
            df_ben_actual = pd.DataFrame(columns=["nombre", "semestre"])

          st.write("💡 **Haz doble clic en cualquier celda para editar:**")

          df_ben_editado = st.data_editor(
              df_ben_actual,
              column_config={
                  "nombre": st.column_config.TextColumn(
                      "Nombre Completo de la Persona", required=True
                  ),
                  "semestre": st.column_config.SelectboxColumn(
                      "Semestre Cursando",
                      options=list(range(1, 13)),
                      required=True,
                  ),
              },
              num_rows="dynamic",
              use_container_width=True,
              key="ben_data_editor_v5",
          )

          if st.button(
              "💾 Guardar Cambios de Beneficiarios", key="btn_save_grid_ben_v5"
          ):
            nuevos_beneficiarios = []
            for _, row in df_ben_editado.iterrows():
              nom = str(row["nombre"]).strip()
              if nom and nom != "nan":
                try:
                  sem = int(row["semestre"])
                except Exception:
                  sem = 1
                nuevos_beneficiarios.append(
                    {"nombre": nom, "semestre": sem}
                )

            st.session_state.db["beneficiarios"] = nuevos_beneficiarios
            guardar_datos(st.session_state.db)
            st.session_state.mensaje_exito = (
                "✅ ¡Lista de beneficiarios actualizada correctamente desde la"
                " cuadrícula!"
            )
            st.rerun()

        # =====================================================
        # OPCIÓN 3: ASIGNAR PUNTAJES / CALIFICACIONES
        # =====================================================
        elif "💯 3. Asignar Puntajes" in accion_admin:
          st.markdown(
              "<div class='section-card'><p class='section-card-title'>💯 Asignar"
              " o Modificar Puntajes</p></div>",
              unsafe_allow_html=True,
          )
          lista_beneficiarios = [
              b["nombre"]
              for b in st.session_state.db.get("beneficiarios", [])
          ]

          if lista_beneficiarios:
            beneficiario_eval = st.selectbox(
                "1. Selecciona a la Persona:",
                lista_beneficiarios,
                key="cal_ben_select_v5",
            )
            beneficiario_obj = next(
                b
                for b in st.session_state.db["beneficiarios"]
                if b["nombre"] == beneficiario_eval
            )
            sem_estudiante = beneficiario_obj["semestre"]

            tareas_disponibles = [
                t
                for t in st.session_state.db["plan_semestres"]
                if t["semestre"] == sem_estudiante
            ]

            if tareas_disponibles:
              opciones_tareas = {
                  f"📁 [{t.get('carpeta', 'Tareas')}] Sem {t['semana']} -"
                  f" {t['tarea']} (Máximo: {t['maximo']} pts)": t
                  for t in tareas_disponibles
              }
              tarea_seleccionada_label = st.selectbox(
                  "2. Selecciona la Asignación:",
                  list(opciones_tareas.keys()),
                  key="cal_act_select_v5",
              )
              tarea_obj = opciones_tareas[tarea_seleccionada_label]

              calif_previa = next(
                  (
                      c
                      for c in st.session_state.db["calificaciones"]
                      if (
                          c.get("beneficiario") == beneficiario_eval
                          or c.get("alumno") == beneficiario_eval
                      )
                      and c["tarea_id"] == tarea_obj["id"]
                  ),
                  None,
              )
              val_defecto = (
                  float(calif_previa["puntaje"]) if calif_previa else 0.0
              )

              puntaje_ingresado = st.number_input(
                  "3. Ingresa el Puntaje Obtenido (Puntaje Máximo Posible:"
                  f" {tarea_obj['maximo']} pts)",
                  min_value=0.0,
                  max_value=float(tarea_obj["maximo"]),
                  value=val_defecto,
                  step=0.5,
                  key="pts_input_v5",
              )

              if st.button("💾 Guardar Puntaje", key="btn_save_calif_v5"):
                if calif_previa:
                  calif_previa["puntaje"] = puntaje_ingresado
                  st.session_state.mensaje_exito = (
                      f"✅ Puntaje actualizado a {puntaje_ingresado} pts para"
                      f" **{beneficiario_eval}** en '{tarea_obj['tarea']}'."
                  )
                else:
                  st.session_state.db["calificaciones"].append({
                      "beneficiario": beneficiario_eval,
                      "tarea_id": tarea_obj["id"],
                      "puntaje": puntaje_ingresado,
                  })
                  st.session_state.mensaje_exito = (
                      f"✅ Puntaje registrado: {puntaje_ingresado} pts para"
                      f" **{beneficiario_eval}** en '{tarea_obj['tarea']}'."
                  )

                guardar_datos(st.session_state.db)
                st.rerun()
            else:
              st.warning(
                  f"⚠️ **{beneficiario_eval}** está en el Semestre"
                  f" {sem_estudiante}, pero aún no hay asignaciones creadas"
                  " para ese semestre."
              )
          else:
            st.info(
                "Primero debes registrar a una persona en la pestaña de"
                " Beneficiarios."
            )


if __name__ == "__main__":
  aplicacion_principal()