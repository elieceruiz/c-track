import streamlit as st
import pymongo
from datetime import datetime, time, timedelta
import pytz
import pandas as pd

# Configurar zona horaria de Colombia para convertir fechas UTC a hora local y para filtrar por día actual local
zona_col = pytz.timezone("America/Bogota")

# Configuración inicial de Streamlit: título, layout centrado
st.set_page_config(page_title="App Registro de Llamadas", layout="centered")

# Conexión a la base de datos MongoDB usando URI almacenada en los secretos de Streamlit
MONGO_URI = st.secrets["mongo_uri"]
client = pymongo.MongoClient(MONGO_URI)
db = client["registro_llamadas_db"]
col_llamadas = db["llamadas"]

# Función para formatear duración entre fechas en formato legible '0d 0h 1m 30s'
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

# Función para calcular Average Handle Time (promedio duración) de llamadas finalizadas, formato legible
def calcular_aht(llamadas):
    if not llamadas:
        return "0h 0m 0s"  # Retorna cero cuando no hay llamadas
    total = timedelta()
    for l in llamadas:
        total += l["fin"] - l["inicio"]
    promedio = total / len(llamadas)
    horas, rem = divmod(promedio.seconds, 3600)
    minutos, segundos = divmod(rem, 60)
    return f"{horas}h {minutos}m {segundos}s"

# Función para calcular el Average Handle Time (AHT) pero en segundos
def aht_en_segundos(llamadas):
    if not llamadas:
        return 0
    total = timedelta()
    for l in llamadas:
        total += l["fin"] - l["inicio"]
    segundos = int(total.total_seconds() / len(llamadas))
    return segundos

# Valores por defecto en sesion state para controlar estado de vista y llamada
if "llamada_activa" not in st.session_state:
    st.session_state["llamada_activa"] = None
if "estado_llamada" not in st.session_state:
    st.session_state["estado_llamada"] = "normal"
if "percepcion_emoji" not in st.session_state:
    st.session_state["percepcion_emoji"] = "feliz"
if "vista" not in st.session_state:
    st.session_state["vista"] = "Llamada en curso"

# Función para iniciar una llamada: inserta registro con tiempo inicio UTC, estado y percepción vacíos
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

# Función para terminar llamada: actualiza registro con tiempo fin UTC, estado final y percepción seleccionada
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

# Cambio de vista entre "Llamada en curso" y "Registros"
def on_vista_change():
    st.session_state["vista"] = st.session_state["sel_vista"]

# Selector de vista principal
vistas = ["Llamada en curso", "Registros"]
st.selectbox(
    "Seleccione vista:",
    vistas,
    key="sel_vista",
    index=vistas.index(st.session_state["vista"]),
    on_change=on_vista_change
)

# Título de la app
st.title("Registro y Control de Llamadas")

