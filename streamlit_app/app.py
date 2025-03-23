import streamlit as st
import requests
import json
import yaml
import time

# Configuración de las APIs
STRATEGY_API_URL = "http://localhost:8505"
INDICATOR_API_URL = "http://localhost:8506"

# Crear pestañas para estrategias e indicadores
tab1, tab2 = st.tabs(["Generador de Estrategias", "Generador de Indicadores"])

with tab1:
    # Título de la interfaz
    st.title("Generador de Estrategias de Trading")

    # Inicializar variables de estado de la sesión para estrategias
    if 'strategy_data' not in st.session_state:
        st.session_state.strategy_data = None
    if 'strategy_saved' not in st.session_state:
        st.session_state.strategy_saved = False
    if 'last_strategy_prompt' not in st.session_state:
        st.session_state.last_strategy_prompt = ""

    # Área de texto para escribir el prompt
    strategy_prompt = st.text_area("Escribe tu prompt aquí", 
                          placeholder="Ejemplo: Crear una nueva estrategia Bollinger Bands")

    # Función para generar estrategia
    def generate_strategy(user_prompt):
        url = f"{STRATEGY_API_URL}/generate_strategy/"
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
                    st.session_state.last_strategy_prompt = user_prompt
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
            save_url = f"{STRATEGY_API_URL}/save_strategy/"
            save_response = requests.post(save_url, json={"strategy_data": st.session_state.strategy_data})
            if save_response.status_code == 200:
                st.session_state.strategy_saved = True
                return True
        return False

    # Botón para enviar el prompt
    if st.button("Generar estrategia"):
        if strategy_prompt:
            with st.spinner("Generando estrategia..."):
                if generate_strategy(strategy_prompt):
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

with tab2:
    # Título de la interfaz
    st.title("Generador de Indicadores de Trading")

    # Inicializar variables de estado de la sesión para indicadores
    if 'indicator_data' not in st.session_state:
        st.session_state.indicator_data = None
    if 'indicator_saved' not in st.session_state:
        st.session_state.indicator_saved = False
    if 'last_indicator_prompt' not in st.session_state:
        st.session_state.last_indicator_prompt = ""

    # Área de texto para escribir el prompt
    indicator_prompt = st.text_area("Escribe tu prompt aquí", 
                          placeholder="Ejemplo: Crear un indicador RSI para detectar sobrecompra y sobreventa")

    # Función para generar indicador
    def generate_indicator(user_prompt):
        url = f"{INDICATOR_API_URL}/generate_indicator/"
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
                    # Verificar que los datos del indicador estén presentes
                    if "indicator_data" in response_data:
                        indicator_data = response_data["indicator_data"]
                        st.session_state.indicator_data = {
                            "name": indicator_data.get("name", "Sin nombre"),
                            "description": indicator_data.get("description", "Sin descripción"),
                            "config_yaml": indicator_data.get("config_yaml", ""),
                            "implementation_yaml": indicator_data.get("implementation_yaml", "")
                        }
                        st.session_state.last_indicator_prompt = user_prompt
                        # Resetear el estado de guardado cuando se genera un nuevo indicador
                        st.session_state.indicator_saved = False
                        return True
                    else:
                        st.error("La respuesta no contiene datos del indicador")
                        return False
            st.error(f"Error en la respuesta: {response.text}")
            return False
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return False

    # Función para guardar indicador
    def save_indicator():
        if st.session_state.indicator_data:
            save_url = f"{INDICATOR_API_URL}/save_indicator/"
            save_response = requests.post(save_url, json={"indicator_data": st.session_state.indicator_data})
            if save_response.status_code == 200:
                st.session_state.indicator_saved = True
                return True
        return False

    # Botón para enviar el prompt
    if st.button("Generar indicador"):
        if indicator_prompt:
            with st.spinner("Generando indicador..."):
                if generate_indicator(indicator_prompt):
                    st.success("Indicador generado exitosamente")
                    
                    # Mostrar el nombre y la descripción
                    st.subheader(st.session_state.indicator_data["name"])
                    st.write(st.session_state.indicator_data["description"])
                    
                    # Mostrar los YAMLs generados
                    st.subheader("Configuración YAML")
                    st.code(st.session_state.indicator_data["config_yaml"], language="yaml")
                    
                    st.subheader("Implementación YAML")
                    st.code(st.session_state.indicator_data["implementation_yaml"], language="yaml")
                else:
                    st.error("Error al generar el indicador")
        else:
            st.warning("Por favor, escribe un prompt antes de enviar.")

    # Botón para guardar el indicador (solo se muestra si hay un indicador generado y no ha sido guardado)
    if st.session_state.indicator_data and not st.session_state.indicator_saved:
        if st.button("Guardar indicador en la base de datos"):
            with st.spinner("Guardando indicador..."):
                if save_indicator():
                    st.success("Indicador guardado en la base de datos")
                else:
                    st.error("Error al guardar el indicador")
    elif st.session_state.indicator_saved:
        st.success("El indicador ya ha sido guardado en la base de datos")

# Mostrar información de depuración
st.sidebar.title("Información de depuración")

# Mostrar información de estrategias
if st.session_state.get('last_strategy_prompt'):
    st.sidebar.subheader("Último prompt de estrategia:")
    st.sidebar.code(st.session_state.last_strategy_prompt)

if st.session_state.get('strategy_data'):
    st.sidebar.subheader("Datos de estrategia recibidos:")
    st.sidebar.json(st.session_state.strategy_data)

# Mostrar información de indicadores
if st.session_state.get('last_indicator_prompt'):
    st.sidebar.subheader("Último prompt de indicador:")
    st.sidebar.code(st.session_state.last_indicator_prompt)

if st.session_state.get('indicator_data'):
    st.sidebar.subheader("Datos de indicador recibidos:")
    st.sidebar.json(st.session_state.indicator_data)