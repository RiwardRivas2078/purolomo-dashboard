import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re
from unicodedata import normalize
from collections import defaultdict
from datetime import date, datetime
import os

# ============================================================================
# CONFIGURACIÓN DE TEMA Y ESTADÍSTICA
# ============================================================================
st.set_page_config(page_title="Market Intelligence - Purolomo", page_icon="🐔", layout="wide")

if "tema" not in st.session_state:
    st.session_state.tema = "light"
if "estadistica" not in st.session_state:
    st.session_state.estadistica = "Mediana"

def toggle_tema():
    st.session_state.tema = "dark" if st.session_state.tema == "light" else "light"

def toggle_estadistica():
    st.session_state.estadistica = "Promedio" if st.session_state.estadistica == "Mediana" else "Mediana"

# ============================================================================
# CSS PARA AMBOS TEMAS (igual que tu original)
# ============================================================================
if st.session_state.tema == "light":
    tema_css = """
    <style>
        .stApp { background-color: #F8F9FA; }
        .stApp, .stMarkdown, .stDataFrame, .stSelectbox, .stMultiSelect, .stDateInput, .stCheckbox, .stToggle, .stButton { color: #1E1E1E; }
        h1, h2, h3 { color: #CC0000 !important; }
        .metric-red { background-color: #FFF5F5; border-left: 6px solid #CC0000; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); color: #1E1E1E; }
        .metric-green { background-color: #F0FFF4; border-left: 6px solid #00A859; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); color: #1E1E1E; }
        .metric-neutral { background-color: #F2F2F2; border-left: 6px solid #6C757D; border-radius: 16px; padding: 16px; color: #1E1E1E; }
        .super-metric { background-color: white; border-radius: 20px; padding: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-top: 3px solid #CC0000; }
        .stButton button { background-color: #CC0000; color: white; border-radius: 30px; font-weight: bold; border: none; }
        .stButton button:hover { background-color: #00A859; }
        .stCheckbox label { background-color: white; padding: 6px 14px; border-radius: 30px; border: 1px solid #E5E5E5; }
        .stCheckbox label:hover { border-color: #CC0000; background-color: #FFF5F5; }
        .stDataFrame { background-color: white; }
        .stDataFrame th { background-color: #F0F0F0; text-align: center !important; }
        .stDataFrame td { background-color: white; text-align: center !important; }
        .centered-title { text-align: center; }
    </style>
    """
else:
    tema_css = """
    <style>
        .stApp { background-color: #1E1E1E; }
        .stApp, .stMarkdown, .stDataFrame, .stSelectbox, .stMultiSelect, .stDateInput, .stCheckbox, .stToggle, .stButton { color: #FFFFFF !important; }
        h1, h2, h3 { color: #CC0000 !important; }
        .metric-red { background-color: #2D2D2D; border-left: 6px solid #CC0000; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.3); color: #FFFFFF; }
        .metric-green { background-color: #2D2D2D; border-left: 6px solid #00A859; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.3); color: #FFFFFF; }
        .metric-neutral { background-color: #2D2D2D; border-left: 6px solid #6C757D; border-radius: 16px; padding: 16px; color: #FFFFFF; }
        .super-metric { background-color: #2D2D2D; border-radius: 20px; padding: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2); border-top: 3px solid #CC0000; color: white; }
        .stButton button { background-color: #CC0000; color: white; border-radius: 30px; font-weight: bold; border: none; }
        .stButton button:hover { background-color: #00A859; }
        .stCheckbox label { background-color: #2D2D2D; padding: 6px 14px; border-radius: 30px; border: 1px solid #555; color: white; }
        .stCheckbox label:hover { border-color: #CC0000; background-color: #3D3D3D; }
        .stDataFrame { background-color: #2D2D2D; color: white; }
        .stDataFrame th { background-color: #3D3D3D; color: white; text-align: center !important; }
        .stDataFrame td { background-color: #2D2D2D; color: white; text-align: center !important; }
        .centered-title { text-align: center; color: white; }
    </style>
    """

st.markdown(tema_css, unsafe_allow_html=True)

# Logo centrado
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        st.image("LOGO_PUROLOMO.PNG", use_container_width=True)
    except:
        st.warning("Logo no encontrado")

