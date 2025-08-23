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
def load_data(zip_path: str) -> pd.DataFrame:
    """
    Carga el archivo CSV desde un archivo ZIP en el directorio.
    Utiliza Streamlit cache para optimizar el rendimiento y evitar recargas repetidas.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            # Filtrar los archivos CSV dentro del ZIP
            csv_files = [n for n in z.namelist() if n.lower().endswith(".csv")]
            
            # Si no hay archivos CSV dentro del ZIP, mostrar error
            if not csv_files:
                st.error("El ZIP no contiene ningún archivo CSV")
                st.stop()

            # Si hay varios CSV, toma el primero
            csv_name = csv_files[0]
            st.write(f"Leyendo: {csv_name}")  # Opcional, para depuración

            # Abrir el archivo CSV y cargarlo en un DataFrame
            with z.open(csv_name) as f:
                df_out = pd.read_csv(f)

        st.success("CSV cargado correctamente")
        return df_out
    
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo ZIP: {str(e)}")
        st.stop()
        
# Llamada de la función y muestra de los primeros datos
df_out = load_data("out.zip")  # Asegúrate de que el archivo ZIP esté en el directorio correcto
st.dataframe(df_out.head())



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

def agg_time_series(
    df: pd.DataFrame,
    y_col: str,
    by_species: bool = False,
) -> pd.DataFrame:


