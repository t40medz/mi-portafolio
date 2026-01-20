import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ruta a los $1,200", page_icon="📱", layout="wide")

# --- 1. CONEXIÓN A DATOS (GOOGLE SHEETS) ---
# Pega aquí el enlace CSV de tu Google Sheet (Publicar en la web -> CSV)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRSJ7HUzdMFxd__pO3CqfckWPtpH-Z_9we9fOq5xaBGaprEiWHBGnQ-hcH4t-I-jZp35LGhElnXe65N/pub?output=csv" 

# Función para cargar datos (con caché para que sea rápido)
@st.cache_data(ttl=60) # Actualiza cada 60 segundos
def load_data():
    try:
        df = pd.read_csv(sheet_url)
        return df
    except:
        return pd.DataFrame()

df_portfolio = load_data()

# --- BLOQUE DE DIAGNÓSTICO (NUEVO) ---
if df_portfolio.empty:
    st.error("⚠️ El archivo está vacío. Revisa el enlace.")
else:
    # Esto te mostrará en pantalla qué columnas leyó realmente
    st.write("👀 Columnas detectadas:", df_portfolio.columns.tolist()) 
    
    # Verificamos si existe la columna 'Ticker' antes de seguir
    if 'Ticker' not in df_portfolio.columns:
        st.error(f"❌ Error: No encuentro la columna 'Ticker'. Asegúrate de que en Google Sheets la columna B se llame exactamente 'Ticker'.")
        st.stop() # Detiene la app aquí para que no explote

# --- 2. OBTENER PRECIOS EN TIEMPO REAL ---
def get_current_prices(tickers):
    if not tickers:
        return {}
    try:
        # Descarga datos de Yahoo Finance
        data = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
        return data
    except Exception as e:
        st.error(f"Error conectando al mercado: {e}")
        return {}

# --- LÓGICA PRINCIPAL ---
st.title("📱 Mi Misión: Celular Nuevo ($1,500)")

if df_portfolio.empty:
    st.warning("⚠️ No pude leer tu Google Sheet. Revisa que el enlace termine en '&output=csv'.")
else:
    # Preparar lista de tickers
    tickers_list = df_portfolio['Ticker'].tolist()
    current_prices = get_current_prices(tickers_list)

    # Calcular valores actuales
    total_value = 0
    df_portfolio['Precio_Actual'] = df_portfolio['Ticker'].apply(lambda x: current_prices[x] if x in current_prices else 0)
    df_portfolio['Valor_Total'] = df_portfolio['Cantidad'] * df_portfolio['Precio_Actual']
    df_portfolio['Ganancia'] = df_portfolio['Valor_Total'] - (df_portfolio['Cantidad'] * df_portfolio['Precio_Compra'])
    
    total_actual = df_portfolio['Valor_Total'].sum()
    meta = 1500  # Tu meta del celular
    progreso = (total_actual / meta)
    falta = meta - total_actual

    # --- 3. DASHBOARD VISUAL ---
    
    # KPIs Principales
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Capital Actual", f"${total_actual:.2f}", f"{progreso*100:.1f}% de la Meta")
    col2.metric("🎯 Falta para el Celular", f"${falta:.2f}", delta_color="inverse")
    
    # Buscar al Ganador del Día (Simulado con ganancia total por ahora)
    mejor_activo = df_portfolio.loc[df_portfolio['Ganancia'].idxmax()]
    col3.metric("🏆 Activo Estrella", mejor_activo['Activo'], f"+${mejor_activo['Ganancia']:.2f}")

    # Barra de Progreso
    st.write("### 🚀 Progreso de la Misión")
    st.progress(min(progreso, 1.0))
    if progreso >= 1.0:
        st.balloons()
        st.success("¡FELICIDADES! ¡META ALCANZADA! 🎉")

    # Gráficos
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🍰 ¿Dónde está mi dinero?")
        fig_pie = px.pie(df_portfolio, values='Valor_Total', names='Activo', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("📊 Tabla de Control")
        st.dataframe(df_portfolio[['Activo', 'Cantidad', 'Precio_Actual', 'Valor_Total', 'Ganancia']], hide_index=True)

    # Botón de actualización manual
    if st.button('🔄 Actualizar Precios Ahora'):
        st.rerun()