st.title("📊 Market Intelligence - Purolomo & Marcas Aliadas")
st.caption("Comparativa de precios con reglas personalizadas")

# ============================================================================
# CARGA DE DATOS DESDE CSVs (reemplaza PostgreSQL)
# ============================================================================
@st.cache_data
def cargar_datos():
    # Cargar Gamma
    df_gamma = pd.read_csv("Historico_Gamma.csv", parse_dates=["fecha"])
    df_gamma["supermercado"] = "Excelsior Gama"
    if os.path.exists("Historico_PlanSuarez.csv"):
        df_plan = pd.read_csv("Historico_PlanSuarez.csv", parse_dates=["fecha"])
        df_plan["supermercado"] = "Plan Suarez"
        df = pd.concat([df_gamma, df_plan], ignore_index=True)
    else:
        df = df_gamma
    # Renombrar columnas
    df.rename(columns={
        "nombre": "nombre_original",
        "precio_usd": "precio_usd",
        "precio_bs": "precio_bs",
        "fecha": "fecha_extraccion",
        "categoria_principal": "categoria"
    }, inplace=True)
    # Agregar columna es_propio: cualquier producto que contenga "LA LUCHA" en el nombre
    df["es_propio"] = df["nombre_original"].str.contains("LA LUCHA", case=False, na=False)
    # Asignar un ID de producto_referencia simulado (para compatibilidad con el resto del código)
    # Para el propio, usaremos 1; para la competencia, un ID único por nombre.
    df["producto_referencia_id"] = 0
    propios = df[df["es_propio"]]["nombre_original"].unique()
    for idx, nombre in enumerate(propios, start=1):
        df.loc[df["nombre_original"] == nombre, "producto_referencia_id"] = idx
    # Para competidores, asignamos IDs negativos distintos
    competidores = df[~df["es_propio"]]["nombre_original"].unique()
    for idx, nombre in enumerate(competidores, start=1000):
        df.loc[df["nombre_original"] == nombre, "producto_referencia_id"] = idx
    return df

df = cargar_datos()

# ============================================================================
# FUNCIONES AUXILIARES (las mismas que tenías, sin cambios)
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

def normalizar_categoria(nombre):
    if not nombre:
        return ""
    texto = normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('ASCII').lower()
    marcas = [
        'la lucha', 'punta de monte', 'alibal', 'purolomo', 'san blas', 'purovo', 'milpa',
        'renata', 'mary', 'pantera', 'plumrose', 'gama', 'dulce mar', 'montserratina',
        'movilla', 'mallorca', 'oscar mayer', 'ricci', 'tovar', 'san jose', 'sky chefs',
        'chocozuela', 'quaker', 'kellogg', 'post', 'maizoritos', 'miduchy', 'naru',
        'jossie', 'primor', 'competencia', 'el drago', 'fiesta', 'la leonesa', 'tigo'
    ]
    for m in marcas:
        texto = re.sub(rf'\b{re.escape(m)}\b', '', texto)
    texto = re.sub(r'\b(de|la|el|los|las|para|con|sin|y|o|a|ante|bajo|cabe|contra|desde|durante|en|entre|hacia|hasta|mediante|por|según|so|sobre|tras|blanco|integral|premium|superior|extra|light|fresco|natural|original|tipo|clásico|deluxe|gourmet|familiar|económico|canilla|tipo)\b', '', texto)
    texto = re.sub(r'[^\w\s]', ' ', texto)
    palabras = [p for p in texto.split() if len(p) > 2 and not p.isdigit()]
    return palabras[0] if palabras else "sin_categoria"

def cumple_reglas(nombre_producto, palabras_incluir, palabras_excluir):
    import re
    nombre_norm = normalize('NFKD', nombre_producto.lower()).encode('ASCII', 'ignore').decode('ASCII')
    nombre_norm = re.sub(r'[^a-z0-9]', '', nombre_norm)
    for p in palabras_incluir:
        p_norm = normalize('NFKD', p.lower()).encode('ASCII', 'ignore').decode('ASCII')
        p_norm = re.sub(r'[^a-z0-9]', '', p_norm)
        if p_norm not in nombre_norm:
            return False
    for p in palabras_excluir:
        p_norm = normalize('NFKD', p.lower()).encode('ASCII', 'ignore').decode('ASCII')
        p_norm = re.sub(r'[^a-z0-9]', '', p_norm)
        if p_norm in nombre_norm:
            return False
    return True

