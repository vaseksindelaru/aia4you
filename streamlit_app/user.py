import streamlit as st
import requests

# Título de la interfaz
st.title("Generador de Estrategias de Trading")

# Área de texto para escribir el prompt
prompt = st.text_area("Escribe tu prompt aquí", 
                      placeholder="Ejemplo: Crear una nueva estrategia Momentum Trading")

# Botón para enviar el prompt
if st.button("Enviar"):
    if prompt:
        # Enviar el prompt a helpConnect.py via POST request
        url = "http://localhost:8000/help_connect"  # Ajusta la URL según tu API
        payload = {"prompt": prompt}
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                st.success("Estrategia generada exitosamente:")
                st.write(response.text)
            else:
                st.error(f"Error al generar la estrategia: {response.status_code}")
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
    else:
        st.warning("Por favor, escribe un prompt antes de enviar.")