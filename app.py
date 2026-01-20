import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ruta a los $1,200", page_icon="📱", layout="wide")

# --- 1. CONEXIÓN A DATOS (GOOGLE SHEETS) ---
# ¡ASEGÚRATE DE QUE ESTE ENLACE SEA EL CSV (output=csv)!
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRSJ7HUzdMFxd__pO3CqfckWPtpH-Z_9we9fOq5xaBGaprEiWHBGnQ-hcH4t-I-jZp35LGhElnXe65N/pub?output=csv" 

@st.cache_data(ttl=10)
def load_data():
    try:
        # header=0 asegura que lea la primera fila como títulos
        df = pd.read_csv(sheet_url, header=0)
        # Limpiamos espacios en los nombres de las columnas (ej: "Ticker " -> "Ticker")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return pd.DataFrame()

df_portfolio = load_data()

# --- 2. FUNCIÓN DE PRECIOS ROBUSTA ---
def get_current_prices(tickers):
    if not tickers:
        return {}
    try:
        # Descarga datos del día actual
        data = yf.download(tickers, period="1d", progress=False)
        
        # Manejo especial si data viene vacía o con formato complejo
        if data.empty:
            st.warning("⚠️ No se encontraron datos en Yahoo Finance. Revisa los Tickers en tu Excel (ej: usa 'BTC-USD' en vez de 'BTC').")
            return {}
            
        # Extraer solo el precio de cierre ('Close')
        # Si descargamos un solo activo, pandas devuelve una Series. Si son varios, un DataFrame.
        closes = data['Close']
        
        # Tomamos el último valor disponible (.iloc[-1])
        if isinstance(closes, pd.DataFrame):
             return closes.iloc[-1].to_dict()
        else:
             # Si es un solo activo, el nombre de la columna es el ticker o hay que manejarlo manual
             return {tickers[0]: closes.iloc[-1]}
             
    except Exception as e:
        st.error(f"⚠️ Error conectando con el mercado: {e}")
        return {}

# --- LÓGICA PRINCIPAL ---
st.title("📱 Mi Misión: Celular Nuevo ($1,500)")

if df_portfolio.empty:
    st.info("Esperando datos... Verifica que tu enlace en 'app.py' sea correcto.")
elif 'Ticker' not in df_portfolio.columns:
    st.error("❌ Error: No encuentro la columna 'Ticker' en tu Excel. Revisa la Fila 1.")
else:
    # --- LAVADORA DE DATOS (NUEVO) ---
    # Convertimos Tickers a texto limpio
    df_portfolio['Ticker'] = df_portfolio['Ticker'].astype(str).str.strip()
    
    # Convertimos números forzosamente (quitamos $ y , si existen)
    cols_num = ['Cantidad', 'Precio_Compra']
    for col in cols_num:
        # Esto elimina '$' y ',' y convierte a número. Si falla, pone 0.
        df_portfolio[col] = df_portfolio[col].astype(str).str.replace(r'[$,]', '', regex=True)
        df_portfolio[col] = pd.to_numeric(df_portfolio[col], errors='coerce').fillna(0)

    # --- OBTENER PRECIOS ---
    tickers_list = df_portfolio['Ticker'].unique().tolist()
    current_prices = get_current_prices(tickers_list)

    # Calcular valores (usando 0 si no encuentra precio para no romper la app)
    df_portfolio['Precio_Actual'] = df_portfolio['Ticker'].apply(lambda x: current_prices.get(x, 0))
    
    # Aviso si algún precio vino en 0
    if (df_portfolio['Precio_Actual'] == 0).any():
        st.warning("⚠️ Algunos activos tienen precio $0. Revisa que los Tickers en Excel terminen en '-USD' para cripto.")

    df_portfolio['Valor_Total'] = df_portfolio['Cantidad'] * df_portfolio['Precio_Actual']
    df_portfolio['Ganancia'] = df_portfolio['Valor_Total'] - (df_portfolio['Cantidad'] * df_portfolio['Precio_Compra'])
    
    total_actual = df_portfolio['Valor_Total'].sum()
    meta = 1500  
    progreso = (total_actual / meta)
    falta = meta - total_actual

    # --- 3. DASHBOARD VISUAL ---
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Capital Actual", f"${total_actual:,.2f}", f"{progreso*100:.1f}% de la Meta")
    col2.metric("🎯 Falta para el Celular", f"${falta:,.2f}", delta_color="inverse")
    
    # Buscar Ganador (evitando error si todo es 0)
    if total_actual > 0:
        mejor_activo = df_portfolio.loc[df_portfolio['Ganancia'].idxmax()]
        col3.metric("🏆 Activo Estrella", mejor_activo['Activo'], f"+${mejor_activo['Ganancia']:,.2f}")

    st.write("### 🚀 Progreso de la Misión")
    st.progress(min(progreso, 1.0))
    
    st.divider()
    
    # Solo mostramos gráficos si hay dinero
    if total_actual > 0:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🍰 Diversificación")
            fig_pie = px.pie(df_portfolio, values='Valor_Total', names='Activo', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            st.subheader("📊 Tabla Detallada")
            st.dataframe(df_portfolio[['Activo', 'Cantidad', 'Precio_Actual', 'Valor_Total', 'Ganancia']], hide_index=True)
    else:
        st.info("🔍 Tus datos se cargaron, pero el valor total es $0. Revisa los Tickers en el Excel.")

    if st.button('🔄 Actualizar Datos'):
        st.rerun()
