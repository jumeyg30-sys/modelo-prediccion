import streamlit as st
import zipfile
import os
import pandas as pd
from typing import List


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


def infer_climate_columns(df: pd.DataFrame) -> List[str]:
    """Devuelve la lista de columnas que consideraremos como variables climáticas.
    Se basa en tu lista declarada; ignora columnas de identificación y conteo."""
    declared = [
        "PRECTOTCORR", "PS", "QV2M", "RH2M", "T2M", "T2MDEW", "T2MWET",
        "T2M_MAX", "T2M_MIN", "T2M_RANGE", "TS", "WD10M", "WD2M",
        "WS10M", "WS10M_MAX", "WS10M_MIN", "WS10M_RANGE", "WS2M",
        "WS2M_MAX", "WS2M_MIN", "WS2M_RANGE",
    ]
    return [c for c in declared if c in df.columns]

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

#-------------------------------------------------------------------------
# Barra lateral (entrada de datos) para buscar por nombre común o científico
#--------------------------------------------------------------------------

st.sidebar.header("⚙️ Configuración & Filtros")
csv_default_path = "df_out.csv"
csv_path = st.sidebar.text_input("Ruta del CSV", value=csv_default_path)

# Asegúrate de cargar los datos primero
df = load_data("out.zip")

# Verificar que df es un DataFrame
if isinstance(df, pd.DataFrame):
    # Llamar a la función de inferencia de columnas climáticas
    CLIMATE_COLS = infer_climate_columns(df)
else:
    st.error("El archivo CSV no se cargó correctamente.")


# Mapas de nombres (para sincronizar filtros)
common_names = sorted(df["COMMON NAME"].dropna().unique()) if "COMMON NAME" in df.columns else []
scientific_names = sorted(df["SCIENTIFIC NAME"].dropna().unique()) if "SCIENTIFIC NAME" in df.columns else []

# Widgets de filtros — sincronizados
st.sidebar.subheader("🎯 Filtros por especie")
selected_common = st.sidebar.selectbox("Common Name", options=["(Todos)"] + common_names, index=0)
selected_scient = st.sidebar.selectbox("Scientific Name", options=["(Todos)"] + scientific_names, index=0)


common = None if selected_common == "(Todos)" else selected_common
scient = None if selected_scient == "(Todos)" else selected_scient

# Si el usuario escoge un common_name, acota el scientific y viceversa (visual)
if common:
    candidates = df.loc[df["COMMON NAME"] == common, "SCIENTIFIC NAME"].dropna().unique().tolist()
    st.sidebar.caption(f"Especies científicas para '{common}': {', '.join(sorted(set(map(str, candidates))))}")
if scient:
    candidates = df.loc[df["SCIENTIFIC NAME"] == scient, "COMMON NAME"].dropna().unique().tolist()
    st.sidebar.caption(f"Nombres comunes para '{scient}': {', '.join(sorted(set(map(str, candidates))))}")

st.sidebar.subheader("🌡️ Filtro de variable climática")
selected_var = st.sidebar.selectbox("Variable climática", options=CLIMATE_COLS if CLIMATE_COLS else ["(no hay)"])

st.sidebar.subheader("🗓️ Filtro de meses")
months_all = sorted(df["MONTH_x"].dropna().unique().astype(int)) if "MONTH_x" in df.columns else []
selected_months = st.sidebar.multiselect("Mes(es)", options=months_all, default=months_all)

# Filtrado principal según la barra lateral
filtered = filter_df(df, common, scient, selected_months)





