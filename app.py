import streamlit as st
import pymongo
from datetime import datetime, timedelta
import pytz
import pandas as pd

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
    st.session_state["percepcion_emoji"] = "feliz"
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
        st.session_state["percepcion_emoji"] = "feliz"

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
        st.session_state["percepcion_emoji"] = "feliz"

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

    st.markdown(f"**Número de llamadas hoy:** {num_llamadas}")
    st.markdown(f"**Average Handle Time (AHT):** {aht}")

    st.subheader("Llamada en curso")

    if st.session_state["llamada_activa"]:
        llamada = col_llamadas.find_one({"_id": st.session_state["llamada_activa"]})
        inicio_local = llamada["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
        st.write(f"Llamada iniciada el {inicio_local.strftime('%Y-%m-%d %H:%M:%S')}")

        estado_opciones = {
            "caida": "🔵 Caída",
            "normal": "🟡 Normal",
            "corte": "🔴 Finalizada"
        }
        estado = st.selectbox(
            "Estado de la llamada:",
            options=list(estado_opciones.keys()),
            index=list(estado_opciones.keys()).index(st.session_state["estado_llamada"]),
            format_func=lambda x: estado_opciones[x],
            key="estado_llamada"
        )

        if estado != "caida":
            percepcion_opciones = {
                "feliz": "😃 Feliz",
                "meh": "😐 Meh",
                "enojado": "😡 Enojado"
            }
            percepcion = st.selectbox(
                "Percepción:",
                options=list(percepcion_opciones.keys()),
                index=list(percepcion_opciones.keys()).index(st.session_state.get("percepcion_emoji", "feliz")),
                format_func=lambda x: percepcion_opciones[x],
                key="percepcion_emoji"
            )
            st.markdown(f"Emoji seleccionado: {percepcion}")
        else:
            st.info("La percepción no aplica para llamadas de estado 'Caída'")
            st.session_state["percepcion_emoji"] = None

        if st.button("Terminar llamada"):
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