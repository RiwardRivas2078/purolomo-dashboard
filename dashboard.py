import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from database import get_session, PrecioHistorico, ProductoReferencia, Supermercado
from sqlalchemy import text, func
import re
from unicodedata import normalize
from collections import defaultdict
from datetime import date, datetime

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
# CSS PARA AMBOS TEMAS (MEJORADO PARA CENTRAR PRECIOS)
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
# BARRA SUPERIOR DE HERRAMIENTAS
# ============================================================================
col_t1, col_t2, col_t3 = st.columns([1, 1, 3])
with col_t1:
    tema_icono = "☀️" if st.session_state.tema == "light" else "🌙"
    st.button(f"{tema_icono} Tema", on_click=toggle_tema, help="Cambiar tema claro/oscuro")
with col_t2:
    estadistica_icono = "📊" if st.session_state.estadistica == "Mediana" else "📈"
    st.button(f"{estadistica_icono} {st.session_state.estadistica}", on_click=toggle_estadistica, help="Alternar entre mediana y promedio")
with col_t3:
    usar_usd = st.toggle("💰 USD", value=True)
    moneda = "USD" if usar_usd else "Bs"

# ============================================================================
# FUNCIONES AUXILIARES (sin cambios)
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
# CONEXIÓN A BD Y TABLAS AUXILIARES (sin cambios)
# ============================================================================
session = get_session()
marcas_propias = ['La Lucha', 'Punta de Monte', 'Alibal', 'Purolomo', 'San Blas', 'Purovo', 'Milpa']

session.execute(text("""
    CREATE TABLE IF NOT EXISTS match_manual (
        id SERIAL PRIMARY KEY,
        producto_propio_id INTEGER REFERENCES productos_referencia(id) ON DELETE CASCADE,
        nombre_original TEXT NOT NULL,
        creado_en TIMESTAMP DEFAULT NOW(),
        UNIQUE(producto_propio_id, nombre_original)
    )
"""))
session.execute(text("""
    CREATE TABLE IF NOT EXISTS reglas_match (
        producto_propio_id INTEGER PRIMARY KEY REFERENCES productos_referencia(id),
        palabras_incluir TEXT[] DEFAULT '{}',
        palabras_excluir TEXT[] DEFAULT '{}',
        creado_en TIMESTAMP DEFAULT NOW()
    )
"""))
session.commit()

