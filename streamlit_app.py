import streamlit as st
import zipfile
import os
import pandas as pd
from typing import List, Optional, Tuple

import streamlit as st
import zipfile
import os
import pandas as pd
from typing import List, Optional

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
def load_data(zip_path: str) -> pd.DataFrame:
    """Carga los datos desde un archivo ZIP y realiza las conversiones necesarias."""
    with zipfile.ZipFile(zip_path, "r") as z:
        csv_files = [n for n in z.namelist() if n.lower().endswith(".csv")]
        
        if not csv_files:
            st.error("El ZIP no contiene ningún archivo CSV")
            st.stop()

        # Tomamos el primer archivo CSV
        csv_name = csv_files[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f)
    
    # Normalizaciones útiles
    if "YEAR_MONTH" in df.columns:
        # Convertir YEAR_MONTH a string
        df["YEAR_MONTH"] = df["YEAR_MONTH"].astype(str)
    
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
    df_out: pd.DataFrame,
    scientific_name: Optional[str] = None,
    month: Optional[str] = None,
    climate_var: Optional[str] = None
) -> pd.DataFrame:
    """Filtra el DataFrame según el nombre científico, el mes y la variable climática (si se proporcionan)."""
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

# Cargar datos desde ZIP
df = load_data("out.zip")

# Verificar que df es un DataFrame
if isinstance(df, pd.DataFrame):
    # Llamar a la función de inferencia de columnas climáticas
    CLIMATE_COLS = infer_climate_columns(df)
else:
    st.error("El archivo CSV no se cargó correctamente.")

# Mapas de nombres (para sincronizar filtros)
scientific_names = sorted(df["SCIENTIFIC NAME"].dropna().unique()) if "SCIENTIFIC NAME" in df.columns else []

# Barra lateral (entrada de datos) para buscar por nombre científico
st.sidebar.header("⚙️ Configuración & Filtros")

# Filtro por nombre científico
st.sidebar.subheader("🎯 Filtro por nombre científico")
selected_scient = st.sidebar.selectbox("Scientific Name", options=["(Todos)"] + scientific_names, index=0)

# Si se selecciona un nombre científico, filtrar los datos
scient = None if selected_scient == "(Todos)" else selected_scient

# Filtro de variable climática
st.sidebar.subheader("🌡️ Filtro de variable climática")
selected_var = st.sidebar.selectbox("Variable climática", options=CLIMATE_COLS if CLIMATE_COLS else ["(no hay)"])

# Filtro de meses
st.sidebar.subheader("🗓️ Filtro de meses")
months_all = sorted(df["MONTH_x"].dropna().unique().astype(int)) if "MONTH_x" in df.columns else []
selected_months = st.sidebar.multiselect("Mes(es)", options=months_all, default=months_all)

# Filtrado de la data
filtered = filter_df(df, selected_scient, selected_months, selected_var)

# Mostrar el DataFrame filtrado
st.write("Datos Filtrados:", filtered)
