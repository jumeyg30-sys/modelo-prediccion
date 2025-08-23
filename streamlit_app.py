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

import streamlit as st
import pandas as pd
import zipfile
import os
import zipfile
import pandas as pd
import streamlit as st

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
