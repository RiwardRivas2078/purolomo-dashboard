import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import date
import re
import os

st.set_page_config(page_title="Market Intelligence - Purolomo", layout="wide")

# ============================================================================
# CARGA DE DATOS DESDE CSVs (sin base de datos)
# ============================================================================
@st.cache_data
def cargar_datos():
    # Cargar Gamma
    df_gamma = pd.read_csv("Historico_Gamma.csv", parse_dates=["fecha"])
    df_gamma["supermercado"] = "Excelsior Gama"
    # Si existe Plan Suarez, cargarlo
    if os.path.exists("Historico_PlanSuarez.csv"):
        df_plan = pd.read_csv("Historico_PlanSuarez.csv", parse_dates=["fecha"])
        df_plan["supermercado"] = "Plan Suarez"
        df = pd.concat([df_gamma, df_plan], ignore_index=True)
    else:
        df = df_gamma
    # Renombrar columnas para que coincidan con el dashboard (ajusta según tu CSV)
    # En tu CSV las columnas se llaman: fecha, nombre, precio_usd, precio_bs, etc.
    df.rename(columns={
        "nombre": "nombre_original",
        "precio_usd": "precio_usd",
        "precio_bs": "precio_bs",
        "fecha": "fecha_extraccion"
    }, inplace=True)
    # Identificar productos propios (marca La Lucha en el nombre original)
    df["es_propio"] = df["nombre_original"].str.contains("LA LUCHA", case=False, na=False)
    return df

df = cargar_datos()

# ============================================================================
# FUNCIONES AUXILIARES (extraer peso, etc.)
# ============================================================================
def extraer_peso(nombre):
    if not nombre:
        return ""
    patron = r'(\d+(?:[.,]\d+)?)\s*(kg|kilo|gr|g)'
    match = re.search(patron, nombre.lower())
    if match:
        cantidad = float(match.group(1).replace(',', '.'))
        unidad = match.group(2)
        if unidad in ['kg', 'kilo']:
            return f"{int(cantidad)}kg" if cantidad.is_integer() else f"{cantidad}kg"
        elif unidad in ['gr', 'g']:
            return f"{int(cantidad)}gr" if cantidad.is_integer() else f"{cantidad}gr"
    return ""

# ============================================================================
# INTERFAZ DE USUARIO (igual que antes, pero usando df en lugar de BD)
# ============================================================================
st.title("📊 Market Intelligence - Purolomo")
st.caption("Datos desde CSVs históricos")

# Filtros en sidebar
with st.sidebar:
    usar_usd = st.toggle("USD", value=True)
    moneda = "USD" if usar_usd else "Bs"
    # Fechas
    min_fecha = df["fecha_extraccion"].min().date()
    max_fecha = df["fecha_extraccion"].max().date()
    fecha_inicio = st.date_input("Desde", min_fecha, min_value=min_fecha, max_value=max_fecha)
    fecha_fin = st.date_input("Hasta", max_fecha, min_value=min_fecha, max_value=max_fecha)
    # Supermercados
    supermercados = df["supermercado"].unique()
    seleccion_sup = st.multiselect("Supermercados", supermercados, default=supermercados.tolist())

# Filtrar datos por fecha y supermercado
mask = (df["fecha_extraccion"].dt.date >= fecha_inicio) & (df["fecha_extraccion"].dt.date <= fecha_fin) & (df["supermercado"].isin(seleccion_sup))
df_filtrado = df[mask]

# Obtener lista de productos propios (los que contienen "LA LUCHA" en el nombre)
productos_propios = df_filtrado[df_filtrado["es_propio"]]["nombre_original"].unique()
if len(productos_propios) == 0:
    st.warning("No hay productos propios en los datos filtrados.")
    st.stop()

producto_seleccionado = st.selectbox("Producto propio", productos_propios)

# Filtrar precios del producto propio
precios_propio = df_filtrado[df_filtrado["nombre_original"] == producto_seleccionado]
# Competencia: otros productos que no son propios (puedes refinar con reglas si quieres)
competidores = df_filtrado[~df_filtrado["es_propio"]]

# Tabla comparativa (último precio por supermercado)
ultimos_propio = precios_propio.groupby("supermercado").last().reset_index()
ultimos_comp = competidores.groupby(["supermercado", "nombre_original"]).last().reset_index()

# Mostrar tabla (puedes adaptar según tu estilo)
st.subheader(f"Comparativa: {producto_seleccionado}")
# ... (aquí puedes mostrar una tabla pivote similar a la que tenías, pero yo te pongo un ejemplo simple)
if not ultimos_propio.empty:
    st.write("Precios del producto propio:")
    st.dataframe(ultimos_propio[["supermercado", "precio_usd"]])
# KPIs
precio_prom_prop = ultimos_propio["precio_usd"].mean()
precio_prom_comp = ultimos_comp["precio_usd"].mean()
st.metric("Promedio propio", f"{precio_prom_prop:.2f} USD")
st.metric("Promedio competencia", f"{precio_prom_comp:.2f} USD")
