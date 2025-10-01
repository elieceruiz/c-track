# app.py
import streamlit as st
import pymongo
from datetime import datetime, timedelta, UTC
import pytz
import pandas as pd
import time
from my_key_listener import my_key_listener

# ---------------------------
# Configuración inicial
# ---------------------------
zona_col = pytz.timezone("America/Bogota")
st.set_page_config(page_title="📲 CallBoard", layout="centered")

MONGO_URI = st.secrets["mongo_uri"]
client = pymongo.MongoClient(MONGO_URI)
db = client["registro_llamadas_db"]
col_llamadas = db["llamadas"]

# ---------------------------
# Funciones auxiliares
# ---------------------------
def formatear_duracion(inicio, fin):
    duracion = fin - inicio
    dias = duracion.days
    horas, rem = divmod(duracion.seconds, 3600)
    minutos, segundos = divmod(rem, 60)
    partes = []
    if dias > 0:
        partes.append(f"{dias}d")
    partes.append(f"{horas}h")
    partes.append(f"{minutos}m")
    partes.append(f"{segundos}s")
    return " ".join(partes)

def calcular_aht(llamadas):
    if not llamadas:
        return "0h 0m 0s"
    total = timedelta()
    for l in llamadas:
        total += l["fin"] - l["inicio"]
    promedio = total / len(llamadas)
    horas, rem = divmod(promedio.seconds, 3600)
    minutos, segundos = divmod(rem, 60)
    return f"{horas}h {minutos}m {segundos}s"

def aht_en_segundos(llamadas):
    if not llamadas:
        return 0
    total = timedelta()
    for l in llamadas:
        total += l["fin"] - l["inicio"]
    segundos = int(total.total_seconds() / len(llamadas))
    return segundos

def iniciar_llamada():
    if not st.session_state.get("llamada_activa"):
        inicio_utc = datetime.now(UTC)
        llamada = {
            "inicio": inicio_utc,
            "fin": None,
            "estado_final": None,
            "emoji_percepcion": None
        }
        result = col_llamadas.insert_one(llamada)
        st.session_state["llamada_activa"] = result.inserted_id
        st.session_state["estado_llamada"] = "normal"
        st.session_state["percepcion_emoji"] = "feliz"
        st.session_state.running = True
        st.session_state.start_time = time.time()
        st.success("Llamada iniciada — ¡buena suerte! 🎧")
        st.rerun()

def terminar_llamada():
    if st.session_state.get("llamada_activa"):
        fin_utc = datetime.now(UTC)
        col_llamadas.update_one(
            {"_id": st.session_state["llamada_activa"]},
            {"$set": {
                "fin": fin_utc,
                "estado_final": st.session_state["estado_llamada"],
                "emoji_percepcion": st.session_state["percepcion_emoji"]
            }}
        )
        st.session_state["llamada_activa"] = None
        st.session_state.running = False
        st.session_state.elapsed_time = 0.0
        st.session_state.start_time = 0.0
        st.success("Llamada finalizada ✅")
        st.rerun()

def on_vista_change():
    st.session_state["vista"] = st.session_state["sel_vista"]

# ---------------------------
# Funciones del Teclonómetro
# ---------------------------
if "running" not in st.session_state:
    st.session_state.running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = 0.0
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0.0
if "last_key" not in st.session_state:
    st.session_state.last_key = None

def start_timer():
    if not st.session_state.running:
        st.session_state.start_time = time.time()
        st.session_state.running = True

def reset_timer():
    st.session_state.running = False
    st.session_state.elapsed_time = 0.0
    st.session_state.start_time = 0.0

# ---------------------------
# Valores iniciales
# ---------------------------
if "llamada_activa" not in st.session_state:
    st.session_state["llamada_activa"] = None
if "estado_llamada" not in st.session_state:
    st.session_state["estado_llamada"] = "normal"
if "percepcion_emoji" not in st.session_state:
    st.session_state["percepcion_emoji"] = "feliz"
if "vista" not in st.session_state:
    st.session_state["vista"] = "Llamada en curso"

# ---------------------------
# Selector de vista
# ---------------------------
vistas = ["Llamada en curso", "Registros"]
st.selectbox(
    "Seleccione vista:",
    vistas,
    key="sel_vista",
    index=vistas.index(st.session_state["vista"]),
    on_change=on_vista_change
)