def calcular_cobertura(precios_comp_ult, productos_unicos, super_ids_unicos):
    total_combinaciones_posibles = len(productos_unicos) * len(super_ids_unicos)
    total_datos_existentes = len(precios_comp_ult)
    cobertura = (total_datos_existentes / total_combinaciones_posibles) * 100 if total_combinaciones_posibles > 0 else 0
    return cobertura, total_datos_existentes, total_combinaciones_posibles

def formatear_nombre_producto(nombre):
    if not nombre:
        return nombre
    palabras = nombre.lower().split()
    return " ".join(palabras).capitalize()

# ============================================================================
# TABLA AUXILIAR DE REGLAS (simulada con diccionario, ya que no tenemos BD)
# ============================================================================
# Para simplificar, almacenaremos las reglas en session_state
if "reglas_match" not in st.session_state:
    st.session_state.reglas_match = {}

def guardar_reglas(producto_id, incluir, excluir):
    st.session_state.reglas_match[producto_id] = {"incluir": incluir, "excluir": excluir}

def obtener_reglas(producto_id):
    return st.session_state.reglas_match.get(producto_id, {"incluir": [], "excluir": []})

# ============================================================================
# FILTROS DE FECHA Y SUPERMERCADOS (usando el DataFrame)
# ============================================================================
# Obtener lista de supermercados y fechas desde df
super_list = sorted(df["supermercado"].unique())
min_fecha = df["fecha_extraccion"].min().date()
max_fecha = df["fecha_extraccion"].max().date()

