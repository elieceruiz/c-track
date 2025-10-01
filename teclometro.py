import streamlit as st
import time
import streamlit.components.v1 as components

# Ajusta el path según dónde pongas frontend/
my_key_listener = components.declare_component("my_key_listener", path="./frontend/my_key_listener")

def run_teclometro():
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
        tiempo_llamada = st.session_state.elapsed_time + (
            time.time() - st.session_state.start_time if st.session_state.running else 0
        )
        st.session_state.running = False
        st.session_state.elapsed_time = 0.0
        st.session_state.start_time = 0.0
        return tiempo_llamada

    key = my_key_listener(key="listener")
    tiempo_llamada = 0.0
    if key != st.session_state.last_key:
        st.session_state.last_key = key
        if key == "Delete":
            start_timer()
            st.rerun()
        elif key == "Shift":
            tiempo_llamada = reset_timer()
            st.rerun()

    if st.session_state.running:
        current_time = st.session_state.elapsed_time + (time.time() - st.session_state.start_time)
    else:
        current_time = st.session_state.elapsed_time

    hours = int(current_time // 3600)
    minutes = int((current_time % 3600) // 60)
    seconds = int(current_time % 60)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    st.markdown("# Teclonómetro")
    st.info("""
    **Instrucciones**  
    - Presiona **Delete** para iniciar el cronómetro.  
    - Presiona **Shift** para reiniciar y detener.  
    - Usa los botones para control manual.
    """)
    st.markdown(f"### {formatted_time}")
    if st.session_state.running:
        st.success("Estado: Corriendo")
    else:
        st.error("Estado: Detenido")
    st.write("Última tecla:", key if key else "Ninguna")
    emoji = "🏃‍♂️" if st.session_state.running else "🛑"
    st.markdown(f"## {emoji}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Iniciar (Delete)", use_container_width=True):
            start_timer()
            st.rerun()
    with col2:
        if st.button("Reiniciar (Shift)", use_container_width=True):
            tiempo_llamada = reset_timer()
            st.rerun()

    if st.session_state.running:
        time.sleep(0.1)
        st.rerun()

    return formatted_time, tiempo_llamada

def get_formatted_time():
    if st.session_state.running:
        current_time = st.session_state.elapsed_time + (time.time() - st.session_state.start_time)
    else:
        current_time = st.session_state.elapsed_time
    hours = int(current_time // 3600)
    minutes = int((current_time % 3600) // 60)
    seconds = int(current_time % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_current_time():
    if st.session_state.running:
        return st.session_state.elapsed_time + (time.time() - st.session_state.start_time)
    return st.session_state.elapsed_time
