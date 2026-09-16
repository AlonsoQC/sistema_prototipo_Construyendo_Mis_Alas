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

# Estilos CSS corregidos para garantizar legibilidad completa en modo claro y oscuro
CUSTOM_CSS = """
<style>
    /* Fondo blanco general */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* Forzar texto oscuro de alto contraste en etiquetas, párrafos y títulos */
    p, label, span, h1, h2, h3, h4, .stMarkdown, .stWidgetLabel label {
        color: #0F172A !important;
    }

    /* Título Principal */
    h1 {
        color: #0284C7 !important;
        font-weight: 800 !important;
    }

    /* Pestañas (Tabs): Fondo del contenedor */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #F1F5F9 !important;
        padding: 8px !important;
        border-radius: 12px !important;
    }

    /* Pestañas INACTIVAS (Fondo claro y texto gris oscuro visible) */
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 8px 16px !important;
    }
    
    .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    /* Pestaña ACTIVADA (Fondo azul y texto blanco brillante) */
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }

    .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Opciones de Radio Buttons (Agregar/Editar) */
    div[role="radiogroup"] label p, div[role="radiogroup"] label span {
        color: #0F172A !important;
        font-weight: 600 !important;
    }

    /* Botones de Acción (Fondo azul y texto blanco obligatorio) */
    .stButton > button {
        border-radius: 10px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.4rem !important;
        border: none !important;
        background-color: #2563EB !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important;
    }
    
    .stButton > button p, .stButton > button span {
        color: #FFFFFF !important;
    }

    /* Cajas de Métricas */
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

# --- MANEJO SEGURO DE SECRETO / VARIABLES DE ENTORNO ---
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

  return datos


def obtener_datos_defecto():
  return {
      "usuarios": {"admin": {"password": "admin123", "rol": "administrador"}},
      "beneficiarios": [{"nombre": "Carlos Pérez", "semestre": 1}],
      "plan_semestres": [
          {
              "id": 1,
              "semestre": 1,
              "semana": 1,
              "fecha": "2026-09-01",
              "tarea": "Examen Diagnóstico",
              "maximo": 100,
          },
          {
              "id": 2,
              "semestre": 1,
              "semana": 2,
              "fecha": "2026-09-08",
              "tarea": "Proyecto Parcial 1",
              "maximo": 100,
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
    st.subheader("🔑 Ingreso al Sistema")
    st.write("Selecciona una opción para comenzar de forma muy sencilla.")
    mostrar_mensaje_exito()

    opcion_auth = st.radio(
        "¿Qué deseas hacer?",
        ["Entrar a mi cuenta", "Crear una cuenta nueva"],
        horizontal=True,
    )

    if opcion_auth == "Entrar a mi cuenta":
      col_in1, col_in2 = st.columns([1, 1])
      with col_in1:
        usuario = st.text_input("👤 Tu Nombre de Usuario")
        password = st.text_input("🔒 Tu Contraseña", type="password")

        if st.button("🚀 Entrar al Sistema"):
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
        nuevo_usuario = st.text_input("👤 Elige tu Nombre de Usuario")
        nueva_pass = st.text_input("🔒 Elige una Contraseña", type="password")
        rol = st.selectbox(
            "📌 ¿Qué tipo de usuario serás?",
            ["consultor", "administrador"],
            help=(
                "Consultor: Solo para ver información. Administrador: Para"
                " modificar datos."
            ),
        )

        codigo_admin = ""
        if rol == "administrador":
          codigo_admin = st.text_input(
              "🔑 Código Especial de Administrador",
              type="password",
              help="Código secreto para administradores (123456789)",
          )

        if st.button("✨ Registrar Mi Cuenta"):
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
          "<div style='background-color:#E0F2FE; padding:12px;"
          " border-radius:10px; color:#0369A1; font-weight:bold;"
          " font-size:1.1rem;'>👤 Sesión activa:"
          f" <b>{st.session_state.usuario_logueado}</b> | Rol:"
          f" <b>{st.session_state.rol_logueado.upper()}</b></div>",
          unsafe_allow_html=True,
      )
    with col_logout:
      if st.button("🚪 Cerrar Sesión"):
        st.session_state.usuario_logueado = None
        st.session_state.rol_logueado = None
        st.rerun()

    st.write("")
    mostrar_mensaje_exito()

    # NAVEGACIÓN PRINCIPAL CON ICONOS Y LENGUAJE SIMPLE
    tab_buscar_beneficiario, tab_buscar_semestre, tab_admin = st.tabs([
        "🔍 Ver Avance por Persona",
        "📚 Ver Plan General",
        "⚙️ Administración y Registro",
    ])

    # ---------------------------------------------------------
    # 1. BUSCADOR POR BENEFICIARIO
    # ---------------------------------------------------------
    with tab_buscar_beneficiario:
      st.markdown("### 📋 Calificaciones y Avance Individual")
      st.write(
          "Selecciona el nombre de la persona para ver cómo va con sus"
          " puntajes."
      )

      nombres_beneficiarios = [
          b["nombre"] for b in st.session_state.db["beneficiarios"]
      ]

      if nombres_beneficiarios:
        beneficiario_sel = st.selectbox(
            "👉 Selecciona un Beneficiario:",
            ["-- Haz clic aquí para elegir --"] + nombres_beneficiarios,
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
                  "Semana": f"Semana {t['semana']}",
                  "Fecha Estimada": t["fecha"],
                  "Nombre de la Actividad": t["tarea"],
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
                f"Aún no hay actividades asignadas para el Semestre"
                f" {semestre_beneficiario}."
            )
      else:
        st.info("No hay beneficiarios registrados todavía.")

    # ---------------------------------------------------------
    # 2. BUSCADOR POR SEMESTRE
    # ---------------------------------------------------------
    with tab_buscar_semestre:
      st.markdown("### 📅 Plan Completo de Actividades por Semestre")
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
            "👉 Elige el Semestre que deseas consultar:", semestres_disponibles
        )

        st.markdown(
            f"#### 📝 Actividades Programadas para el Semestre {sem_sel}"
        )
        plan_sem = [
            t
            for t in st.session_state.db["plan_semestres"]
            if t["semestre"] == sem_sel
        ]

        if plan_sem:
          df_plan = pd.DataFrame(plan_sem)[
              ["semana", "fecha", "tarea", "maximo"]
          ]
          df_plan.columns = [
              "Semana",
              "Fecha de Entrega",
              "Actividad",
              "Puntaje Máximo",
          ]
          st.table(df_plan.sort_values(by="Semana"))
        else:
          st.info("No hay actividades registradas en este semestre.")

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
    # 3. PANEL DE ADMINISTRACIÓN (MÓDULOS DE GESTIÓN SIMPLE)
    # ---------------------------------------------------------
    with tab_admin:
      if st.session_state.rol_logueado != "administrador":
        st.error("🚫 Esta sección requiere permisos de Administrador.")
      else:
        st.markdown("### ⚙️ Panel de Control y Administración")
        st.write(
            "Elige la tarea que deseas realizar con los botones de abajo:"
        )

        # Sub-pestañas internas limpias y sin saltos bruscos de pantalla
        admin_tab_ben, admin_tab_act, admin_tab_cal = st.tabs([
            "👥 1. Beneficiarios (Agregar / Editar)",
            "📅 2. Actividades (Agregar / Editar)",
            "💯 3. Calificaciones (Asignar Puntajes)",
        ])

        # =====================================================
        # SUBTAB 1: GESTIÓN COMPLETA DE BENEFICIARIOS
        # =====================================================
        with admin_tab_ben:
          sub_ben = st.radio(
              "¿Qué quieres hacer con los beneficiarios?",
              [
                  "➕ Agregar Nuevo Beneficiario",
                  "✏️ Editar o Eliminar Existente",
              ],
              horizontal=True,
              key="sub_ben_radio",
          )

          st.markdown("---")

          if sub_ben == "➕ Agregar Nuevo Beneficiario":
            st.markdown("#### ➕ Registrar una Nueva Persona")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
              nuevo_beneficiario = st.text_input(
                  "Nombre Completo de la Persona", key="nuevo_ben_input"
              )
            with col_b2:
              semestre_beneficiario = st.number_input(
                  "Semestre que cursará",
                  min_value=1,
                  max_value=12,
                  value=1,
                  key="sem_ben_input",
              )

            if st.button("💾 Guardar Nueva Persona", key="btn_add_ben"):
              nombre_limpio = nuevo_beneficiario.strip()
              if nombre_limpio == "":
                st.warning("⚠️ Por favor escribe el nombre de la persona.")
              else:
                nombres_existentes = [
                    b["nombre"].lower()
                    for b in st.session_state.db["beneficiarios"]
                ]
                if nombre_limpio.lower() in nombres_existentes:
                  st.warning(
                      f"⚠️ La persona **{nombre_limpio}** ya está registrada."
                  )
                else:
                  st.session_state.db["beneficiarios"].append({
                      "nombre": nombre_limpio,
                      "semestre": semestre_beneficiario,
                  })
                  guardar_datos(st.session_state.db)
                  st.session_state.mensaje_exito = (
                      f"✅ ¡**{nombre_limpio}** guardado(a) correctamente!"
                  )
                  st.rerun()

          elif sub_ben == "✏️ Editar o Eliminar Existente":
            st.markdown("#### ✏️ Cambiar Nombre o Eliminar una Persona")
            lista_ben = st.session_state.db["beneficiarios"]

            if lista_ben:
              dict_ben = {
                  f"{b['nombre']} (Semestre {b['semestre']})": b for b in lista_ben
              }
              ben_sel_label = st.selectbox(
                  "Selecciona la persona que deseas modificar:",
                  list(dict_ben.keys()),
              )
              ben_a_editar = dict_ben[ben_sel_label]

              col_be1, col_be2 = st.columns(2)
              with col_be1:
                nombre_editado = st.text_input(
                    "Editar Nombre Completo",
                    value=ben_a_editar["nombre"],
                    key="nombre_ben_edit",
                )
              with col_be2:
                semestre_editado = st.number_input(
                    "Editar Semestre",
                    min_value=1,
                    max_value=12,
                    value=int(ben_a_editar["semestre"]),
                    key="sem_ben_edit",
                )

              col_btn_be1, col_btn_be2 = st.columns(2)
              with col_btn_be1:
                if st.button(
                    "💾 Guardar Cambios en Nombre / Semestre",
                    key="btn_update_ben",
                ):
                  if nombre_editado.strip() == "":
                    st.warning("⚠️ El nombre no puede quedar vacío.")
                  else:
                    nombre_anterior = ben_a_editar["nombre"]
                    nuevo_nombre = nombre_editado.strip()

                    # Actualizar en la lista de beneficiarios
                    ben_a_editar["nombre"] = nuevo_nombre
                    ben_a_editar["semestre"] = semestre_editado

                    # Actualizar sus calificaciones registradas si cambió de nombre
                    for c in st.session_state.db["calificaciones"]:
                      if (
                          c.get("beneficiario") == nombre_anterior
                          or c.get("alumno") == nombre_anterior
                      ):
                        c["beneficiario"] = nuevo_nombre

                    guardar_datos(st.session_state.db)
                    st.session_state.mensaje_exito = (
                        f"✅ Datos de **{nuevo_nombre}** actualizados"
                        " correctamente."
                    )
                    st.rerun()

              with col_btn_be2:
                if st.button(
                    "🗑️ Eliminar a esta Persona del Sistema",
                    key="btn_delete_ben",
                ):
                  nombre_del = ben_a_editar["nombre"]
                  # Eliminar de beneficiarios
                  st.session_state.db["beneficiarios"] = [
                      b
                      for b in st.session_state.db["beneficiarios"]
                      if b["nombre"] != nombre_del
                  ]
                  # Eliminar sus calificaciones
                  st.session_state.db["calificaciones"] = [
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c.get("beneficiario") != nombre_del
                      and c.get("alumno") != nombre_del
                  ]
                  guardar_datos(st.session_state.db)
                  st.session_state.mensaje_exito = (
                      f"✅ **{nombre_del}** fue eliminado(a) del sistema."
                  )
                  st.rerun()
            else:
              st.info("No hay beneficiarios registrados para editar.")

        # =====================================================
        # SUBTAB 2: GESTIÓN DE ACTIVIDADES (PLAN DE SEMESTRES)
        # =====================================================
        with admin_tab_act:
          sub_act = st.radio(
              "¿Qué deseas hacer con las actividades?",
              [
                  "➕ Crear Nueva Actividad",
                  "✏️ Editar o Eliminar Actividad Existente",
              ],
              horizontal=True,
              key="sub_act_radio",
          )

          st.markdown("---")

          if sub_act == "➕ Crear Nueva Actividad":
            st.markdown("#### ➕ Registrar Nueva Actividad")
            col1, col2 = st.columns(2)
            with col1:
              sem_plan = st.number_input(
                  "Semestre",
                  min_value=1,
                  max_value=12,
                  value=1,
                  key="sem_plan_new",
              )
              semana_num = st.number_input(
                  "Número de Semana",
                  min_value=1,
                  max_value=30,
                  value=1,
                  key="sem_num_new",
              )
              fecha_entrega = st.date_input(
                  "Fecha Estimada", value=date.today(), key="fecha_new"
              )

            with col2:
              nombre_tarea_plan = st.text_input(
                  "Nombre de la Actividad", key="nombre_act_new"
              )
              max_pts_plan = st.number_input(
                  "Puntaje Máximo (Valor de la tarea)",
                  min_value=1.0,
                  value=100.0,
                  step=5.0,
                  key="max_pts_new",
              )

            if st.button("💾 Guardar Actividad en el Plan", key="btn_add_act"):
              if nombre_tarea_plan.strip() == "":
                st.warning("⚠️ Escribe el nombre de la actividad.")
              else:
                repetido = any(
                    t["semestre"] == sem_plan
                    and t["tarea"].lower() == nombre_tarea_plan.strip().lower()
                    for t in st.session_state.db["plan_semestres"]
                )
                if repetido:
                  st.warning(
                      "⚠️ Ya existe una actividad con ese mismo nombre en este"
                      " semestre."
                  )
                else:
                  nuevo_id = (
                      max(
                          [
                              t["id"]
                              for t in st.session_state.db["plan_semestres"]
                          ],
                          default=0,
                      )
                      + 1
                  )
                  st.session_state.db["plan_semestres"].append({
                      "id": nuevo_id,
                      "semestre": sem_plan,
                      "semana": semana_num,
                      "fecha": str(fecha_entrega),
                      "tarea": nombre_tarea_plan.strip(),
                      "maximo": max_pts_plan,
                  })
                  guardar_datos(st.session_state.db)
                  st.session_state.mensaje_exito = (
                      f"✅ Actividad '{nombre_tarea_plan.strip()}' guardada"
                      " exitosamente."
                  )
                  st.rerun()

          elif sub_act == "✏️ Editar o Eliminar Actividad Existente":
            st.markdown("#### ✏️ Modificar o Borrar Actividades Creadas")
            tareas_existentes = st.session_state.db["plan_semestres"]

            if tareas_existentes:
              dict_tareas = {
                  f"Semestre {t['semestre']} - Sem {t['semana']}: {t['tarea']}"
                  f" (ID: {t['id']})": t
                  for t in tareas_existentes
              }
              tarea_sel_label = st.selectbox(
                  "Selecciona la actividad a modificar:",
                  list(dict_tareas.keys()),
              )
              tarea_a_editar = dict_tareas[tarea_sel_label]

              col_e1, col_e2 = st.columns(2)
              with col_e1:
                sem_edit = st.number_input(
                    "Semestre",
                    min_value=1,
                    max_value=12,
                    value=int(tarea_a_editar["semestre"]),
                    key="sem_edit",
                )
                semana_edit = st.number_input(
                    "Número de Semana",
                    min_value=1,
                    max_value=30,
                    value=int(tarea_a_editar["semana"]),
                    key="sem_num_edit",
                )
                try:
                  fecha_val = date.fromisoformat(tarea_a_editar["fecha"])
                except Exception:
                  fecha_val = date.today()
                fecha_edit = st.date_input(
                    "Fecha Estimada", value=fecha_val, key="fecha_edit"
                )

              with col_e2:
                nombre_edit = st.text_input(
                    "Nombre de la Actividad",
                    value=tarea_a_editar["tarea"],
                    key="nombre_edit",
                )
                max_edit = st.number_input(
                    "Puntaje Máximo",
                    min_value=1.0,
                    value=float(tarea_a_editar["maximo"]),
                    step=5.0,
                    key="max_edit",
                )

              col_b1, col_b2 = st.columns(2)
              with col_b1:
                if st.button(
                    "💾 Guardar Cambios en esta Actividad", key="btn_update_act"
                ):
                  if nombre_edit.strip() == "":
                    st.warning(
                        "⚠️ El nombre de la actividad no puede estar vacío."
                    )
                  else:
                    tarea_a_editar["semestre"] = sem_edit
                    tarea_a_editar["semana"] = semana_edit
                    tarea_a_editar["fecha"] = str(fecha_edit)
                    tarea_a_editar["tarea"] = nombre_edit.strip()
                    tarea_a_editar["maximo"] = max_edit
                    guardar_datos(st.session_state.db)
                    st.session_state.mensaje_exito = (
                        f"✅ Actividad '{nombre_edit.strip()}' actualizada"
                        " correctamente."
                    )
                    st.rerun()

              with col_b2:
                if st.button(
                    "🗑️ Eliminar esta Actividad", key="btn_delete_act"
                ):
                  st.session_state.db["plan_semestres"] = [
                      t
                      for t in st.session_state.db["plan_semestres"]
                      if t["id"] != tarea_a_editar["id"]
                  ]
                  st.session_state.db["calificaciones"] = [
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c["tarea_id"] != tarea_a_editar["id"]
                  ]
                  guardar_datos(st.session_state.db)
                  st.session_state.mensaje_exito = (
                      "✅ Actividad eliminada correctamente."
                  )
                  st.rerun()
            else:
              st.info("No hay actividades para editar.")

        # =====================================================
        # SUBTAB 3: ASIGNACIÓN DE CALIFICACIONES
        # =====================================================
        with admin_tab_cal:
          st.markdown("#### 💯 Asignar o Cambiar Puntaje")
          lista_beneficiarios = [
              b["nombre"] for b in st.session_state.db["beneficiarios"]
          ]

          if lista_beneficiarios:
            beneficiario_eval = st.selectbox(
                "1. Selecciona a la Persona:",
                lista_beneficiarios,
                key="cal_ben_select",
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
                  f"Semana {t['semana']} - {t['tarea']} (Máximo:"
                  f" {t['maximo']} pts)": t
                  for t in tareas_disponibles
              }
              tarea_seleccionada_label = st.selectbox(
                  "2. Selecciona la Actividad:",
                  list(opciones_tareas.keys()),
                  key="cal_act_select",
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
                  key="pts_input",
              )

              if st.button("💾 Guardar Puntaje", key="btn_save_calif"):
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
                  f" {sem_estudiante}, pero aún no hay actividades creadas para"
                  " ese semestre."
              )
          else:
            st.info(
                "Primero debes registrar a una persona en la pestaña de"
                " Beneficiarios."
            )


if __name__ == "__main__":
  aplicacion_principal()