st.markdown("### Filtros")
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    fecha_inicio = st.date_input("Desde", min_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f2:
    fecha_fin = st.date_input("Hasta", max_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f3:
    st.write("")

st.markdown("**Supermercados con datos:**")
selected_super_nombres = []
cols = st.columns(len(super_list))
for idx, nombre in enumerate(super_list):
    with cols[idx]:
        if st.checkbox(nombre, value=True, key=f"sup_{nombre}"):
            selected_super_nombres.append(nombre)
if not selected_super_nombres:
    selected_super_nombres = super_list

# Filtrar datos
mask = (df["fecha_extraccion"].dt.date >= fecha_inicio) & (df["fecha_extraccion"].dt.date <= fecha_fin) & (df["supermercado"].isin(selected_super_nombres))
df_filtrado = df[mask]

# Métrica de productos propios
st.markdown("---")
st.markdown("### 📦 Productos Purolomo & Aliados por supermercado")
cols_metric = st.columns(len(selected_super_nombres))
for idx, sup_nombre in enumerate(selected_super_nombres):
    count = df_filtrado[(df_filtrado["supermercado"] == sup_nombre) & df_filtrado["es_propio"]]["nombre_original"].nunique()
    with cols_metric[idx]:
        st.markdown(f"""
        <div class="super-metric">
            <strong>{sup_nombre}</strong><br>
            <span style="font-size: 1.8rem; color:#CC0000;">{count}</span><br>
            <span style="font-size: 0.7rem;">productos aliados</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SELECTOR DE PRODUCTO PROPIO (usando es_propio)
# ============================================================================
productos_propios = df_filtrado[df_filtrado["es_propio"]]["nombre_original"].unique()
if len(productos_propios) == 0:
    st.error("No hay productos propios en los datos filtrados.")
    st.stop()
opciones = {formatear_nombre_producto(prod): prod for prod in productos_propios}
producto_label_display = st.selectbox("🔍 Selecciona un producto propio:", list(opciones.keys()))
producto_original = opciones[producto_label_display]

# Obtener el ID de producto_referencia para este producto (el que asignamos al cargar)
producto_id = df_filtrado[df_filtrado["nombre_original"] == producto_original]["producto_referencia_id"].iloc[0]

# ============================================================================
# REGLAS DE MATCH (desde session_state)
# ============================================================================
reglas = obtener_reglas(producto_id)
palabras_incluir = reglas["incluir"]
palabras_excluir = reglas["excluir"]

# ============================================================================
# PRECIOS DEL PRODUCTO PROPIO
# ============================================================================
precios_propio = df_filtrado[df_filtrado["nombre_original"] == producto_original]

if precios_propio.empty:
    st.warning(f"⚠️ El producto '{producto_label_display}' no tiene precios en los supermercados seleccionados.")
    st.stop()

# ============================================================================
# COMPETIDORES: usando reglas o categoría (igual que tu código original)
# ============================================================================
todos_precios = df_filtrado[df_filtrado["nombre_original"] != producto_original]
competidores = []
if palabras_incluir or palabras_excluir:
    for _, row in todos_precios.iterrows():
        if cumple_reglas(row["nombre_original"], palabras_incluir, palabras_excluir):
            competidores.append(row)
    st.info(f"📏 Usando reglas personalizadas: +{', '.join(palabras_incluir)}  -{', '.join(palabras_excluir)}")
else:
    categoria_propia = normalizar_categoria(producto_original)
    for _, row in todos_precios.iterrows():
        if normalizar_categoria(row["nombre_original"]) == categoria_propia:
            competidores.append(row)
    st.info(f"📏 Sin reglas, usando categoría: '{categoria_propia}'")

# Convertir lista de dicts a DataFrame
if competidores:
    competidores = pd.DataFrame(competidores)
else:
    competidores = pd.DataFrame()

# ============================================================================
# TABLA COMPARATIVA (últimos precios)
# ============================================================================
# Combinar propio y competidores
todos_items = pd.concat([precios_propio, competidores]) if not competidores.empty else precios_propio

# Obtener último precio por (supermercado, nombre_original)
ultimos = {}
for _, row in todos_items.iterrows():
    key = (row["supermercado"], row["nombre_original"])
    precio_val = row["precio_usd"] if usar_usd else row["precio_bs"]
    if key not in ultimos or row["fecha_extraccion"] > ultimos[key]["fecha"]:
        ultimos[key] = {
            "precio": float(precio_val),
            "fecha": row["fecha_extraccion"],
            "nombre_original": row["nombre_original"],
            "peso": extraer_peso(row["nombre_original"])
        }

productos_unicos = sorted(set(v["nombre_original"] for v in ultimos.values()))
super_unicos = sorted(set(k[0] for k in ultimos.keys()))
super_nombres = super_unicos

# Crear DataFrame con nombres formateados
df_valores = pd.DataFrame(index=[formatear_nombre_producto(prod) for prod in productos_unicos], columns=super_nombres)
for prod in productos_unicos:
    prod_formateado = formatear_nombre_producto(prod)
    for sup in super_unicos:
        key = (sup, prod)
        if key in ultimos:
            df_valores.loc[prod_formateado, sup] = ultimos[key]["precio"]
        else:
            df_valores.loc[prod_formateado, sup] = None

# Identificar fila del producto propio
nombre_propio_tabla = formatear_nombre_producto(producto_original)

# Estilos: centrado y resaltado
def format_precio(val):
    if pd.isna(val):
        return "Sin datos"
    return f"{val:.2f} {moneda}"

styled = df_valores.style.format(format_precio)
styled = styled.set_table_styles([
    {'selector': 'th', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
    {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]}
])
styled = styled.set_properties(**{'text-align': 'center'})

def resaltar_fila(row):
    if row.name == nombre_propio_tabla:
        return ['background-color: #D4EDDA; font-weight: bold;'] * len(row)
    return [''] * len(row)
styled = styled.apply(resaltar_fila, axis=1)

st.subheader(f"🛒 Comparativa: {producto_label_display}")
st.dataframe(styled, use_container_width=True, height=400)

# Fecha máxima en los datos mostrados
fecha_max_str = df_filtrado["fecha_extraccion"].max().strftime("%d/%m/%Y")
st.markdown(f"<p class='centered-title'>📅 Datos actualizados al {fecha_max_str}</p>", unsafe_allow_html=True)

# ============================================================================
# KPIS Y COBERTURA
# ============================================================================
st.subheader("📈 Indicadores Clave")

precios_propio_ult = [v["precio"] for k, v in ultimos.items() if k[1] == producto_original]
precios_comp_ult = [v["precio"] for k, v in ultimos.items() if k[1] != producto_original]

if st.session_state.estadistica == "Mediana":
    valor_prop = np.median(precios_propio_ult) if precios_propio_ult else 0
    valor_comp = np.median(precios_comp_ult) if precios_comp_ult else 0
    titulo_est = "Mediana"
else:
    valor_prop = np.mean(precios_propio_ult) if precios_propio_ult else 0
    valor_comp = np.mean(precios_comp_ult) if precios_comp_ult else 0
    titulo_est = "Promedio"

cobertura = (len(precios_comp_ult) / (len(productos_unicos) * len(super_unicos))) * 100 if super_unicos else 0

if valor_prop > valor_comp:
    clase_metric = "metric-red"
    mensaje = "⚠️ Precio por encima de la competencia"
    icono = "🔴"
elif valor_prop < valor_comp:
    clase_metric = "metric-green"
    mensaje = "✅ Precio por debajo de la competencia"
    icono = "🟢"
else:
    clase_metric = "metric-neutral"
    mensaje = "⚖️ Precio igual a la competencia"
    icono = "⚪"

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="{clase_metric}">
        <strong>💰 {producto_label_display.split(' - ')[0]} ({titulo_est})</strong><br>
        <span style="font-size: 1.8rem;">{valor_prop:.2f} {moneda}</span>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="{clase_metric}">
        <strong>🏷️ Competencia ({titulo_est})</strong><br>
        <span style="font-size: 1.8rem;">{valor_comp:.2f} {moneda}</span>
    </div>
    """, unsafe_allow_html=True)
with col3:
    diff = valor_prop - valor_comp
    diff_rel = (diff / valor_comp) * 100 if valor_comp else 0
    st.markdown(f"""
    <div class="{clase_metric}">
        <strong>📊 Diferencia</strong><br>
        <span style="font-size: 1.6rem;">{diff:+.2f} {moneda}</span><br>
        <span style="font-size: 0.9rem;">({diff_rel:+.1f}%)</span><br>
        <span style="font-size: 0.85rem;">{icono} {mensaje}</span>
    </div>
    """, unsafe_allow_html=True)

st.caption(f"🔍 Análisis basado en {len(precios_comp_ult)} datos de precio (de un total de {len(productos_unicos) * len(super_unicos)} posibles). Cobertura: {cobertura:.1f}%. Estadística: {titulo_est}.")

# ============================================================================
# GRÁFICO EVOLUTIVO (igual que tu original)
# ============================================================================
st.subheader(f"📈 Evolución de precios - {titulo_est} de la competencia vs producto propio")

precios_comp_por_fecha = defaultdict(list)
for _, row in competidores.iterrows():
    fecha = row["fecha_extraccion"].date()
    precio = row["precio_usd"] if usar_usd else row["precio_bs"]
    precios_comp_por_fecha[fecha].append(precio)

precios_prop_por_fecha = defaultdict(list)
for _, row in precios_propio.iterrows():
    fecha = row["fecha_extraccion"].date()
    precio = row["precio_usd"] if usar_usd else row["precio_bs"]
    precios_prop_por_fecha[fecha].append(precio)

datos_evol = []
for fecha, valores in precios_comp_por_fecha.items():
    if valores:
        stat = np.median(valores) if st.session_state.estadistica == "Mediana" else np.mean(valores)
        datos_evol.append({"Fecha": fecha, "Tipo": "Competencia", "Precio": stat})
for fecha, valores in precios_prop_por_fecha.items():
    if valores:
        stat = np.median(valores) if st.session_state.estadistica == "Mediana" else np.mean(valores)
        datos_evol.append({"Fecha": fecha, "Tipo": producto_label_display.split(' - ')[0], "Precio": stat})

df_evol = pd.DataFrame(datos_evol).sort_values("Fecha")
if not df_evol.empty:
    colores_map = {producto_label_display.split(' - ')[0]: "#CC0000", "Competencia": "#00A859"}
    fig_evol = px.line(df_evol, x="Fecha", y="Precio", color="Tipo", markers=True,
                       labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                       color_discrete_map=colores_map,
                       title=f"Evolución - {titulo_est} diaria")
    fig_evol.update_traces(textposition="top center", texttemplate='%{y:.2f}', marker=dict(size=8))
    fig_evol.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white" if st.session_state.tema == "light" else "#2D2D2D",
        legend_title=None, height=450, hovermode="x unified",
        font=dict(color="black" if st.session_state.tema == "light" else "white")
    )
    fig_evol.update_xaxes(tickformat="%Y-%m-%d", tickangle=45)
    st.plotly_chart(fig_evol, use_container_width=True)
else:
    st.info("No hay datos suficientes para el gráfico evolutivo.")

# ============================================================================
# BOXPLOT POR DÍA
# ============================================================================
st.subheader("📊 Distribución de precios de la competencia por día (Boxplot)")
if not competidores.empty:
    box_data = []
    for _, row in competidores.iterrows():
        fecha = row["fecha_extraccion"].date()
        precio = row["precio_usd"] if usar_usd else row["precio_bs"]
        sup = row["supermercado"]
        box_data.append({"Fecha": fecha, "Precio": precio, "Supermercado": sup, "Producto": row["nombre_original"]})
    df_box = pd.DataFrame(box_data)
    fig_box = px.box(df_box, x="Fecha", y="Precio", points="all",
                     labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                     title="Distribución diaria de precios de competidores",
                     color_discrete_sequence=["#00A859"])
    fig_box.update_traces(
        marker=dict(size=6, color="#00A859", opacity=0.7),
        jitter=0,
        pointpos=0,
        hovertemplate='<b>Producto:</b> %{text}<br><b>Precio:</b> %{y:.2f}<extra></extra>',
        text=df_box['Producto'] + ' (' + df_box['Supermercado'] + ')'
    )
    fig_box.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white" if st.session_state.tema == "light" else "#2D2D2D",
        height=450,
        font=dict(color="black" if st.session_state.tema == "light" else "white")
    )
    fig_box.update_xaxes(tickformat="%Y-%m-%d", tickangle=45)
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("No hay competidores para mostrar boxplot.")

