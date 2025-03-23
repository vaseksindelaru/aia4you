import streamlit as st
import requests
import json
import yaml

# Título de la interfaz
st.title("Generador de Estrategias de Trading")

# Configuración de la API
API_URL = "http://localhost:8505"

# Área de texto para escribir el prompt
prompt = st.text_area("Escribe tu prompt aquí", 
                      placeholder="Ejemplo: Crear una nueva estrategia Momentum Trading")

# Inicializar variables de estado de la sesión
if 'strategy_data' not in st.session_state:
    st.session_state.strategy_data = None
if 'strategy_saved' not in st.session_state:
    st.session_state.strategy_saved = False

# Función para generar estrategia
def generate_strategy():
    url = f"{API_URL}/generate_strategy/"
    payload = {"prompt": prompt}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if response_data["status"] == "success":
                st.session_state.strategy_data = {
                    "name": response_data["strategy_name"],
                    "description": response_data["strategy_description"],
                    "yaml_content": response_data["strategy_yaml"]
                }
                return True
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
if st.button("Enviar"):
    if prompt:
        with st.spinner("Generando estrategia..."):
            if generate_strategy():
                st.success("Estrategia generada exitosamente")
                
                # Mostrar el nombre y la descripción
                st.subheader(st.session_state.strategy_data["name"])
                st.write(st.session_state.strategy_data["description"])
                
                # Mostrar el YAML generado
                st.code(st.session_state.strategy_data["yaml_content"], language="yaml")
                
                # Resetear el estado de guardado
                st.session_state.strategy_saved = False
            else:
                st.error("Error al generar la estrategia")
    else:
        st.warning("Por favor, escribe un prompt antes de enviar.")

# Botón para guardar la estrategia
if st.session_state.strategy_data and not st.session_state.strategy_saved:
    if st.button("Guardar estrategia en la base de datos"):
        with st.spinner("Guardando estrategia..."):
            if save_strategy():
                st.success("Estrategia guardada en la base de datos")
            else:
                st.error("Error al guardar la estrategia")

# Mostrar mensaje si ya se guardó la estrategia
if st.session_state.strategy_saved:
    st.success("La estrategia ya ha sido guardada en la base de datos")