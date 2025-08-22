import streamlit as st
import zipfile
import os
import pandas as pd

st.title('🐦 Visualización de Resultados del Modelo Predictivo')

st.info('Modelo multivariante para predecir abundancia y diversidad de aves según variables climáticas en el campus de la ESPOL ')

# 1. Ruta al archivo comprimido (ajusta según tu estructura de carpetas)
zip_path = os.path.join("data", "out.zip")

# 2. Extraer dentro de la carpeta data/
with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall("data")

# 3. Ahora leer el CSV extraído
csv_path = os.path.join("data", "out.csv")
df_out = pd.read_csv(csv_path)

# Para verificar
print(df_out.head())