# ============================================================================
# EDITOR DE REGLAS (manual, sin BD)
# ============================================================================
with st.expander("✏️ Editar reglas de inclusión/exclusión para este producto"):
    st.markdown("""
    **Instrucciones:**  
    - **Incluir** (separado por comas): palabras que **deben** aparecer en el nombre del competidor.  
    - **Excluir** (separado por comas): palabras que **no** deben aparecer.  
    """)
    incluir_actual = ", ".join(palabras_incluir)
    excluir_actual = ", ".join(palabras_excluir)
    incluir_edit = st.text_input("Palabras que DEBEN aparecer", value=incluir_actual)
    excluir_edit = st.text_input("Palabras que NO deben aparecer", value=excluir_actual)
    if st.button("Guardar reglas"):
        nueva_incluir = [p.strip().lower() for p in incluir_edit.split(",") if p.strip()]
        nueva_excluir = [p.strip().lower() for p in excluir_edit.split(",") if p.strip()]
        guardar_reglas(producto_id, nueva_incluir, nueva_excluir)
        st.success("Reglas guardadas. Recargando página...")
        st.rerun()

with st.expander("🔍 Diagnóstico (reglas y competidores rechazados)"):
    st.write(f"**Reglas activas:** Incluir: {palabras_incluir} | Excluir: {palabras_excluir}")
    st.write("**Competidores ACEPTADOS (mostrados en tabla):**")
    for prod in productos_unicos:
        if prod != producto_original:
            st.write(f"✅ {prod}")
    st.write("**Competidores RECHAZADOS (primeros 20):**")
    # Mostrar algunos que no cumplen reglas (si las hay)
    rechazados = todos_precios[~todos_precios["nombre_original"].isin(productos_unicos)]
    for _, row in rechazados.head(20).iterrows():
        st.write(f"❌ {row['nombre_original']}")

st.caption("🚀 Los gráficos evolutivos y KPIs se basan en la estadística seleccionada (Mediana/Promedio). La tabla tiene precios centrados, nombres en formato título y resalta el producto propio. Las reglas se guardan solo durante la sesión (al recargar se pierden).")
