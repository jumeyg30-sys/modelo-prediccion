import streamlit as st
import zipfile
import os
import pandas as pd
from typing import List, Optional, Tuple

st.set_page_config(
    page_title="Avifauna & Clima — Dashboard",
    page_icon="🕊️",
    layout="wide",
)

st.title("🐦 Dashboard Avifauna & Variables Climáticas")
st.caption("Explora avistamientos por especie y su relación con variables climáticas. Filtra, compara y prepara insumos para tu modelo predictivo.")
st.info('Modelo multivariante para predecir abundancia y diversidad de aves según variables climáticas en el campus de la ESPOL ')

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
    common_name: Optional[str] = None,
    scientific_name: Optional[str] = None,
    month: Optional[str] = None,
    climate_var: Optional[str] = None
) -> pd.DataFrame:
    """Filtra el DataFrame según las especies comunes, científicas,
    el mes y la variable climática (si se proporcionan)."""
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

# Cargar datos desde ZIP
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

# Barra lateral (entrada de datos) para buscar por nombre común o científico
st.sidebar.header("⚙️ Configuración & Filtros")

# Filtros por especie (conexión entre nombre común y científico)
st.sidebar.subheader("🎯 Filtros por especie")
selected_common = st.sidebar.selectbox("Common Name", options=["(Todos)"] + common_names, index=0)

# Filtrar los científicos disponibles basados en el nombre común
if selected_common != "(Todos)":
    filtered_scientific_names = df[df["COMMON NAME"] == selected_common]["SCIENTIFIC NAME"].dropna().unique()
else:
    filtered_scientific_names = scientific_names

selected_scient = st.sidebar.selectbox("Scientific Name", options=["(Todos)"] + filtered_scientific_names, index=0)

# Si se selecciona un nombre común, actualizamos el científico y viceversa
common = None if selected_common == "(Todos)" else selected_common
scient = None if selected_scient == "(Todos)" else selected_scient

# Filtros por especie (conexión entre nombre común y científico)
st.sidebar.subheader("🎯 Filtros por especie")
selected_common = st.sidebar.selectbox("Common Name", options=["(Todos)"] + common_names, index=0)

# Filtrar los científicos disponibles basados en el nombre común
if selected_common != "(Todos)":
    filtered_scientific_names = df[df["COMMON NAME"] == selected_common]["SCIENTIFIC NAME"].dropna().unique()
else:
    filtered_scientific_names = scientific_names

selected_scient = st.sidebar.selectbox("Scientific Name", options=["(Todos)"] + filtered_scientific_names, index=0)

common = None if selected_common == "(Todos)" else selected_common
scient = None if selected_scient == "(Todos)" else selected_scient

# Filtrado de la data
filtered = filter_df(df, common, scient)

# Mostrar el DataFrame filtrado
st.write("Datos Filtrados:", filtered)








