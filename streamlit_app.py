import streamlit as st
import zipfile
import os
import pandas as pd
from typing import List, Optional, Tuple
import plotly.express as px

st.set_page_config(
    page_title="Avifauna & Clima — Dashboard",
    page_icon="🕊️",
    layout="wide",
)

# ------------------------------------------------------------------------------
# Cargar datos
# ------------------------------------------------------------------------------

@st.cache_data  # usa la caché de Streamlit para no recargar el CSV en cada cambio
def load_data(path: str) -> pd.DataFrame:
    """Carga el DataFrame desde un archivo CSV.

    Args:
        path: Ruta al archivo CSV que contiene df_out. Debe contener las
            columnas mencionadas en la descripción del usuario: YEAR_MONTH,
            COMMON NAME, SCIENTIFIC NAME, LAT, LON, y las variables climáticas.

    Returns:
        pd.DataFrame: DataFrame con los datos.
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        csv_files = [n for n in z.namelist() if n.lower().endswith(".csv")]
        
        if not csv_files:
            st.error("El ZIP no contiene ningún archivo CSV")
            st.stop()

        # Tomamos el primer archivo CSV
        csv_name = csv_files[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f)
    # Convertir la columna YEAR_MONTH en fecha para facilitar los filtros y
    # ordenamientos. Si tu formato es "YYYY-MM", pandas lo convertirá
    # correctamente a un Timestamp con el primer día del mes.
    if "YEAR_MONTH" in df.columns:
        df["YEAR_MONTH"] = pd.to_datetime(df["YEAR_MONTH"], errors="coerce")
    return df


def main() -> None:
    """Función principal que define la interfaz y la lógica de la app."""

    # --------------------------------------------------------------------------
    # Título y descripción
    # --------------------------------------------------------------------------
    # Las funciones st.title, st.header y st.write se usan para mostrar texto en
    # la aplicación. Según la documentación, st.title genera un texto grande
    # ideal como título【382884099989979†L98-L108】; st.header y st.subheader se
    # utilizan para secciones y subsecciones【382884099989979†L115-L129】, y
    # st.write permite añadir párrafos o incluso dataframes【382884099989979†L138-L149】.
    st.title("Dashboard interactivo de avifauna y variables climáticas")
    st.write(
        """
        Esta aplicación permite explorar la abundancia de avifauna en relación con
        variables climáticas. Usa los filtros en la barra lateral para seleccionar
        una especie y una variable climática y explora los gráficos generados.
        """
    )

    # --------------------------------------------------------------------------
    # Cargar el dataset
    # --------------------------------------------------------------------------
    # Ajusta la ruta al CSV según tu entorno. Por ejemplo, si el archivo se
    # encuentra en un directorio de datos dentro de tu proyecto, usa
    # 'data/df_out.csv'. Si estás trabajando en GitHub Desktop, pon la ruta
    # relativa desde la raíz del repositorio.
    
    data_path = "df_out.zip"   # ajusta al nombre de tu archivo
    df = load_data(data_path)

    # --------------------------------------------------------------------------
    # Definición de filtros en la barra lateral
    # --------------------------------------------------------------------------
    st.sidebar.header("Filtros")

    # Lista de nombres comunes y científicos únicos, ordenados alfabéticamente.
    # Se usan selectboxes (menús desplegables) para que el usuario elija una
    # opción. Los selectboxes devuelven la opción seleccionada【883161431007632†L375-L389】.
    common_names = sorted(df["COMMON NAME"].dropna().unique())

    # Selección de nombre común
    selected_common = st.sidebar.selectbox(
        "Seleccione el nombre común", options=common_names
    )

    # Filtra las opciones de nombre científico según el nombre común elegido. De
    # este modo, se evita que el usuario seleccione combinaciones inexistentes.
    possible_scientific = (
        df.loc[df["COMMON NAME"] == selected_common, "SCIENTIFIC NAME"]
        .dropna()
        .unique()
    )
    scientific_names = sorted(possible_scientific)
    selected_scientific = st.sidebar.selectbox(
        "Seleccione el nombre científico", options=scientific_names
    )

    # Lista de variables climáticas disponibles. Puedes agregar o quitar
    # variables dependiendo de tu DataFrame. Estas columnas deben existir en
    # df_out.
    climate_variables = [
        "PRECTOTCORR",
        "PS",
        "QV2M",
        "RH2M",
        "T2M",
        "T2MDEW",
        "T2MWET",
        "T2M_MAX",
        "T2M_MIN",
        "T2M_RANGE",
        "TS",
        "WD10M",
        "WD2M",
        "WS10M",
        "WS10M_MAX",
        "WS10M_MIN",
        "WS10M_RANGE",
        "WS2M",
        "WS2M_MAX",
        "WS2M_MIN",
        "WS2M_RANGE",
    ]
    available_vars = [var for var in climate_variables if var in df.columns]
    selected_var = st.sidebar.selectbox(
        "Seleccione una variable climática", options=available_vars
    )

    # --------------------------------------------------------------------------
    # Filtrar el DataFrame según las selecciones del usuario
    # --------------------------------------------------------------------------
    # Combinamos los filtros de nombre común y nombre científico. Esto nos
    # proporciona el subconjunto de datos para la especie seleccionada.
    species_df = df[
        (df["COMMON NAME"] == selected_common)
        & (df["SCIENTIFIC NAME"] == selected_scientific)
    ]

    # --------------------------------------------------------------------------
    # Visualización 1: Avistamientos totales por especie
    # --------------------------------------------------------------------------
    st.header("Avistamientos por especie")
    # Calcula la suma de avistamientos por nombre común. Si tu DataFrame usa
    # otra columna para el conteo (por ejemplo, log_avistamientos), modifica
    # accordingly.
    if "avistamientos" in df.columns:
        av_counts = df.groupby("COMMON NAME")["avistamientos"].sum().reset_index()
        fig_bar = px.bar(
            av_counts,
            x="COMMON NAME",
            y="avistamientos",
            title="Cantidad total de avistamientos por especie",
            labels={"COMMON NAME": "Especie", "avistamientos": "Avistamientos"},
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info(
            "La columna 'avistamientos' no está presente en el DataFrame. No se puede generar el gráfico de barras."
        )

# ------------------------
# Secciones (Tabs principales)
# ------------------------
tab_resumen, tab_especie, tab_variable, tab_modelos = st.tabs([
    "📊 Resumen",
    "🕊️ Especie",
    "🌡️ Variable climática",
    "🧠 Modelos",
])

# -------------------
# Tab: Resumen global
# -------------------
with tab_resumen:
    st.subheader("Distribución de avistamientos por especie (top N)")

    # Agrega por COMMON NAME
    if "COMMON NAME" in df.columns and "avistamientos" in df.columns:
        agg = (
            df.groupby("COMMON NAME", as_index=False)["avistamientos"].sum()
              .sort_values("avistamientos", ascending=False)
        )
        top_n = st.slider("¿Cuántas especies mostrar?", min_value=5, max_value=min(50, len(agg)), value=min(20, len(agg)))
        agg_top = agg.head(top_n)
        fig_bar = px.bar(
            agg_top,
            x="COMMON NAME",
            y="avistamientos",
            title="Avistamientos totales por especie",
        )
        fig_bar.update_layout(xaxis_title="Especie (Common Name)", yaxis_title="Avistamientos")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No se encuentran columnas 'COMMON NAME' y/o 'avistamientos'.")
