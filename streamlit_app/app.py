import streamlit as st
import requests
import json
import yaml
import time

# Título de la interfaz
st.title("Generador de Estrategias de Trading")

# Configuración de la API
API_URL = "http://localhost:8505"

# Inicializar variables de estado de la sesión
if 'strategy_data' not in st.session_state:
    st.session_state.strategy_data = None
if 'strategy_saved' not in st.session_state:
    st.session_state.strategy_saved = False
if 'last_prompt' not in st.session_state:
    st.session_state.last_prompt = ""

# Área de texto para escribir el prompt
prompt = st.text_area("Escribe tu prompt aquí", 
                      placeholder="Ejemplo: Crear una nueva estrategia Bollinger Bands")

# Función para generar estrategia
def generate_strategy(user_prompt):
    url = f"{API_URL}/generate_strategy/"
    payload = {"prompt": user_prompt}
    try:
        # Mostrar el prompt que se está enviando
        st.info(f"Enviando prompt: '{user_prompt}'")
        
        # Agregar un timestamp para evitar caché
        timestamp = int(time.time())
        response = requests.post(f"{url}?t={timestamp}", json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data["status"] == "success":
                st.session_state.strategy_data = {
                    "name": response_data["strategy_name"],
                    "description": response_data["strategy_description"],
                    "yaml_content": response_data["strategy_yaml"]
                }
                st.session_state.last_prompt = user_prompt
                # Resetear el estado de guardado cuando se genera una nueva estrategia
                st.session_state.strategy_saved = False
                return True
        st.error(f"Error en la respuesta: {response.text}")
        return False
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return False

# Función para guardar estrategia
def save_strategy():
    if st.session_state.strategy_data:
        save_url = f"{API_URL}/save_strategy/"
        save_response = requests.post(save_url, json={"strategy_data": st.session_state.strategy_data})
        if save_response.status_code == 200:
            st.session_state.strategy_saved = True
            return True
    return False

# Botón para enviar el prompt
if st.button("Generar estrategia"):
    if prompt:
        with st.spinner("Generando estrategia..."):
            if generate_strategy(prompt):
                st.success("Estrategia generada exitosamente")
                
                # Mostrar el nombre y la descripción
                st.subheader(st.session_state.strategy_data["name"])
                st.write(st.session_state.strategy_data["description"])
                
                # Mostrar el YAML generado
                st.code(st.session_state.strategy_data["yaml_content"], language="yaml")
            else:
                st.error("Error al generar la estrategia")
    else:
        st.warning("Por favor, escribe un prompt antes de enviar.")

# Botón para guardar la estrategia (solo se muestra si hay una estrategia generada y no ha sido guardada)
if st.session_state.strategy_data and not st.session_state.strategy_saved:
    if st.button("Guardar estrategia en la base de datos"):
        with st.spinner("Guardando estrategia..."):
            if save_strategy():
                st.success("Estrategia guardada en la base de datos")
            else:
                st.error("Error al guardar la estrategia")
elif st.session_state.strategy_saved:
    st.success("La estrategia ya ha sido guardada en la base de datos")

# Mostrar información de depuración
st.sidebar.title("Información de depuración")
if st.session_state.last_prompt:
    st.sidebar.subheader("Último prompt enviado:")
    st.sidebar.code(st.session_state.last_prompt)

if st.session_state.strategy_data:
    st.sidebar.subheader("Datos de estrategia recibidos:")
    st.sidebar.json(st.session_state.strategy_data)