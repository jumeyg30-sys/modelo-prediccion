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

#-------------------------------------------------------------------------
# Barra lateral (entrada de datos) para buscar por nombre común o científico
#--------------------------------------------------------------------------


# ------------------
# Barra lateral (entrada de datos)
# ------------------
st.sidebar.header("⚙️ Configuración & Filtros")

# Carga de datos
csv_path = "df_out.csv"  # Ruta del archivo CSV (ajustar según el archivo real)
df = load_data(csv_path)

# Filtros de la barra lateral
common_names = sorted(df["COMMON NAME"].dropna().unique()) if "COMMON NAME" in df.columns else []
scientific_names = sorted(df["SCIENTIFIC NAME"].dropna().unique()) if "SCIENTIFIC NAME" in df.columns else []

st.sidebar.subheader("🎯 Filtros por especie")
selected_common = st.sidebar.selectbox("Common Name", options=["(Todos)"] + common_names, index=0)
selected_scient = st.sidebar.selectbox("Scientific Name", options=["(Todos)"] + scientific_names, index=0)

common = None if selected_common == "(Todos)" else selected_common
scient = None if selected_scient == "(Todos)" else selected_scient

# Filtro de variable climática
st.sidebar.subheader("🌡️ Filtro de variable climática")
climate_columns = [
    "PRECTOTCORR", "PS", "QV2M", "RH2M", "T2M", "T2MDEW", "T2MWET",
    "T2M_MAX", "T2M_MIN", "T2M_RANGE", "TS", "WD10M", "WD2M",
    "WS10M", "WS10M_MAX", "WS10M_MIN", "WS10M_RANGE", "WS2M",
    "WS2M_MAX", "WS2M_MIN", "WS2M_RANGE",
]
selected_var = st.sidebar.selectbox("Variable climática", options=["(Todas)"] + climate_columns, index=0)

# Filtro de meses
months_all = sorted(df["MONTH_x"].dropna().unique().astype(int)) if "MONTH_x" in df.columns else []
selected_months = st.sidebar.multiselect("Mes(es)", options=months_all, default=months_all)

# Filtrado principal según los filtros de la barra lateral
filtered = filter_df(df, common, scient, selected_months, selected_var if selected_var != "(Todas)" else None)

# --------------------
# Secciones (Tabs principales)
# --------------------
tab_resumen, tab_especie, tab_variable = st.tabs([
    "📊 Resumen",
    "🕊️ Especie",
    "🌡️ Variable climática",
])

# -------------------
# Tab: Resumen global
# -------------------
with tab_resumen:
    st.subheader("Distribución de avistamientos por especie (top N)")

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

# ----------------
# Tab: Por especie
# ----------------
with tab_especie:
    st.subheader("Serie temporal de avistamientos y variable climática para la especie seleccionada")

    if filtered.empty:
        st.warning("No hay datos con los filtros actuales. Ajusta especie y/o meses.")
    else:
        # Serie temporal de avistamientos (promedio por mes/fecha)
        ts_av = agg_time_series(filtered, y_col="avistamientos", by_species=False)

        # Serie temporal de variable climática seleccionada
        if selected_var in filtered.columns:
            ts_clim = agg_time_series(filtered, y_col=selected_var, by_species=False)
        else:
            ts_clim = pd.DataFrame()

        # Construir figura con dos ejes Y si hay ambas series
        if not ts_av.empty and not ts_clim.empty:
            has_date = "YEAR_MONTH" in ts_av.columns and ts_av["YEAR_MONTH"].notna().any()
            x_label = "YEAR_MONTH" if has_date else "MONTH_x"

            fig = px.line(ts_av, x=x_label, y="avistamientos", title="Avistamientos en el tiempo")
            st.plotly_chart(fig, use_container_width=True)

            if not ts_clim.empty:
                fig_clim = px.line(ts_clim, x=x_label, y=selected_var, title=f"Comportamiento de {selected_var} en el tiempo")
                st.plotly_chart(fig_clim, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar las series temporales de avistamientos o variable climática.")

# ----------------------------  
# Tab: Por variable climática
# ----------------------------  
with tab_variable:
    st.subheader("Serie temporal para la variable climática seleccionada")

    if selected_var not in df.columns:
        st.warning("Selecciona una variable climática válida en la barra lateral.")
    else:
        ts_var = agg_time_series(filtered, y_col=selected_var, by_species=False)
        if ts_var.empty:
            st.info("No hay datos para construir la serie temporal con los filtros actuales.")
        else:
            has_date = "YEAR_MONTH" in ts_var.columns and ts_var["YEAR_MONTH"].notna().any()
            x_col = "YEAR_MONTH" if has_date else "MONTH_x"
            fig_v = px.line(ts_var, x=x_col, y=selected_var, title=f"{selected_var} en el tiempo")
            st.plotly_chart(fig_v, use_container_width=True)
