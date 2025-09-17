import streamlit as st
import pymongo
from datetime import datetime, timedelta
import pytz
import pandas as pd

# Forzar columnas horizontales con scroll en móvil
st.markdown("""
<style>
[data-testid="stVerticalBlock"] > div {
    flex-wrap: nowrap !important;
    overflow-x: auto;
}
</style>
""", unsafe_allow_html=True)

# Zona horaria Colombia
zona_col = pytz.timezone("America/Bogota")

# Config Streamlit
st.set_page_config(page_title="App Registro de Llamadas", layout="centered")

# Conexión a MongoDB
MONGO_URI = st.secrets["mongo_uri"]
client = pymongo.MongoClient(MONGO_URI)
db = client["registro_llamadas_db"]
col_llamadas = db["llamadas"]

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

if "llamada_activa" not in st.session_state:
    st.session_state["llamada_activa"] = None
if "estado_llamada" not in st.session_state:
    st.session_state["estado_llamada"] = "normal"
if "percepcion_emoji" not in st.session_state:
    st.session_state["percepcion_emoji"] = None
if "vista" not in st.session_state:
    st.session_state["vista"] = "Llamada en curso"

def iniciar_llamada():
    if not st.session_state["llamada_activa"]:
        inicio_utc = datetime.utcnow()
        llamada = {
            "inicio": inicio_utc,
            "fin": None,
            "estado_final": None,
            "emoji_percepcion": None
        }
        result = col_llamadas.insert_one(llamada)
        st.session_state["llamada_activa"] = result.inserted_id
        st.session_state["estado_llamada"] = "normal"
        st.session_state["percepcion_emoji"] = None

def terminar_llamada():
    if st.session_state["llamada_activa"]:
        fin_utc = datetime.utcnow()
        col_llamadas.update_one(
            {"_id": st.session_state["llamada_activa"]},
            {"$set": {
                "fin": fin_utc,
                "estado_final": st.session_state["estado_llamada"],
                "emoji_percepcion": st.session_state["percepcion_emoji"]
            }}
        )
        st.session_state["llamada_activa"] = None
        st.session_state["estado_llamada"] = "normal"
        st.session_state["percepcion_emoji"] = None

def on_vista_change():
    st.session_state["vista"] = st.session_state["sel_vista"]

vistas = ["Llamada en curso", "Registros"]
st.selectbox(
    "Seleccione vista:",
    vistas,
    key="sel_vista",
    index=vistas.index(st.session_state["vista"]),
    on_change=on_vista_change
)

st.title("Registro y Control de Llamadas")

if st.session_state["vista"] == "Llamada en curso":
    hoy_ini = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    llamadas_hoy = list(col_llamadas.find({
        "inicio": {"$gte": hoy_ini, "$lte": hoy_fin},
        "fin": {"$ne": None}
    }))
    num_llamadas = len(llamadas_hoy)
    aht = calcular_aht(llamadas_hoy)

    st.markdown("🔵 Caída | 🟡 Normal | 🔴 Tuve que finalizarla")

    st.markdown(f"**Número de llamadas hoy:** {num_llamadas}")
    st.markdown(f"**Average Handle Time (AHT):** {aht}")

    st.subheader("Llamada en curso")

    if st.session_state["llamada_activa"]:
        llamada = col_llamadas.find_one({"_id": st.session_state["llamada_activa"]})
        inicio_local = llamada["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
        st.write(f"Llamada iniciada el {inicio_local.strftime('%Y-%m-%d %H:%M:%S')}")

        col1, col2, col3 = st.columns([1,1,1], gap="small")
        with col1:
            if st.button("🔵", key="btn_caida"):
                st.session_state["estado_llamada"] = "caida"
                st.session_state["percepcion_emoji"] = None
        with col2:
            if st.button("🟡", key="btn_normal"):
                st.session_state["estado_llamada"] = "normal"
        with col3:
            if st.button("🔴", key="btn_corte"):
                st.session_state["estado_llamada"] = "corte"
                st.session_state["percepcion_emoji"] = None

        estado = st.session_state["estado_llamada"]
        if estado == "normal":
            st.warning(f"Estado seleccionado: {estado}")
        elif estado == "caida":
            st.info(f"Estado seleccionado: {estado}")
        elif estado == "corte":
            st.error(f"Estado seleccionado: {estado}")

        if estado in ["normal", "corte"]:
            st.write("Seleccione percepción:")
            colf1, colf2, colf3 = st.columns([1,1,1], gap="small")
            with colf1:
                if st.button("😃", key="emoji_feliz"):
                    st.session_state["percepcion_emoji"] = "feliz"
            with colf2:
                if st.button("😐", key="emoji_meh"):
                    st.session_state["percepcion_emoji"] = "meh"
            with colf3:
                if st.button("😡", key="emoji_enojado"):
                    st.session_state["percepcion_emoji"] = "enojado"
            percep = st.session_state["percepcion_emoji"]
            if percep:
                st.markdown(f"Emoji seleccionado: {percep}")

        if estado:
            if st.button("Terminar llamada", key="btn_terminar"):
                terminar_llamada()
                st.rerun()
    else:
        if st.button("Iniciar llamada"):
            iniciar_llamada()
            st.rerun()

else:
    st.subheader("Registros históricos de llamadas")

    hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    llamadas_hoy = list(col_llamadas.find({
        "inicio": {"$gte": hoy_inicio, "$lte": hoy_fin},
        "fin": {"$ne": None}
    }))

    num_llamadas = len(llamadas_hoy)
    aht = calcular_aht(llamadas_hoy)

    st.markdown(f"**Número de llamadas hoy:** {num_llamadas}")
    st.markdown(f"**Average Handle Time (AHT):** {aht}")

    registros = []
    for l in llamadas_hoy:
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
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay registros finalizados para hoy.")