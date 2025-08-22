import streamlit as st
import pandas as pd

st.title('🐦 Visualización de Resultados del Modelo Predictivo')

st.info('Modelo multivariante para predecir abundancia y diversidad de aves según variables climáticas en el campus de la ESPOL ')

df_out = pd.read_csv(r"D:\Alan\TESIS\out.csv")
df
