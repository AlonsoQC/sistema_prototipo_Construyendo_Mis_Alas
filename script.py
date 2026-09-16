from datetime import date
import json
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# --- MANEJO SEGURO DE SECRETO / VARIABLES DE ENTORNO ---
# Evita que el código se detenga si no existe el archivo secrets.toml
try:
  DB_URL = st.secrets.get("DATABASE_URL", "")
except Exception:
  DB_URL = os.getenv("DATABASE_URL", "")

DATA_FILE = "data_colegio.json"


@st.cache_resource
def get_db_engine():
  if DB_URL:
    # Normaliza la URL para compatibilidad con SQLAlchemy
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


def obtener_datos_defecto():
  return {
      "usuarios": {"admin": {"password": "admin123", "rol": "administrador"}},
      "alumnos": [{"nombre": "Carlos Pérez", "semestre": 1}],
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
          {"alumno": "Carlos Pérez", "tarea_id": 1, "puntaje": 90.0}
      ],
  }


def cargar_datos():
  engine = get_db_engine()

  # 1. Cargar desde PostgreSQL en la nube si hay URL
  if engine:
    try:
      inicializar_db_nube(engine)
      with engine.connect() as conn:
        result = conn.execute(
            text("SELECT datos FROM colegio_datos WHERE id = 1;")
        ).fetchone()

      if result and result[0]:
        datos = result[0]
        if "plan_semestres" not in datos:
          datos["plan_semestres"] = []
        if "calificaciones" not in datos:
          datos["calificaciones"] = []
        return datos
      else:
        datos_defecto = obtener_datos_defecto()
        guardar_datos(datos_defecto)
        return datos_defecto
    except Exception as e:
      st.error(f"Error en base de datos de la nube: {e}")

  # 2. Respaldo local JSON si no hay nube o falla la conexión
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      datos = json.load(f)
      if "plan_semestres" not in datos:
        datos["plan_semestres"] = []
      if "calificaciones" not in datos:
        datos["calificaciones"] = []
      return datos
  else:
    datos_defecto = obtener_datos_defecto()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(datos_defecto, f, ensure_ascii=False, indent=4)
    return datos_defecto


def guardar_datos(datos):
  engine = get_db_engine()

  # 1. Guardar en la nube si está disponible
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


