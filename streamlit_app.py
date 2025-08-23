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

# Filtrado principal según la barra lateral
filtered = filter_df(df, scient, common)

# Mostrar el DataFrame filtrado
st.write("Datos Filtrados:", filtered)

#-------------------------------------

# Lista de especies disponibles para filtrar
mis_especies = df_out['COMMON NAME'].unique().tolist()

# Variables climáticas (asumidas según tu código)
variables_climaticas = ['T2M_MIN', 'T2M_MAX', 'PS', 'QV2M', 'WS10M_MAX', 
                        'PRECTOTCORR', 'T2M_RANGE', 'RH2M']

# Filtro de la especie seleccionado en la barra lateral (ya lo tienes)
especie_seleccionada = st.sidebar.selectbox("Selecciona una especie", mis_especies)

# Filtro de la variable climática
variable_seleccionada = st.sidebar.selectbox("Selecciona una variable climática", variables_climaticas)

# Ordenar los meses
orden_meses = ['01','02','03','04','05','06','07','08','09','10','11','12']

# Función para crear el gráfico
def generar_grafico(especie, var):
    # Filtrar los datos para la especie seleccionada
    datos = df_out[df_out['COMMON NAME'] == especie].copy()
    if datos.empty:
        st.warning(f"No hay datos para la especie '{especie}'.")
        return

    # Asegurar que MONTH esté formateado correctamente
    df_out['MONTH_x'] = df_out['MONTH_x'].astype(str).str.zfill(2)

    # Agregar promedio mensual de la variable climática
    clima = df_out.groupby('MONTH_x')[var].mean().reset_index()

    # Unir los datos de avistamientos con los de clima
    datos = pd.merge(datos, clima, on='MONTH_x', how='left')

    # Ordenar los meses correctamente
    datos['MONTH_x'] = pd.Categorical(datos['MONTH_x'], categories=orden_meses, ordered=True)
    datos = datos.sort_values('MONTH_x')

    # Verifica que no esté vacío después del merge
    if datos[var].isnull().all():
        st.warning(f"Todos los valores de {var} son NaN después del merge.")
        return

    # Crear el gráfico
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Eje izquierdo: log de avistamientos
    sns.lineplot(data=datos, x='MONTH_x', y='log_avistamientos', label='log10(Avistamientos + 1)', color='blue', ax=ax1)
    ax1.set_ylabel('log10(Avistamientos + 1)', color='blue')

    # Eje derecho: variable climática
    ax2 = ax1.twinx()
    sns.lineplot(data=datos, x='MONTH_x', y=var, label=var, color='red', ax=ax2)
    ax2.set_ylabel(var, color='red')

    # Título y ajustes
    plt.title(f'Avistamientos (log) y {var} por mes - {especie}')
    plt.xlabel('Mes')
    plt.tight_layout()

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)



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