# Vista principal según selección de usuario
if st.session_state["vista"] == "Llamada en curso":
    # Definir rango día actual en Colombia para filtrar documentos del día
    fecha_hoy = datetime.now(zona_col).date()
    hoy_ini = zona_col.localize(datetime.combine(fecha_hoy, time.min))
    hoy_fin = zona_col.localize(datetime.combine(fecha_hoy, time.max))

    # Filtra llamadas finalizadas que comenzaron dentro del día actual local
    llamadas_hoy = list(col_llamadas.find({
        "inicio": {"$gte": hoy_ini, "$lte": hoy_fin},
        "fin": {"$ne": None}
    }))

    # Calcular número de llamadas y promedio AHT del día
    num_llamadas = len(llamadas_hoy)
    aht = calcular_aht(llamadas_hoy)
    aht_seg = aht_en_segundos(llamadas_hoy)

    # Mostrar métricas resumen en UI
    st.markdown(f"**Número de llamadas hoy:** {num_llamadas}")
    st.markdown(f"**Average Handle Time (AHT):** {aht}")
    st.markdown(f"**AHT en segundos:** {aht_seg}")

    st.subheader("Llamada en curso")

    if st.session_state["llamada_activa"]:
        llamada = col_llamadas.find_one({"_id": st.session_state["llamada_activa"]})
        if llamada:
            # Mostrar hora de inicio local convertida desde UTC
            inicio_local = llamada["inicio"].replace(tzinfo=pytz.UTC).astimezone(zona_col)
            st.write(f"Llamada iniciada el {inicio_local.strftime('%Y-%m-%d %H:%M:%S')}")

        # Opciones posibles para estado de llamada
        estado_opciones = {
            "caida": "🔵 Caída",
            "normal": "🟡 Normal",
            "corte": "🔴 Finalizada"
        }
        # Dropdown que actualiza estado en session_state
        estado = st.selectbox(
            "Estado de la llamada:",
            options=list(estado_opciones.keys()),
            format_func=lambda x: estado_opciones[x],
            key="estado_llamada"
        )

        # Si el estado es "caida", no aplica percepción y se informa
        if estado == "caida":
            st.session_state["percepcion_emoji"] = None
            st.info("La percepción no aplica para estado 'Caída'")
        else:
            # Opciones para percepción de la llamada
            percepcion_opciones = {
                "feliz": "😃 Feliz",
                "meh": "😐 Meh",
                "enojado": "😡 Enojado"
            }
            # Dropdown que actualiza percepción en session_state
            percepcion = st.selectbox(
                "Percepción:",
                options=list(percepcion_opciones.keys()),
                format_func=lambda x: percepcion_opciones[x],
                key="percepcion_emoji"
            )

        # Mostrar texto destacado según estado elegido
        if estado == "normal":
            st.success(f"Estado seleccionado: {estado_opciones[estado]}")
        elif estado == "caida":
            st.info(f"Estado seleccionado: {estado_opciones[estado]}")
        elif estado == "corte":
            st.error(f"Estado seleccionado: {estado_opciones[estado]}")

        # Mostrar texto destacado según percepción si aplica
        if estado != "caida" and st.session_state.get("percepcion_emoji"):
            perc = st.session_state["percepcion_emoji"]
            if perc == "feliz":
                st.success(f"Emoji seleccionado: {percepcion_opciones[perc]}")
            elif perc == "meh":
                st.info(f"Emoji seleccionado: {percepcion_opciones[perc]}")
            elif perc == "enojado":
                st.error(f"Emoji seleccionado: {percepcion_opciones[perc]}")

        # Botón para terminar llamada, guarda datos y reinicia estado llamada activa
        if st.button("Terminar llamada"):
            terminar_llamada()
            st.rerun()
    else:
        # Botón para iniciar llamada crea registro y activa estado
        if st.button("Iniciar llamada"):
            iniciar_llamada()
            st.rerun()

else:  # Vista Registros históricos de llamadas

    st.subheader("Registros históricos de llamadas")

    # Buscar todas las llamadas finalizadas en base de datos sin filtrar por fecha
    llamadas_finalizadas = list(col_llamadas.find({"fin": {"$ne": None}}))

    # Número total de llamadas finalizadas
    num_total = len(llamadas_finalizadas)

    # Calcular promedio AHT con todo el historial
    aht_total = calcular_aht(llamadas_finalizadas)
    aht_total_seg = aht_en_segundos(llamadas_finalizadas)

    # Mostrar resumen total histórico
    st.markdown(f"**Número total de llamadas:** {num_total}")
    st.markdown(f"**Average Handle Time (AHT) total:** {aht_total}")
    st.markdown(f"**AHT total en segundos:** {aht_total_seg}")

    registros = []
    # Preparar lista para mostrar tabla con datos locales y legibles
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
        # Mostrar tabla con toda la información de registros
        df = pd.DataFrame(registros)
        st.dataframe(df, use_container_width=True)
    else:
        # Aviso en caso que no haya datos disponibles
        st.info("No hay registros finalizados.")
