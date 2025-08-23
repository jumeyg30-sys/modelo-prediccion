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

from typing import Optional

def filter_df(
    df_out: pd.DataFrame,
    common_name: Optional[str] = None,
    scientific_name: Optional[str] = None,
    month: Optional[str] = None,
    climate_var: Optional[str] = None
) -> pd.DataFrame:
    """
    Filtra el DataFrame según las especies comunes, científicas,
    el mes y la variable climática (si se proporcionan).
    """
    if common_name:
        df_out = df_out[df_out["COMMON NAME"] == common_name]
    
    if scientific_name:
        df_out = df_out[df_out["SCIENTIFIC NAME"] == scientific_name]
    
    if month:
        df_out = df_out[df_out["YEAR_MONTH"].str.contains(month)]
    
    if climate_var:
        df_out = df_out[df_out[climate_var].notnull()]  # Filtrar valores no nulos en la variable climática
    
    return df_out


def agg_time_series(
    df: pd.DataFrame,
    y_col: str,
    by_species: bool = False,
) -> pd.DataFrame:
    """Agrega por tiempo (YEAR_MONTH) y opcionalmente por especie.
    Si YEAR_MONTH no existe o es nulo, intenta usar MONTH_x como alternativa (no ideal)."""
    has_date = "YEAR_MONTH" in df.columns and df["YEAR_MONTH"].notna().any()
    if has_date:
        group_cols = ["YEAR_MONTH"]
    else:
        group_cols = ["MONTH_x"]  # fallback

    if by_species:
        group_cols = group_cols + ["COMMON NAME", "SCIENTIFIC NAME"]

    g = df.groupby(group_cols, dropna=True, as_index=False)[y_col].mean()
    # Orden temporal
    if has_date:
        g = g.sort_values("YEAR_MONTH")
    else:
        g = g.sort_values("MONTH_x")
    return g

