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

    # Asegurar tipo numérico para columnas climáticas y avistamientos
    numeric_cols = [
        "PRECTOTCORR", "PS", "QV2M", "RH2M", "T2M", "T2MDEW", "T2MWET",
        "T2M_MAX", "T2M_MIN", "T2M_RANGE", "TS", "WD10M", "WD2M",
        "WS10M", "WS10M_MAX", "WS10M_MIN", "WS10M_RANGE", "WS2M",
        "WS2M_MAX", "WS2M_MIN", "WS2M_RANGE", "avistamientos", "log_avistamientos",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Estándares de nombre (quitar espacios laterales)
    for c in ["COMMON NAME", "SCIENTIFIC NAME"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    return df


def filter_df(
    df: pd.DataFrame,
    common_name: Optional[str],
    scientific_name: Optional[str],
    months: List[int] | None,
) -> pd.DataFrame:
    out = df.copy()
    if common_name:
        out = out[out["COMMON NAME"] == common_name]
    if scientific_name:
        out = out[out["SCIENTIFIC NAME"] == scientific_name]
    if months and "MONTH_x" in out.columns:
        out = out[out["MONTH_x"].isin(months)]
    return out