def aplicacion_principal():
  st.title("🎓 Sistema Escolar por Semestres y Semanas")

  if "db" not in st.session_state:
    st.session_state.db = cargar_datos()

  if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

  if "rol_logueado" not in st.session_state:
    st.session_state.rol_logueado = None

  # --- AUTENTICACIÓN ---
  if st.session_state.usuario_logueado is None:
    st.subheader("Acceso al Sistema")
    opcion_auth = st.radio(
        "Selecciona una opción", ["Iniciar Sesión", "Crear Cuenta"]
    )

    if opcion_auth == "Iniciar Sesión":
      usuario = st.text_input("Nombre de Usuario")
      password = st.text_input("Contraseña", type="password")
      if st.button("Entrar"):
        usuarios = st.session_state.db["usuarios"]
        if usuario in usuarios and usuarios[usuario]["password"] == password:
          st.session_state.usuario_logueado = usuario
          st.session_state.rol_logueado = usuarios[usuario]["rol"]
          st.success(f"¡Bienvenido {usuario}!")
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos.")

    elif opcion_auth == "Crear Cuenta":
      nuevo_usuario = st.text_input("Elige un Nombre de Usuario")
      nueva_pass = st.text_input("Elige una Contraseña", type="password")
      rol = st.selectbox("Tipo de Cuenta", ["administrador", "consultor"])

      if st.button("Registrar Cuenta"):
        if nuevo_usuario in st.session_state.db["usuarios"]:
          st.warning("El usuario ya existe.")
        elif nuevo_usuario == "" or nueva_pass == "":
          st.warning("Completa todos los campos.")
        else:
          st.session_state.db["usuarios"][nuevo_usuario] = {
              "password": nueva_pass,
              "rol": rol,
          }
          guardar_datos(st.session_state.db)
          st.success("Cuenta creada exitosamente.")

  # --- INTERFAZ PRINCIPAL ---
  else:
    col_user, col_logout = st.columns([4, 1])
    with col_user:
      st.info(
          f"👤 Usuario: **{st.session_state.usuario_logueado}** | Rol:"
          f" **{st.session_state.rol_logueado.upper()}**"
      )
    with col_logout:
      if st.button("Cerrar Sesión"):
        st.session_state.usuario_logueado = None
        st.session_state.rol_logueado = None
        st.rerun()

    st.markdown("---")

    tab_buscar_alumno, tab_buscar_semestre, tab_admin = st.tabs([
        "🔍 Buscar por Alumno",
        "📚 Plan y Progreso por Semestre",
        "⚙️ Panel de Administración",
    ])

    # 1. BUSCADOR POR ALUMNO
    with tab_buscar_alumno:
      st.subheader("Búsqueda y Avance por Alumno")
      nombres_alumnos = [a["nombre"] for a in st.session_state.db["alumnos"]]

      if nombres_alumnos:
        alumno_sel = st.selectbox(
            "Selecciona un alumno:", ["-- Seleccionar --"] + nombres_alumnos
        )

        if alumno_sel != "-- Seleccionar --":
          alumno_info = next(
              a for a in st.session_state.db["alumnos"] if a["nombre"] == alumno_sel
          )
          semestre_alumno = alumno_info["semestre"]

          tareas_planeadas = [
              t
              for t in st.session_state.db["plan_semestres"]
              if t["semestre"] == semestre_alumno
          ]

          st.write(
              f"### Expediente: **{alumno_sel}** (Semestre {semestre_alumno})"
          )

          if tareas_planeadas:
            reporte = []
            pts_obtenidos_total = 0
            pts_maximos_total = 0

            for t in tareas_planeadas:
              calif = next(
                  (
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c["alumno"] == alumno_sel and c["tarea_id"] == t["id"]
                  ),
                  None,
              )

              if calif is not None:
                estado = "Calificado"
                puntaje_str = f"{calif['puntaje']} / {t['maximo']}"
                pts_obtenidos_total += calif["puntaje"]
              else:
                estado = "Pendiente"
                puntaje_str = f"0 / {t['maximo']}"

              pts_maximos_total += t["maximo"]

              reporte.append({
                  "Semana": f"Semana {t['semana']}",
                  "Fecha Programada": t["fecha"],
                  "Tarea / Actividad": t["tarea"],
                  "Estado": estado,
                  "Calificación": puntaje_str,
              })

            df_reporte = pd.DataFrame(reporte)
            st.dataframe(df_reporte, use_container_width=True)

            col_m1, col_m2 = st.columns(2)
            with col_m1:
              st.metric(
                  "Puntaje Acumulado",
                  f"{pts_obtenidos_total:.1f} / {pts_maximos_total:.1f} pts",
              )
            with col_m2:
              porcentaje = (
                  (pts_obtenidos_total / pts_maximos_total * 100)
                  if pts_maximos_total > 0
                  else 0
              )
              st.metric("Progreso Total del Semestre", f"{porcentaje:.1f}%")
          else:
            st.warning(
                f"No hay tareas programadas aún para el Semestre"
                f" {semestre_alumno}."
            )
      else:
        st.info("No hay alumnos registrados.")

    # 2. BUSCADOR POR SEMESTRE
    with tab_buscar_semestre:
      st.subheader("Plan Global por Semestre")
      semestres_disponibles = sorted(
          list(
              set(
                  [a["semestre"] for a in st.session_state.db["alumnos"]]
                  + [t["semestre"] for t in st.session_state.db["plan_semestres"]]
              )
          )
      )

      if semestres_disponibles:
        sem_sel = st.selectbox("Selecciona Semestre:", semestres_disponibles)

        st.markdown(f"#### 📅 Plan de Tareas del Semestre {sem_sel}")
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
              "Fecha Entrega",
              "Tarea Programada",
              "Puntaje Máximo",
          ]
          st.table(df_plan.sort_values(by="Semana"))
        else:
          st.info(
              "No se han dado de alta tareas para este semestre en el plan de"
              " estudios."
          )

        st.markdown(f"#### 👥 Alumnos Inscritos en Semestre {sem_sel}")
        alumnos_sem = [
            a["nombre"]
            for a in st.session_state.db["alumnos"]
            if a["semestre"] == sem_sel
        ]
        if alumnos_sem:
          st.write(", ".join([f"**{nombre}**" for nombre in alumnos_sem]))
        else:
          st.info("No hay alumnos registrados en este semestre.")
      else:
        st.info("No hay semestres registrados en el sistema.")

    # 3. PANEL DE ADMINISTRACIÓN
    with tab_admin:
      if st.session_state.rol_logueado != "administrador":
        st.error("🚫 Se requieren permisos de administrador.")
      else:
        st.subheader("Gestión del Sistema Escolar")

        admin_subtab1, admin_subtab2, admin_subtab3 = st.tabs([
            "📅 Plan de Semestres (Tareas)",
            "👤 Registrar Alumnos",
            "💯 Asignar Calificaciones",
        ])

        with admin_subtab1:
          st.markdown(
              "#### Crear Tarea Programada (Aplica a todos los alumnos del"
              " semestre)"
          )
          col1, col2 = st.columns(2)
          with col1:
            sem_plan = st.number_input(
                "Semestre", min_value=1, max_value=12, value=1, key="sem_plan"
            )
            semana_num = st.number_input(
                "Número de Semana",
                min_value=1,
                max_value=30,
                value=1,
                key="sem_num",
            )
            fecha_entrega = st.date_input(
                "Fecha de Entrega", value=date.today()
            )

          with col2:
            nombre_tarea_plan = st.text_input(
                "Nombre de la Tarea / Actividad"
            )
            max_pts_plan = st.number_input(
                "Puntaje Máximo", min_value=1.0, value=100.0, step=5.0
            )

          if st.button("Guardar en Plan de Semestre"):
            if nombre_tarea_plan.strip() != "":
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
              st.success(
                  f"Tarea '{nombre_tarea_plan}' agregada al Semestre"
                  f" {sem_plan} (Semana {semana_num})."
              )
              st.rerun()
            else:
              st.warning("Escribe el nombre de la tarea.")

        with admin_subtab2:
          st.markdown("#### Registrar Nuevo Alumno")
          nuevo_alumno = st.text_input("Nombre Completo del Alumno")
          semestre_alumno = st.number_input(
              "Asignar Semestre", min_value=1, max_value=12, value=1
          )

          if st.button("Guardar Alumno"):
            if nuevo_alumno.strip() != "":
              st.session_state.db["alumnos"].append(
                  {"nombre": nuevo_alumno.strip(), "semestre": semestre_alumno}
              )
              guardar_datos(st.session_state.db)
              st.success(
                  f"Alumno **{nuevo_alumno}** registrado en Semestre"
                  f" {semestre_alumno}."
              )
              st.rerun()
            else:
              st.warning("Escribe el nombre del alumno.")

        with admin_subtab3:
          st.markdown("#### Evaluar Tareas Registradas")
          lista_alumnos = [a["nombre"] for a in st.session_state.db["alumnos"]]

          if lista_alumnos:
            alumno_eval = st.selectbox("Seleccionar Alumno", lista_alumnos)
            alumno_obj = next(
                a
                for a in st.session_state.db["alumnos"]
                if a["nombre"] == alumno_eval
            )
            sem_estudiante = alumno_obj["semestre"]

            tareas_disponibles = [
                t
                for t in st.session_state.db["plan_semestres"]
                if t["semestre"] == sem_estudiante
            ]

            if tareas_disponibles:
              opciones_tareas = {
                  f"Semana {t['semana']} - {t['tarea']} (Máx: {t['maximo']} pts)": t
                  for t in tareas_disponibles
              }
              tarea_seleccionada_label = st.selectbox(
                  "Seleccionar Tarea a Calificar", list(opciones_tareas.keys())
              )
              tarea_obj = opciones_tareas[tarea_seleccionada_label]

              calif_previa = next(
                  (
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c["alumno"] == alumno_eval
                      and c["tarea_id"] == tarea_obj["id"]
                  ),
                  None,
              )
              val_defecto = (
                  float(calif_previa["puntaje"]) if calif_previa else 0.0
              )

              puntaje_ingresado = st.number_input(
                  f"Puntaje Obtenido (Máximo: {tarea_obj['maximo']})",
                  min_value=0.0,
                  max_value=float(tarea_obj["maximo"]),
                  value=val_defecto,
                  step=0.5,
              )

              if st.button("Guardar Calificación"):
                if calif_previa:
                  calif_previa["puntaje"] = puntaje_ingresado
                  st.info(
                      f"Calificación actualizada para **{tarea_obj['tarea']}**."
                  )
                else:
                  st.session_state.db["calificaciones"].append({
                      "alumno": alumno_eval,
                      "tarea_id": tarea_obj["id"],
                      "puntaje": puntaje_ingresado,
                  })
                  st.success(
                      f"Calificación guardada para **{tarea_obj['tarea']}**."
                  )

                guardar_datos(st.session_state.db)
                st.rerun()
            else:
              st.warning(
                  f"No hay tareas configuradas en el Plan del Semestre"
                  f" {sem_estudiante}. Ve a la pestaña 'Plan de Semestres' para"
                  " crearlas."
              )
          else:
            st.info("Primero registra a un alumno.")


if __name__ == "__main__":
  aplicacion_principal()