# ============================================================================
# FILTROS DE FECHA Y SUPERMERCADOS (sin cambios)
# ============================================================================
st.markdown("### Filtros")
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    fechas = session.query(func.min(PrecioHistorico.fecha_extraccion), func.max(PrecioHistorico.fecha_extraccion)).first()
    min_fecha = fechas[0] if fechas[0] else date.today()
    max_fecha = fechas[1] if fechas[1] else date.today()
    fecha_inicio = st.date_input("Desde", min_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f2:
    fecha_fin = st.date_input("Hasta", max_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f3:
    st.write("")

super_con_datos = session.query(Supermercado).join(PrecioHistorico).filter(
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).distinct().all()
if not super_con_datos:
    st.error("No hay datos en el rango seleccionado.")
    st.stop()

super_options = {s.nombre: s.id for s in super_con_datos}
st.markdown("**Supermercados con datos:**")
selected_super_nombres = []
cols = st.columns(len(super_options))
for idx, (nombre, sid) in enumerate(super_options.items()):
    with cols[idx]:
        if st.checkbox(nombre, value=True, key=f"sup_{sid}"):
            selected_super_nombres.append(nombre)
selected_super_ids = [super_options[n] for n in selected_super_nombres]

st.markdown("---")
st.markdown("### 📦 Productos Purolomo & Aliados por supermercado")
if selected_super_nombres:
    cols_metric = st.columns(len(selected_super_nombres))
    for idx, sup_nombre in enumerate(selected_super_nombres):
        sup_id = super_options[sup_nombre]
        count = session.query(func.count(func.distinct(PrecioHistorico.nombre_original))).filter(
            PrecioHistorico.supermercado_id == sup_id,
            PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin),
            PrecioHistorico.producto_referencia_id.in_(
                session.query(ProductoReferencia.id).filter(ProductoReferencia.marca.in_(marcas_propias))
            )
        ).scalar()
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
# SELECTOR DE PRODUCTO PROPIO (sin cambios)
# ============================================================================
productos_propios = session.query(ProductoReferencia).filter(
    ProductoReferencia.marca.in_(marcas_propias),
    ProductoReferencia.activo == True
).all()
opciones = {f"{p.marca} - {p.nombre_producto} ({p.presentacion})" if p.presentacion else f"{p.marca} - {p.nombre_producto}": p.id for p in productos_propios}
producto_label = st.selectbox("🔍 Selecciona un producto propio:", list(opciones.keys()))
producto_id = opciones[producto_label]
producto_actual = session.get(ProductoReferencia, producto_id)

# Preconfigurar reglas para Arroz La Lucha
if producto_actual.nombre_producto == "Arroz La Lucha" and producto_actual.marca == "La Lucha":
    existe_regla = session.execute(text("SELECT 1 FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id}).fetchone()
    if not existe_regla:
        incluir_default = ['arroz']
        excluir_default = ['harina', 'morcilla', 'integral', 'dorado', '2 kg', '800 gr', 'basmati', 'arborio', 'jazmin', 'sushi', 'importado', 'gourmet', 'clasico', 'tradicional', 'la lucha', 'panquecas', 'mezcla', 'tosh', 'avena']
        session.execute(text("INSERT INTO reglas_match (producto_propio_id, palabras_incluir, palabras_excluir) VALUES (:pid, :incluir, :excluir)"), {"pid": producto_id, "incluir": incluir_default, "excluir": excluir_default})
        session.commit()
        st.info("📌 Reglas preconfiguradas para Arroz La Lucha (puedes modificarlas abajo).")

# ============================================================================
# PRECIOS DEL PRODUCTO PROPIO (sin cambios)
# ============================================================================
precios_propio = session.query(PrecioHistorico).filter(
    PrecioHistorico.producto_referencia_id == producto_id,
    PrecioHistorico.supermercado_id.in_(selected_super_ids),
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).all()
if not precios_propio:
    st.warning(f"⚠️ El producto '{producto_label}' no tiene precios en los supermercados seleccionados.")
    st.stop()

# ============================================================================
# COMPETIDORES: REGLAS O CATEGORÍA (sin cambios)
# ============================================================================
todos_precios = session.query(PrecioHistorico).filter(
    PrecioHistorico.supermercado_id.in_(selected_super_ids),
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).all()

reglas = session.execute(text("SELECT palabras_incluir, palabras_excluir FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id}).fetchone()
competidores = []
if reglas and (reglas[0] or reglas[1]):
    palabras_incluir = list(reglas[0]) if reglas[0] else []
    palabras_excluir = list(reglas[1]) if reglas[1] else []
    for p in todos_precios:
        if p.producto_referencia_id == producto_id:
            continue
        if cumple_reglas(p.nombre_original, palabras_incluir, palabras_excluir):
            competidores.append(p)
    st.info(f"📏 Usando reglas personalizadas: +{', '.join(palabras_incluir)}  -{', '.join(palabras_excluir)}")
else:
    categoria_propia = normalizar_categoria(producto_actual.nombre_producto)
    for p in todos_precios:
        if p.producto_referencia_id == producto_id:
            continue
        if normalizar_categoria(p.nombre_original) == categoria_propia:
            competidores.append(p)
    st.info(f"📏 Sin reglas, usando categoría: '{categoria_propia}'")

# ============================================================================
# TABLA COMPARATIVA (PRECIOS CENTRADOS - REFORZADO)
# ============================================================================
ultimos = {}
for p in (precios_propio + competidores):
    key = (p.supermercado_id, p.nombre_original)
    precio_val = p.precio_usd if usar_usd else p.precio_bs
    if key not in ultimos or p.fecha_extraccion > ultimos[key]["fecha"]:
        ultimos[key] = {
            "precio": float(precio_val),
            "fecha": p.fecha_extraccion,
            "nombre_original": p.nombre_original,
            "peso": extraer_peso(p.nombre_original),
            "supermercado_id": p.supermercado_id
        }

productos_unicos = sorted(set(k[1] for k in ultimos.keys()))
super_ids_unicos = sorted(set(k[0] for k in ultimos.keys()))
super_nombres = [session.get(Supermercado, sid).nombre for sid in super_ids_unicos]

# Crear DataFrame con nombres formateados (título)
df_valores = pd.DataFrame(index=[formatear_nombre_producto(prod) for prod in productos_unicos], columns=super_nombres)
for prod in productos_unicos:
    prod_formateado = formatear_nombre_producto(prod)
    for sid, sup_nombre in zip(super_ids_unicos, super_nombres):
        key = (sid, prod)
        if key in ultimos:
            df_valores.loc[prod_formateado, sup_nombre] = ultimos[key]["precio"]
        else:
            df_valores.loc[prod_formateado, sup_nombre] = None

# Identificar producto propio (usar el nombre formateado)
nombre_propio_tabla = None
for prod in productos_unicos:
    if producto_actual.nombre_producto.lower() in prod.lower() or producto_actual.marca.lower() in prod.lower():
        nombre_propio_tabla = formatear_nombre_producto(prod)
        break
if not nombre_propio_tabla and precios_propio:
    nombre_propio_tabla = formatear_nombre_producto(precios_propio[0].nombre_original)

# Formateo y centrado - con CSS adicional
def format_precio(val):
    if pd.isna(val):
        return "Sin datos"
    return f"{val:.2f} {moneda}"

styled = df_valores.style.format(format_precio)
# Forzar centrado de texto en celdas y encabezados
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

fecha_max = session.query(func.max(PrecioHistorico.fecha_extraccion)).filter(
    PrecioHistorico.supermercado_id.in_(selected_super_ids),
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).scalar()
fecha_max_str = fecha_max.strftime("%d/%m/%Y") if fecha_max else "desconocida"

st.subheader(f"🛒 Comparativa: {producto_actual.marca} - {producto_actual.nombre_producto}")
st.dataframe(styled, use_container_width=True, height=400)
st.markdown(f"<p class='centered-title'>📅 Datos actualizados al {fecha_max_str}</p>", unsafe_allow_html=True)

# ============================================================================
# KPIS Y COBERTURA (MEDIANA O PROMEDIO) - sin cambios
# ============================================================================
st.subheader("📈 Indicadores Clave")

# Identificar el nombre original del producto propio (sin formatear)
nombre_propio_original = None
for key in ultimos:
    if producto_actual.nombre_producto.lower() in key[1].lower() or producto_actual.marca.lower() in key[1].lower():
        nombre_propio_original = key[1]
        break
if not nombre_propio_original and precios_propio:
    nombre_propio_original = precios_propio[0].nombre_original

# Precios del producto propio
precios_propio_ult = []
for key, val in ultimos.items():
    if key[1] == nombre_propio_original:
        precios_propio_ult.append(val["precio"])

# Precios de la competencia (todos los demás)
precios_comp_ult = []
for key, val in ultimos.items():
    if key[1] != nombre_propio_original:
        precios_comp_ult.append(val["precio"])

# Calcular estadística
if st.session_state.estadistica == "Mediana":
    valor_prop = np.median(precios_propio_ult) if precios_propio_ult else 0
    valor_comp = np.median(precios_comp_ult) if precios_comp_ult else 0
    titulo_est = "Mediana"
else:
    valor_prop = np.mean(precios_propio_ult) if precios_propio_ult else 0
    valor_comp = np.mean(precios_comp_ult) if precios_comp_ult else 0
    titulo_est = "Promedio"

cobertura, datos_existentes, combinaciones_totales = calcular_cobertura(precios_comp_ult, productos_unicos, super_ids_unicos)

# Determinar clase CSS según comparación
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
        <strong>💰 {producto_actual.marca} ({titulo_est})</strong><br>
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

st.caption(f"🔍 Análisis basado en {datos_existentes} datos de precio (de un total de {combinaciones_totales} posibles). Cobertura: {cobertura:.1f}%. Estadística: {titulo_est}.")

# ============================================================================
# GRÁFICO EVOLUTIVO (CORREGIDO: FECHAS ÚNICAS)
# ============================================================================
st.subheader(f"📈 Evolución de precios - {titulo_est} de la competencia vs producto propio")

precios_comp_por_fecha = defaultdict(list)
for p in competidores:
    fecha = p.fecha_extraccion.date()
    precio = p.precio_usd if usar_usd else p.precio_bs
    precios_comp_por_fecha[fecha].append(precio)

fechas_ordenadas = sorted(precios_comp_por_fecha.keys())
datos_evol = []
for fecha in fechas_ordenadas:
    valores = precios_comp_por_fecha[fecha]
    if valores:
        if st.session_state.estadistica == "Mediana":
            stat_val = np.median(valores)
        else:
            stat_val = np.mean(valores)
        datos_evol.append({"Fecha": fecha, "Tipo": "Competencia", "Precio": stat_val})

precios_prop_por_fecha = defaultdict(list)
for p in precios_propio:
    fecha = p.fecha_extraccion.date()
    precio = p.precio_usd if usar_usd else p.precio_bs
    precios_prop_por_fecha[fecha].append(precio)
for fecha, valores in precios_prop_por_fecha.items():
    if valores:
        if st.session_state.estadistica == "Mediana":
            stat_val = np.median(valores)
        else:
            stat_val = np.mean(valores)
        datos_evol.append({"Fecha": fecha, "Tipo": producto_actual.marca, "Precio": stat_val})

# Convertir a DataFrame y asegurar que las fechas sean únicas en el eje X
df_evol = pd.DataFrame(datos_evol).sort_values("Fecha")
# Eliminar duplicados de fecha por tipo (no debería haber, pero por si acaso)
df_evol = df_evol.drop_duplicates(subset=["Fecha", "Tipo"])

if not df_evol.empty:
    colores_map = {producto_actual.marca: "#CC0000", "Competencia": "#00A859"}
    fig_evol = px.line(df_evol, x="Fecha", y="Precio", color="Tipo", markers=True,
                       labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                       color_discrete_map=colores_map,
                       title=f"Evolución - {titulo_est} diaria")
    fig_evol.update_traces(textposition="top center", texttemplate='%{y:.2f}', marker=dict(size=8))
    fig_evol.update_layout(
        plot_bgcolor="white",  # Fondo blanco siempre
        paper_bgcolor="white" if st.session_state.tema == "light" else "#2D2D2D",
        legend_title=None, height=450, hovermode="x unified",
        font=dict(color="black" if st.session_state.tema == "light" else "white")
    )
    # Forzar que el eje X muestre solo las fechas presentes, sin repetición
    fig_evol.update_xaxes(tickformat="%Y-%m-%d", tickangle=45, dtick="D1")
    st.plotly_chart(fig_evol, use_container_width=True)
else:
    st.info("No hay datos suficientes para el gráfico evolutivo.")

# ============================================================================
# BOXPLOT POR DÍA (sin cambios)
# ============================================================================
st.subheader("📊 Distribución de precios de la competencia por día (Boxplot)")
if competidores:
    box_data = []
    for p in competidores:
        fecha = p.fecha_extraccion.date()
        precio = p.precio_usd if usar_usd else p.precio_bs
        sup_nombre = session.get(Supermercado, p.supermercado_id).nombre
        box_data.append({"Fecha": fecha, "Precio": precio, "Supermercado": sup_nombre, "Producto": p.nombre_original})
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
# EDITOR DE REGLAS Y DIAGNÓSTICO (sin cambios)
# ============================================================================
with st.expander("✏️ Editar reglas de inclusión/exclusión para este producto"):
    st.markdown("""
    **Instrucciones:**  
    - **Incluir** (separado por comas): palabras que **deben** aparecer en el nombre del competidor.  
    - **Excluir** (separado por comas): palabras que **no** deben aparecer.  
    """)
    reglas_actuales = session.execute(text("SELECT palabras_incluir, palabras_excluir FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id}).fetchone()
    incluir_actual = ", ".join(reglas_actuales[0]) if reglas_actuales and reglas_actuales[0] else ""
    excluir_actual = ", ".join(reglas_actuales[1]) if reglas_actuales and reglas_actuales[1] else ""
    incluir_edit = st.text_input("Palabras que DEBEN aparecer", value=incluir_actual)
    excluir_edit = st.text_input("Palabras que NO deben aparecer", value=excluir_actual)
    if st.button("Guardar reglas"):
        nueva_incluir = [p.strip().lower() for p in incluir_edit.split(",") if p.strip()]
        nueva_excluir = [p.strip().lower() for p in excluir_edit.split(",") if p.strip()]
        session.execute(text("DELETE FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id})
        session.execute(text("INSERT INTO reglas_match (producto_propio_id, palabras_incluir, palabras_excluir) VALUES (:pid, :incluir, :excluir)"), {"pid": producto_id, "incluir": nueva_incluir, "excluir": nueva_excluir})
        session.commit()
        st.success("Reglas guardadas. Recargando página...")
        st.rerun()

with st.expander("🔍 Diagnóstico (reglas y competidores rechazados)"):
    if reglas and (reglas[0] or reglas[1]):
        st.write(f"**Reglas activas:** Incluir: {', '.join(palabras_incluir)} | Excluir: {', '.join(palabras_excluir)}")
        st.write("**Competidores ACEPTADOS (mostrados en tabla):**")
        for p in competidores[:20]:
            st.write(f"✅ {p.nombre_original}")
        st.write("**Competidores RECHAZADOS (primeros 20):**")
        rechazados = [p for p in todos_precios if p.producto_referencia_id != producto_id and not cumple_reglas(p.nombre_original, palabras_incluir, palabras_excluir)]
        for p in rechazados[:20]:
            st.write(f"❌ {p.nombre_original}")
    else:
        st.write("No hay reglas definidas, se usa categoría automática.")

session.close()
st.caption("🚀 Los gráficos evolutivos y KPIs se basan en la estadística seleccionada (Mediana/Promedio). La tabla tiene precios centrados, nombres en formato título y resalta el producto propio. El boxplot muestra puntos sin desplazamiento lateral (outliers alineados verticalmente) y fondo blanco en modo oscuro.")