# ---------------------------
# Vista 1: Llamada en curso
# ---------------------------
if st.session_state["vista"] == "Llamada en curso":
    st.title("📲 CallBoard")
    st.caption("Registro y control de llamadas — métricas claras y acciones rápidas")

    # Definir rango del día actual
    fecha_hoy = datetime.now(zona_col).date()
    hoy_ini = zona_col.localize(datetime(fecha_hoy.year, fecha_hoy.month, fecha_hoy.day, 0, 0, 0))
    hoy_fin = zona_col.localize(datetime(fecha_hoy.year, fecha_hoy.month, fecha_hoy.day, 23, 59, 59))

    llamadas_hoy = list(col_llamadas.find({
        "inicio": {"$gte": hoy_ini, "$lte": hoy_fin},
        "fin": {"$ne": None}
    }))

    num_llamadas = len(llamadas_hoy)
    aht = calcular_aht(llamadas_hoy)
    aht_seg = aht_en_segundos(llamadas_hoy)

    # Tarjetas métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("📞 Llamadas hoy", num_llamadas)
    col2.metric("⏱️ AHT", aht)
    col3.metric("🔢 AHT (s)", aht_seg)

    # Barra de progreso contra meta
    objetivo_seg = 300
    progreso = min(1.0, aht_seg / objetivo_seg) if objetivo_seg > 0 else 0
    st.progress(progreso)
    st.caption(f"Progreso AHT vs objetivo ({objetivo_seg}s)")

    st.divider()
    st.subheader("🎛️ Control rápido")
    st.caption("**Instrucciones:** Usa `Supr/Delete` para iniciar una llamada y `Mayús/Shift` para terminar. Maniobra con teclado y, como último recurso (y eso en ausencia de teclado): usa el botón con tap o clic")

    # Detectar tecla
    key = my_key_listener(key="listener")
    st.write(f"Tecla detectada: {key}")  # Debug

    # Lógica de teclas
    if key != st.session_state.last_key:
        st.session_state.last_key = key
        if key == "Delete":
            if not st.session_state.get("llamada_activa"):
                iniciar_llamada()
            else:
                start_timer()
            st.rerun()
        elif key == "Shift":
            if st.session_state.get("llamada_activa"):
                terminar_llamada()
            else:
                reset_timer()
            st.rerun()

    # Botón único con texto dinámico y emojis
    button_text = "✅ Iniciar `Supr/Delete`" if not st.session_state.get("llamada_activa") else "❌ Terminar `Mayús/Shift`"
    if st.button(button_text):
        if not st.session_state.get("llamada_activa"):
            iniciar_llamada()
        else:
            terminar_llamada()

    if st.session_state["llamada_activa"]:
        llamada = col_llamadas.find_one({"_id": st.session_state["llamada_activa"]})
        if llamada:
            inicio_local = llamada["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
            st.write(f"🔔 Llamada iniciada: **{inicio_local.strftime('%Y-%m-%d %H:%M:%S')}**")

        # Estado y percepción
        estado = st.selectbox(
            "Estado:",
            options=["caida", "normal", "corte"],
            format_func=lambda x: {"caida": "🔵 Caída", "normal": "🟡 Normal", "corte": "🔴 Finalizada"}[x],
            key="estado_llamada"
        )

        if estado == "caida":
            st.session_state["percepcion_emoji"] = None
            st.info("La percepción no aplica para llamadas caídas")
        else:
            st.selectbox(
                "Percepción:",
                options=["feliz", "meh", "enojado"],
                format_func=lambda x: {"feliz": "😃 Feliz", "meh": "😐 Meh", "enojado": "😡 Enojado"}[x],
                key="percepcion_emoji"
            )

    # Calcular tiempo transcurrido
    if st.session_state.running:
        current_time = st.session_state.elapsed_time + (time.time() - st.session_state.start_time)
    else:
        current_time = st.session_state.elapsed_time

    # Formatear tiempo
    hours = int(current_time // 3600)
    minutes = int((current_time % 3600) // 60)
    seconds = int(current_time % 60)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Mostrar cronómetro
    st.markdown(f"### {formatted_time}")

    # Mostrar estado
    if st.session_state.running:
        st.success("Estado: Corriendo")
    else:
        st.error("Estado: Detenido")

    # Actualización automática
    if st.session_state.running:
        time.sleep(0.1)
        st.rerun()

    st.divider()
    st.subheader("📈 Actividad por hora")

    if llamadas_hoy:
        df_horas = pd.DataFrame([
            {"hora": l["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col).hour}
            for l in llamadas_hoy
        ])
        conteo = df_horas["hora"].value_counts().sort_index()
        s = pd.Series(index=range(0, 24), dtype=int)
        for h in range(24):
            s.loc[h] = int(conteo.get(h, 0))
        s.index = [f"{h:02d}:00" for h in s.index]
        st.bar_chart(s)
    else:
        st.info("Aún no hay llamadas finalizadas hoy.")

    st.divider()
    ultima = col_llamadas.find_one({"fin": {"$ne": None}}, sort=[("fin", -1)])
    if ultima:
        perc = ultima.get("emoji_percepcion")
        if perc == "feliz":
            st.success("¡Bien! El cliente quedó contento 😃")
        elif perc == "meh":
            st.info("Quedó regular — revisa el caso 😐")
        elif perc == "enojado":
            st.error("Atención: hubo una experiencia negativa 😡")

# ---------------------------
# Vista 2: Registros históricos
# ---------------------------
else:
    st.subheader("📒 Registros históricos de llamadas")

    llamadas_finalizadas = list(col_llamadas.find({"fin": {"$ne": None}}))
    num_total = len(llamadas_finalizadas)
    aht_total = calcular_aht(llamadas_finalizadas)
    aht_total_seg = aht_en_segundos(llamadas_finalizadas)

    col1, col2, col3 = st.columns(3)
    col1.metric("📞 Total llamadas", num_total)
    col2.metric("⏱️ AHT total", aht_total)
    col3.metric("🔢 AHT (s) total", aht_total_seg)

    registros = []
    for l in llamadas_finalizadas:
        inicio_local = l["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
        fin_local = l["fin"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
        duracion = formatear_duracion(l["inicio"], l["fin"])
        registros.append({
            "Inicio": inicio_local.strftime("%Y-%m-%d %H:%M:%S"),
            "Fin": fin_local.strftime("%Y-%m-%d %H:%M:%S"),
            "Duración": duracion,
            "Estado": l.get("estado_final", ""),
            "Percepción": l.get("emoji_percepcion", "")
        })

    if registros:
        df = pd.DataFrame(registros)
        st.dataframe(df, width="stretch")
    else:
        st.info("No hay registros finalizados.")
