import streamlit as st
import zipfile
import os
import pandas as pd

st.title('🐦 Visualización de Resultados del Modelo Predictivo')

st.info('Modelo multivariante para predecir abundancia y diversidad de aves según variables climáticas en el campus de la ESPOL ')

import streamlit as st
import pandas as pd
import zipfile
import os

ZIP_PATH = "out.zip"   # mismo directorio que streamlit_app.py

# Diagnóstico rápido (puedes quitarlo luego)
st.write("cwd:", os.getcwd())
st.write("archivos aquí:", os.listdir("."))

# Abrir el ZIP y leer el primer CSV que encuentre
with zipfile.ZipFile(ZIP_PATH, "r") as z:
    csv_files = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not csv_files:
        st.error("El ZIP no contiene ningún .csv")
        st.stop()

    # Si hay varios CSV, toma el primero (ajústalo si necesitas uno en específico)
    csv_name = csv_files[0]
    st.write("Leyendo:", csv_name)

    with z.open(csv_name) as f:
        df_out = pd.read_csv(f)

st.success("CSV cargado correctamente")
st.dataframe(df_out.head())
