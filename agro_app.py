import streamlit as st
import pandas as pd
import requests
from streamlit_geolocation import streamlit_geolocation

st.title("🚜 App Agrícola Inteligente con GPS y Clima")

# --- 1. Obtener ubicación GPS ---
location = streamlit_geolocation()

# Verificamos que la ubicación esté disponible
if isinstance(location, dict) and location.get("latitude") is not None:
    lat = location["latitude"]
    lon = location["longitude"]
    
    st.success(f"Ubicación obtenida: {lat:.5f}, {lon:.5f}")
    
    # --- 2. Consultar datos reales del clima con Open-Meteo ---
    url_api = "https://api.open-meteo.com/v1/forecast"
    parametros = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
        "timezone": "auto"
    }
    
    response = requests.get(url_api, params=parametros)
    
    if response.status_code == 200:
        datos_clima = response.json().get("current", {})
        # Extraemos los valores reales
        temperatura = datos_clima.get("temperature_2m", 0)
        humedad_real = datos_clima.get("relative_humidity_2m", 0)
        viento = datos_clima.get("wind_speed_10m", 0)
        
        # Guardamos los datos en el estado (usando claves nuevas para evitar conflictos)
        st.session_state['humedad_real_gps'] = humedad_real
        st.session_state['temp_real_gps'] = temperatura
        
        # --- 3. VISUALIZAR DATOS ---
        st.subheader("Datos Actuales de tu Zona")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="🌡️ Temperatura", value=f"{temperatura}°C")
        with col2:
            st.metric(label="💧 Humedad", value=f"{humedad_real}%")
        with col3:
            st.metric(label="💨 Viento", value=f"{viento} km/h")
        
        st.divider()
        st.subheader("Mapa de Ubicación")
        df_ubicacion = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.map(df_ubicacion, zoom=14)
    else:
        st.error("Hubo un problema al conectar con el servicio de clima.")
else:
    st.info("🛰️ Por favor, pulsa el botón para activar el GPS y ver los datos reales de tu ubicación.")
