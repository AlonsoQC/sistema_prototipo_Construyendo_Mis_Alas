from datetime import date
import json
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

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

  # Migración de estructura anterior (alumnos -> beneficiarios)
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

  # 1. Cargar desde la nube (PostgreSQL)
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
  st.title("🎓 Sistema de puntaje Construyendo mis Alas")

  if "db" not in st.session_state:
    st.session_state.db = cargar_datos()

  if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

  if "rol_logueado" not in st.session_state:
    st.session_state.rol_logueado = None

  # --- AUTENTICACIÓN ---
  if st.session_state.usuario_logueado is None:
    st.subheader("Acceso al Sistema")
    mostrar_mensaje_exito()

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
          st.session_state.mensaje_exito = f"✅ ¡Bienvenido(a) {usuario}!"
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos.")

    elif opcion_auth == "Crear Cuenta":
      nuevo_usuario = st.text_input("Elige un Nombre de Usuario")
      nueva_pass = st.text_input("Elige una Contraseña", type="password")
      rol = st.selectbox("Tipo de Cuenta", ["consultor", "administrador"])

      codigo_admin = ""
      if rol == "administrador":
        codigo_admin = st.text_input(
            "Código de Administrador",
            type="password",
            help=(
                "Código requerido para crear cuenta de administrador"
                " (123456789)"
            ),
        )

      if st.button("Registrar Cuenta"):
        if nuevo_usuario.strip() == "" or nueva_pass.strip() == "":
          st.warning("Completa todos los campos obligatorios.")
        elif nuevo_usuario in st.session_state.db["usuarios"]:
          st.warning("⚠️ El nombre de usuario ya existe. Elige otro.")
        elif rol == "administrador" and codigo_admin != "123456789":
          st.error(
              "🚫 Código de administrador incorrecto. No se creó la cuenta."
          )
        else:
          st.session_state.db["usuarios"][nuevo_usuario] = {
              "password": nueva_pass,
              "rol": rol,
          }
          guardar_datos(st.session_state.db)
          st.session_state.mensaje_exito = "✅ Cuenta registrada exitosamente."
          st.rerun()

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
    mostrar_mensaje_exito()

    tab_buscar_beneficiario, tab_buscar_semestre, tab_admin = st.tabs([
        "🔍 Buscar por Beneficiario",
        "📚 Plan y Progreso por Semestre",
        "⚙️ Panel de Administración",
    ])

    # ---------------------------------------------------------
    # 1. BUSCADOR POR BENEFICIARIO
    # ---------------------------------------------------------
    with tab_buscar_beneficiario:
      st.subheader("Búsqueda y Avance por Beneficiario")
      nombres_beneficiarios = [
          b["nombre"] for b in st.session_state.db["beneficiarios"]
      ]

      if nombres_beneficiarios:
        beneficiario_sel = st.selectbox(
            "Selecciona un beneficiario:",
            ["-- Seleccionar --"] + nombres_beneficiarios,
        )

        if beneficiario_sel != "-- Seleccionar --":
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

          st.write(
              f"### Expediente: **{beneficiario_sel}** (Semestre"
              f" {semestre_beneficiario})"
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
                      if c.get("beneficiario", c.get("alumno"))
                      == beneficiario_sel
                      and c["tarea_id"] == t["id"]
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
                  "Actividad": t["tarea"],
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
                f"No hay actividades programadas aún para el Semestre"
                f" {semestre_beneficiario}."
            )
      else:
        st.info("No hay beneficiarios registrados.")

    # ---------------------------------------------------------
    # 2. BUSCADOR POR SEMESTRE
    # ---------------------------------------------------------
    with tab_buscar_semestre:
      st.subheader("Plan Global por Semestre")
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
        sem_sel = st.selectbox("Selecciona Semestre:", semestres_disponibles)

        st.markdown(f"#### 📅 Plan de Actividades del Semestre {sem_sel}")
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
              "Actividad Programada",
              "Puntaje Máximo",
          ]
          st.table(df_plan.sort_values(by="Semana"))
        else:
          st.info(
              "No se han dado de alta actividades para este semestre en el"
              " plan."
          )

        st.markdown(f"#### 👥 Beneficiarios Inscritos en Semestre {sem_sel}")
        beneficiarios_sem = [
            b["nombre"]
            for b in st.session_state.db["beneficiarios"]
            if b["semestre"] == sem_sel
        ]
        if beneficiarios_sem:
          st.write(", ".join([f"**{nombre}**" for nombre in beneficiarios_sem]))
        else:
          st.info("No hay beneficiarios registrados en este semestre.")
      else:
        st.info("No hay semestres registrados en el sistema.")

    # ---------------------------------------------------------
    # 3. PANEL DE ADMINISTRACIÓN
    # ---------------------------------------------------------
    with tab_admin:
      if st.session_state.rol_logueado != "administrador":
        st.error("🚫 Se requieren permisos de administrador.")
      else:
        st.subheader("Gestión del Sistema")

        admin_subtab1, admin_subtab2, admin_subtab3 = st.tabs([
            "📅 Plan de Semestres (Actividades)",
            "👤 Registrar Beneficiarios",
            "💯 Asignar Calificaciones",
        ])

        # -----------------------------------------------------
        # SUBTAB 1: PLAN DE SEMESTRES Y EDICIÓN DE ACTIVIDADES
        # -----------------------------------------------------
        with admin_subtab1:
          modo_actividad = st.radio(
              "Selecciona la acción a realizar:",
              [
                  "➕ Crear Nueva Actividad",
                  "✏️ Editar / Modificar Actividad Existente",
              ],
              horizontal=True,
          )

          if modo_actividad == "➕ Crear Nueva Actividad":
            st.markdown("#### Crear Actividad Programada")
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
                  "Fecha de Entrega", value=date.today(), key="fecha_new"
              )

            with col2:
              nombre_tarea_plan = st.text_input(
                  "Nombre de la Actividad", key="nombre_act_new"
              )
              max_pts_plan = st.number_input(
                  "Puntaje Máximo",
                  min_value=1.0,
                  value=100.0,
                  step=5.0,
                  key="max_pts_new",
              )

            if st.button("Guardar en Plan de Semestre", key="btn_add_act"):
              if nombre_tarea_plan.strip() == "":
                st.warning("Escribe el nombre de la actividad.")
              else:
                repetido = any(
                    t["semestre"] == sem_plan
                    and t["tarea"].lower() == nombre_tarea_plan.strip().lower()
                    for t in st.session_state.db["plan_semestres"]
                )
                if repetido:
                  st.warning(
                      "⚠️ Ya existe una actividad con ese mismo nombre en este"
                      " semestre para evitar duplicados."
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
                      f"✅ Actividad '{nombre_tarea_plan.strip()}' agregada"
                      f" exitosamente al Semestre {sem_plan} (Semana"
                      f" {semana_num})."
                  )
                  st.rerun()

          elif modo_actividad == "✏️ Editar / Modificar Actividad Existente":
            st.markdown("#### Modificar o Eliminar Actividades Pasadas")
            tareas_existentes = st.session_state.db["plan_semestres"]

            if tareas_existentes:
              dict_tareas = {
                  f"Semestre {t['semestre']} - Sem {t['semana']}: {t['tarea']}"
                  f" (ID: {t['id']})": t
                  for t in tareas_existentes
              }
              tarea_sel_label = st.selectbox(
                  "Selecciona la actividad que deseas editar:",
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
                    "Fecha de Entrega", value=fecha_val, key="fecha_edit"
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
                btn_actualizar = st.button(
                    "💾 Guardar Cambios de la Actividad", key="btn_update_act"
                )
              with col_b2:
                btn_eliminar = st.button(
                    "🗑️ Eliminar Actividad", key="btn_delete_act"
                )

              if btn_actualizar:
                if nombre_edit.strip() == "":
                  st.warning("El nombre de la actividad no puede estar vacío.")
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

              if btn_eliminar:
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
              st.info(
                  "No hay actividades registradas en el sistema para editar."
              )

        # -----------------------------------------------------
        # SUBTAB 2: REGISTRAR BENEFICIARIOS
        # -----------------------------------------------------
        with admin_subtab2:
          st.markdown("#### Registrar Nuevo Beneficiario")
          nuevo_beneficiario = st.text_input(
              "Nombre Completo del Beneficiario", key="nuevo_ben_input"
          )
          semestre_beneficiario = st.number_input(
              "Asignar Semestre",
              min_value=1,
              max_value=12,
              value=1,
              key="sem_ben_input",
          )

          if st.button("Guardar Beneficiario", key="btn_add_ben"):
            nombre_limpio = nuevo_beneficiario.strip()
            if nombre_limpio == "":
              st.warning("Escribe el nombre del beneficiario.")
            else:
              nombres_existentes = [
                  b["nombre"].lower()
                  for b in st.session_state.db["beneficiarios"]
              ]
              if nombre_limpio.lower() in nombres_existentes:
                st.warning(
                    f"⚠️ El beneficiario **{nombre_limpio}** ya existe en el"
                    " sistema. No se duplicó."
                )
              else:
                st.session_state.db["beneficiarios"].append({
                    "nombre": nombre_limpio,
                    "semestre": semestre_beneficiario,
                })
                guardar_datos(st.session_state.db)
                st.session_state.mensaje_exito = (
                    f"✅ Beneficiario **{nombre_limpio}** registrado"
                    f" exitosamente en Semestre {semestre_beneficiario}."
                )
                st.rerun()

        # -----------------------------------------------------
        # SUBTAB 3: ASIGNAR CALIFICACIONES
        # -----------------------------------------------------
        with admin_subtab3:
          st.markdown("#### Evaluar Actividades Registradas")
          lista_beneficiarios = [
              b["nombre"] for b in st.session_state.db["beneficiarios"]
          ]

          if lista_beneficiarios:
            beneficiario_eval = st.selectbox(
                "Seleccionar Beneficiario", lista_beneficiarios
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
                  f"Semana {t['semana']} - {t['tarea']} (Máx: {t['maximo']} pts)": t
                  for t in tareas_disponibles
              }
              tarea_seleccionada_label = st.selectbox(
                  "Seleccionar Actividad a Calificar",
                  list(opciones_tareas.keys()),
              )
              tarea_obj = opciones_tareas[tarea_seleccionada_label]

              calif_previa = next(
                  (
                      c
                      for c in st.session_state.db["calificaciones"]
                      if c.get("beneficiario", c.get("alumno"))
                      == beneficiario_eval
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

              if st.button("Guardar Calificación", key="btn_save_calif"):
                if calif_previa:
                  calif_previa["puntaje"] = puntaje_ingresado
                  st.session_state.mensaje_exito = (
                      f"✅ Calificación actualizada a {puntaje_ingresado} pts"
                      f" para **{beneficiario_eval}** en '{tarea_obj['tarea']}'."
                  )
                else:
                  st.session_state.db["calificaciones"].append({
                      "beneficiario": beneficiario_eval,
                      "tarea_id": tarea_obj["id"],
                      "puntaje": puntaje_ingresado,
                  })
                  st.session_state.mensaje_exito = (
                      f"✅ Calificación guardada: {puntaje_ingresado} pts para"
                      f" **{beneficiario_eval}** en '{tarea_obj['tarea']}'."
                  )

                guardar_datos(st.session_state.db)
                st.rerun()
            else:
              st.warning(
                  f"No hay actividades configuradas en el Plan del Semestre"
                  f" {sem_estudiante}. Ve a la pestaña 'Plan de Semestres' para"
                  " crearlas."
              )
          else:
            st.info("Primero registra a un beneficiario.")


if __name__ == "__main__":
  aplicacion_principal()