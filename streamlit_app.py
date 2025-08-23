import streamlit as st
import zipfile
import os
import pandas as pd

st.set_page_config(
    page_title="Avifauna & Clima — Dashboard",
    page_icon="🕊️",
    layout="wide",
)

st.title("🐦 Dashboard Avifauna & Variables Climáticas")
st.caption("Explora avistamientos por especie y su relación con variables climáticas. Filtra, compara y prepara insumos para tu modelo predictivo.")
st.info('Modelo multivariante para predecir abundancia y diversidad de aves según variables climáticas en el campus de la ESPOL ')


# ---------------------------------
# Utilidades y carga de datos (cache)
# ---------------------------------
@st.cache_data(show_spinner=True)
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Normalizaciones útiles
    # Convertir YEAR_MONTH a periodo/fecha si es posible
    if "YEAR_MONTH" in df.columns:
        # Intenta parsear como YYYY-MM o YYYY-MM-DD
        try:
            df["YEAR_MONTH"] = pd.to_datetime(df["YEAR_MONTH"], errors="coerce")
        except Exception:
            pass



