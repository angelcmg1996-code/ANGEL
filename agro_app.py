import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
import joblib
import os
from datetime import datetime, timedelta
import random

# ========== CÓDIGO PWA PARA ANDROID ==========
# Esto permite que la app sea instalable en Android
PWA_HTML = """
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}
</script>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<link rel="manifest" href="/manifest.json">
"""
st.markdown(PWA_HTML, unsafe_allow_html=True)
# =============================================
st.set_page_config(page_title="🌾 AgroInteligente", layout="wide")
st.title("🌾 AgroInteligente - Asistente de Riego con IA")
st.markdown("Ing. Ángel M.G.")

def generar_datos_campo(n=3000):
    np.random.seed(42)
    temperatura = np.random.uniform(12, 42, n)
    humedad_suelo = np.random.uniform(15, 85, n)
    lluvia = np.random.exponential(4, n)
    humedad_suelo = humedad_suelo - 0.3 * (temperatura - 20) + np.random.normal(0, 3, n)
    humedad_suelo = np.clip(humedad_suelo, 10, 95)
    regar = ((humedad_suelo < 50) & (lluvia < 5) & (temperatura > 18)).astype(int)
    volumen = np.where(regar == 1, 15 + (50 - humedad_suelo) * 0.6 + np.random.normal(0, 4), 0)
    volumen = np.clip(volumen, 0, 55)
    df = pd.DataFrame({
        'fecha': [datetime.now() - timedelta(hours=i) for i in range(n)],
        'humedad': humedad_suelo,
        'temperatura': temperatura,
        'lluvia': lluvia,
        'regar': regar,
        'volumen': volumen
    })
    return df

def entrenar_modelos(df):
    X = df[['humedad', 'temperatura', 'lluvia']]
    y_clf = df['regar']
    y_reg = df['volumen']
    clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    clf.fit(X, y_clf)
    X_reg = X[y_clf == 1]
    y_reg = y_reg[y_clf == 1]
    reg = LinearRegression()
    reg.fit(X_reg, y_reg)
    return clf, reg

@st.cache_resource
def obtener_modelos():
    if os.path.exists('clf_riego.pkl') and os.path.exists('reg_volumen.pkl'):
        clf = joblib.load('clf_riego.pkl')
        reg = joblib.load('reg_volumen.pkl')
        df = generar_datos_campo(3000)
    else:
        df = generar_datos_campo(3000)
        clf, reg = entrenar_modelos(df)
        joblib.dump(clf, 'clf_riego.pkl')
        joblib.dump(reg, 'reg_volumen.pkl')
    return clf, reg, df

clf, reg, df_historico = obtener_modelos()

def recomendar(humedad, temp, lluvia):
    X_input = np.array([[humedad, temp, lluvia]])
    decision = int(clf.predict(X_input)[0])
    if decision == 1:
        volumen = reg.predict(X_input)[0]
        volumen = max(5, min(55, volumen))
        return {'regar': True, 'volumen': round(volumen, 1), 'mensaje': f"💧 Recomendación: Riega con {round(volumen, 1)} litros por metro cuadrado.", 'color': '#28a745'}
    else:
        return {'regar': False, 'volumen': 0, 'mensaje': "☀️ Recomendación: No es necesario regar.", 'color': '#dc3545'}

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🧪 Datos del Sensor")
    humedad = st.slider("💧 Humedad del Suelo (%)", 10, 90, 45, key="hum")
    temperatura = st.slider("🌡️ Temperatura (°C)", 10, 45, 30, key="temp")
    lluvia = st.slider("☔ Lluvia últimas 24h (mm)", 0.0, 20.0, 2.0, key="lluv")
    if st.button("🎲 Simular Lectura Aleatoria"):
        temp_rand = random.uniform(15, 40)
        hum_rand = max(15, min(85, 70 - 0.6*(temp_rand-20) + random.gauss(0, 5)))
        lluv_rand = max(0, np.random.exponential(4))
        st.session_state.hum = round(hum_rand)
        st.session_state.temp = round(temp_rand)
        st.session_state.lluv = round(lluv_rand, 1)
        st.rerun()
    resultado = recomendar(st.session_state.hum, st.session_state.temp, st.session_state.lluv)
    st.markdown("---")
    st.subheader("📋 Decisión de la IA")
    st.markdown(f"<div style='background-color:{resultado['color']}; padding:15px; border-radius:10px; color:white; font-size:18px;'>{resultado['mensaje']}</div>", unsafe_allow_html=True)
    if resultado['regar']: st.metric(label="🚿 Volumen", value=f"{resultado['volumen']} L/m²")

with col2:
    st.subheader("📊 Tendencias Históricas")
    df_plot = df_historico.tail(100).copy()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_plot['fecha'], df_plot['humedad'], label='Humedad (%)', color='blue', alpha=0.7)
    ax2 = ax.twinx()
    riego_points = df_plot[df_plot['regar'] == 1]
    ax2.scatter(riego_points['fecha'], riego_points['volumen'], color='green', s=30, label='Riego (L)', alpha=0.8)
    ax.set_xlabel('Tiempo'); ax.set_ylabel('Humedad (%)'); ax2.set_ylabel('Volumen (L)')
    ax.legend(loc='upper left'); ax2.legend(loc='upper right')
    plt.xticks(rotation=45); plt.tight_layout()
    st.pyplot(fig)
    st.subheader("📋 Últimas Decisiones")
    historial = []
    for i in range(5):
        h = np.random.uniform(30, 70); t = np.random.uniform(18, 38); l = np.random.exponential(3)
        res = recomendar(h, t, l)
        historial.append({'Hora': (datetime.now() - timedelta(minutes=i*15)).strftime('%H:%M'), 'Humedad': f"{h:.1f}%", 'Decisión': '💧 Regar' if res['regar'] else '☀️ No regar', 'Volumen': f"{res['volumen']} L" if res['regar'] else '--'})
    st.dataframe(pd.DataFrame(historial), use_container_width=True)

st.markdown("---")
st.caption("🌱 AgroInteligente v2.0 - IA para Agricultura de Precisión.")
