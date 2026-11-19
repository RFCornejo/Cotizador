import streamlit as st
import pandas as pd
import os
import hashlib
import procesador_bd as pbd
import procesador_mad as pmad
import generar_excel_profesional as gep
import generar_pdf_profesional as gpp

st.set_page_config(page_title="Sistema de Preciario de Mantenimientos Toyota", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BD_DIR = os.path.join(BASE_DIR, "BD")
MAD_DIR = os.path.join(BASE_DIR, "MAD")

# ==============================================================================
# CARGA E INDEXACIÓN DEL CATÁLOGO DE MODELOS Y MAESTRO MAD
# ==============================================================================

@st.cache_data(show_spinner=False)
def obtener_catalogo():
    return pbd.indexar_modelos_bd(BD_DIR)

@st.cache_resource(show_spinner=False)
def obtener_catalogo_mad():
    return pmad.cargar_catalogo_mad(MAD_DIR)

with st.spinner("⏳ Cargando catálogo de modelos y maestro de materiales (MAD)..."):
    catalogo = obtener_catalogo()
    try:
        df_mad, mad_lookup = obtener_catalogo_mad()
        mad_disponible = True
    except Exception as e:
        df_mad = pd.DataFrame()
        mad_lookup = {}
        mad_disponible = False

if not catalogo:
    st.error("❌ No se encontraron bases de datos en la carpeta 'BD'. Por favor verifica que los archivos .xls estén presentes.")
    st.stop()

# ==============================================================================
# BARRA LATERAL: FILTROS Y ESTADÍSTICAS
# ==============================================================================

st.sidebar.title("🚗 Toyota Preciario")
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Filtros de Catálogo")

familias_disponibles = ["Todas las familias"] + sorted(list(set(m["familia"] for m in catalogo)))
familia_sel = st.sidebar.selectbox("Filtrar por Familia Toyota:", familias_disponibles)

if familia_sel != "Todas las familias":
    modelos_disponibles = [m for m in catalogo if m["familia"] == familia_sel]
else:
    modelos_disponibles = catalogo

st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Información de la Base de Datos")
st.sidebar.caption(f"**Total de familias:** {len(familias_disponibles) - 1}")
st.sidebar.caption(f"**Total de modelos disponibles:** {len(catalogo)}")
st.sidebar.caption(f"**Modelos en filtro activo:** {len(modelos_disponibles)}")

if mad_disponible:
    st.sidebar.markdown("---")
    st.sidebar.success(f"📦 **Maestro MAD Activo**\n\n{len(df_mad):,} materiales sincronizados con precios VVP y descuentos DCTO oficiales.")
else:
    st.sidebar.warning("⚠️ Carpeta MAD no detectada o con error. Se usarán precios de la BD.")

# ==============================================================================
# BÚSQUEDA Y SELECCIÓN DE MODELO
# ==============================================================================

st.title("Simulador de Preciario de Mantenimientos Toyota")

busqueda = st.text_input(
    "Buscar modelo",
    placeholder="Ej: 2362, GUN126, Hilux, Yaris, Corolla, RAV4..."
)

if busqueda:
    b_term = busqueda.lower().strip()
    modelos_filtrados = [
        m for m in modelos_disponibles
        if (b_term in m["codigo_modelo"].lower() or
            b_term in m["version"].lower() or
            b_term in m["familia"].lower() or
            b_term in m["desc_modelo"].lower())
    ]
else:
    modelos_filtrados = modelos_disponibles

if not modelos_filtrados:
    st.warning("⚠️ No se encontraron modelos que coincidan con la búsqueda.")
    st.stop()

opciones_dict = {m["label"]: m for m in modelos_filtrados}
opcion_sel = st.selectbox("Seleccionar modelo", list(opciones_dict.keys()), key="sel_modelo")
modelo_info = opciones_dict[opcion_sel]

# ==============================================================================
# CARGAR DETALLE DEL MODELO SELECCIONADO
# ==============================================================================

@st.cache_data(show_spinner=False)
def obtener_detalle(archivo_path, hoja_name):
    return pbd.cargar_detalle_modelo(archivo_path, hoja_name)

detalle = obtener_detalle(modelo_info["archivo"], modelo_info["hoja"])
intervalo = detalle["intervalo_km"]
modelo_nombre = f"{modelo_info['familia']} {detalle['desc_modelo']} ({modelo_info['codigo_modelo']})"

st.info(f"📋 **{modelo_nombre}** | Versión: `{modelo_info['version']}` | Intervalo sugerido: **{intervalo:,} km**")

# ==============================================================================
# GESTIÓN DEL ESTADO DE ÍTEMS (REPUESTOS Y FLUIDOS SINCRONIZADOS CON MAD)
# ==============================================================================

def inicializar_items_modelo():
    """Inicializa la lista de repuestos y fluidos sincronizándolos con el catálogo MAD."""
    items_rep = []
    for idx, r in enumerate(detalle.get("repuestos_items", []), 1):
        cod = str(r["codigo"]).strip().upper()
        found = pmad.buscar_en_mad(cod, mad_lookup) if mad_disponible else None
        
        if found:
            vv_unit = float(found["vv_unit"])
            dscto = float(found["dscto"])
            desc = found["descripcion"] or r["descripcion"]
            origen = "MAD"
        else:
            vv_unit = float(r["vv_unit"])
            dscto = 0.0
            desc = r["descripcion"]
            origen = "BD"

        items_rep.append({
            "id": f"REP_{idx}_{cod}",
            "tipo": "REPUESTO",
            "codigo": cod,
            "descripcion": desc,
            "cantidad": float(r["cantidad"]),
            "vv_unit": vv_unit,
            "dscto": dscto,
            "km_cantidades": dict(r.get("km_cantidades", {})),
            "origen": origen
        })

    items_flu = []
    for idx, f in enumerate(detalle.get("fluidos_items", []), 1):
        cod = str(f["codigo"]).strip().upper()
        found = pmad.buscar_en_mad(cod, mad_lookup) if mad_disponible else None

        if found:
            vv_unit = float(found["vv_unit"])
            dscto = float(found["dscto"])
            desc = found["descripcion"] or f["descripcion"]
            origen = "MAD"
        else:
            vv_unit = float(f["vv_unit"])
            dscto = 0.0
            desc = f["descripcion"]
            origen = "BD"

        items_flu.append({
            "id": f"FLU_{idx}_{cod}",
            "tipo": "FLUIDO",
            "codigo": cod,
            "descripcion": desc,
            "cantidad": float(f["cantidad"]),
            "vv_unit": vv_unit,
            "dscto": dscto,
            "km_cantidades": dict(f.get("km_cantidades", {})),
            "origen": origen
        })

    st.session_state.items_repuestos = items_rep
    st.session_state.items_fluidos = items_flu
    st.session_state.current_model_key = modelo_info["label"]

# Inicializar o actualizar si cambia el modelo
if st.session_state.get("current_model_key") != modelo_info["label"]:
    inicializar_items_modelo()

# ==============================================================================
# PARÁMETROS DE COTIZACIÓN
# ==============================================================================

kms_posibles = detalle["kms"]

km_inicio_default = intervalo if intervalo in kms_posibles else kms_posibles[0]
km_fin_default_val = intervalo * 10
km_fin_default = km_fin_default_val if km_fin_default_val in kms_posibles else kms_posibles[-1]

col1, col2 = st.columns(2)
with col1:
    km_inicio = st.selectbox(
        "KM inicial",
        kms_posibles,
        index=kms_posibles.index(km_inicio_default) if km_inicio_default in kms_posibles else 0
    )
with col2:
    km_fin = st.selectbox(
        "KM final",
        kms_posibles,
        index=kms_posibles.index(km_fin_default) if km_fin_default in kms_posibles else len(kms_posibles) - 1
    )

if km_inicio > km_fin:
    st.error("El KM inicial no puede ser mayor al KM final.")
    st.stop()

incluir_terceros = st.checkbox("Incluir servicios de terceros (Lavado, Balanceo, Gastos Operativos)", value=True)

# KMs del rango
kms = []
if km_inicio == 0 or km_inicio == 1000:
    kms = [1000]

kms += [k for k in kms_posibles if k >= max(intervalo, km_inicio) and k <= km_fin]
kms = sorted(list(set(kms)))

def fmt_km(col):
    try:
        val = int(col)
        if val == 1000:
            return "1K"
        return f"{val // 1000}K"
    except (ValueError, TypeError):
        return str(col)

# ==============================================================================
# CONFIGURACIÓN DE DESCUENTOS Y MANO DE OBRA
# ==============================================================================

st.subheader("⚙️ Configuración de Tarifas y Descuentos Generales (0 - 100%)")

col_mo1, col_mo2 = st.columns(2)
with col_mo1:
    precio_hh = st.number_input(
        "Precio Hora Hombre (S/)",
        value=float(detalle["precio_hh_sugerido"]),
        step=1.0
    )
with col_mo2:
    descuento_mo = st.slider("Descuento Mano de Obra %", 0, 100, 0, step=1)

with st.expander("🎯 Aplicar Descuentos Rápidos por Categoría (Repuestos / Fluidos)", expanded=False):
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**Descuento Masivo en Repuestos**")
        d_gen_rep = st.slider("Descuento para todos los repuestos %", 0, 100, 0, step=1, key="slider_gen_rep")
        if st.button("Aplicar % a todos los Repuestos", key="btn_apply_gen_rep"):
            for r in st.session_state.items_repuestos:
                r["dscto"] = float(d_gen_rep)
            st.success(f"Se aplicó {d_gen_rep}% de descuento a todos los repuestos.")
            st.rerun()

    with col_d2:
        st.markdown("**Descuento Masivo en Fluidos**")
        d_gen_flu = st.slider("Descuento para todos los fluidos %", 0, 100, 0, step=1, key="slider_gen_flu")
        if st.button("Aplicar % a todos los Fluidos", key="btn_apply_gen_flu"):
            for f in st.session_state.items_fluidos:
                f["dscto"] = float(d_gen_flu)
            st.success(f"Se aplicó {d_gen_flu}% de descuento a todos los fluidos.")
            st.rerun()

    st.markdown("---")
    if st.button("🔄 Restablecer todos los descuentos al estándar de MAD / BD", key="btn_reset_dctos"):
        inicializar_items_modelo()
        st.success("Descuentos restablecidos a los valores originales de MAD / BD.")
        st.rerun()

# ==============================================================================
# CONSTRUCCIÓN DE TABLAS DE REPUESTOS Y FLUIDOS
# ==============================================================================

def construir_tabla_materiales(items, kms_cols):
    """Construye un DataFrame con las fórmulas oficiales y totales por columna de KM."""
    rows = []
    for idx, it in enumerate(items, 1):
        cant = float(it["cantidad"])
        vv_unit = float(it["vv_unit"])
        vv_venta = round(cant * vv_unit, 2)
        dscto = float(it["dscto"])
        vv_final = round(vv_venta * (1 - dscto / 100), 2)

        r_dict = {
            "Item": idx,
            "Código": it["codigo"],
            "Descripción": it["descripcion"],
            "Cant.": cant,
            "V.V.Unit.": vv_unit,
            "V.Venta": vv_venta,
            "Dscto.": dscto,
            "V.Venta Final": vv_final
        }

        for k in kms_cols:
            km_lbl = fmt_km(k)
            cant_k = float(it.get("km_cantidades", {}).get(k, 0.0))
            if cant_k > 0:
                val_k = round(cant_k * vv_unit * (1 - dscto / 100), 2)
                r_dict[km_lbl] = val_k
            else:
                r_dict[km_lbl] = ""

        rows.append(r_dict)

    km_totales = {k: 0.0 for k in kms_cols}
    if not rows:
        cols = ["Item", "Código", "Descripción", "Cant.", "V.V.Unit.", "V.Venta", "Dscto.", "V.Venta Final"] + [fmt_km(k) for k in kms_cols]
        return pd.DataFrame(columns=cols), km_totales

    df_base = pd.DataFrame(rows)

    for k in kms_cols:
        km_lbl = fmt_km(k)
        km_totales[k] = pd.to_numeric(df_base[km_lbl], errors="coerce").sum().round(2)

    row_tot = {col: "" for col in df_base.columns}
    row_tot["Item"] = ""
    row_tot["Código"] = ""
    row_tot["Descripción"] = "TOTAL"
    for k in kms_cols:
        km_lbl = fmt_km(k)
        row_tot[km_lbl] = km_totales[k]

    df_con_tot = pd.concat([df_base, pd.DataFrame([row_tot])], ignore_index=True)
    return df_con_tot, km_totales

tabla_repuestos, km_totales_rep = construir_tabla_materiales(st.session_state.items_repuestos, kms)
tabla_fluidos, km_totales_flu = construir_tabla_materiales(st.session_state.items_fluidos, kms)

# ==============================================================================
# 1. CÁLCULO DEL RESUMEN PRECIARIO GENERAL
# ==============================================================================

resultado = []
serv_horas = detalle["serv_horas_mo"]
terceros_items = detalle["terceros_items"]

for km in kms:
    if km == 1000:
        fila_km = {
            "KM": km,
            "Servicios": 0.0,
        }
        if incluir_terceros:
            fila_km["Servicios terceros"] = 0.0
        fila_km["Repuestos"] = 0.0
        fila_km["Fluidos"] = 0.0
        fila_km["Total"] = 0.0
        resultado.append(fila_km)
        continue

    # Mano de Obra
    horas = serv_horas.get(km, 0.0)
    total_serv = horas * precio_hh * (1 - descuento_mo / 100)

    # Terceros
    total_terc = 0.0
    if incluir_terceros:
        for t_item in terceros_items:
            total_terc += t_item["kms"].get(km, 0.0)

    # Repuestos y Fluidos
    total_rep = km_totales_rep.get(km, 0.0)
    total_flu = km_totales_flu.get(km, 0.0)

    total = total_serv + total_terc + total_rep + total_flu

    fila_km = {
        "KM": km,
        "Servicios": total_serv,
    }
    if incluir_terceros:
        fila_km["Servicios terceros"] = total_terc
    fila_km["Repuestos"] = total_rep
    fila_km["Fluidos"] = total_flu
    fila_km["Total"] = total

    resultado.append(fila_km)

df = pd.DataFrame(resultado)

# Tabla Resumen Formateada para visualización
df_display_preciario = df.copy()
df_display_preciario["KM"] = df_display_preciario["KM"].apply(fmt_km)

fila_total_df = {
    "KM": "TOTAL",
    "Servicios": df["Servicios"].sum(),
}
if incluir_terceros:
    fila_total_df["Servicios terceros"] = df["Servicios terceros"].sum()
fila_total_df["Repuestos"] = df["Repuestos"].sum()
fila_total_df["Fluidos"] = df["Fluidos"].sum()
fila_total_df["Total"] = df["Total"].sum()

df_display = pd.concat([df_display_preciario, pd.DataFrame([fila_total_df])], ignore_index=True)

st.subheader("📊 Preciario de Mantenimiento (Resumen General)")

fila_total_idx = df_display.index[-1]
def bold_df(row):
    return ["font-weight: bold; background-color: #F0F4F8"] * len(row) if row.name == fila_total_idx else [""] * len(row)

fmt_cols_display = {
    "Servicios": lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x,
    "Repuestos": lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x,
    "Fluidos": lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x,
    "Total": lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x,
}
if incluir_terceros:
    fmt_cols_display["Servicios terceros"] = lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x

st.dataframe(
    df_display.style.apply(bold_df, axis=1).format(fmt_cols_display),
    use_container_width=True
)

# Tarjetas de Totales
col_met1, col_met2, col_met3, col_met4 = st.columns(4)
col_met1.metric("Mano de Obra (sin IGV)", f"S/ {df['Servicios'].sum():,.2f}")
if incluir_terceros:
    col_met2.metric("Servicios Terceros", f"S/ {df['Servicios terceros'].sum():,.2f}")
    col_met3.metric("Repuestos (sin IGV)", f"S/ {df['Repuestos'].sum():,.2f}")
    col_met4.metric("Fluidos (sin IGV)", f"S/ {df['Fluidos'].sum():,.2f}")
else:
    col_met2.metric("Repuestos (sin IGV)", f"S/ {df['Repuestos'].sum():,.2f}")
    col_met3.metric("Fluidos (sin IGV)", f"S/ {df['Fluidos'].sum():,.2f}")
    col_met4.metric("Total sin IGV", f"S/ {df['Total'].sum():,.2f}")

col_tot1, col_tot2 = st.columns(2)
total_rango = df["Total"].sum()
total_con_igv = total_rango * 1.18
with col_tot1:
    st.metric("💰 Costo Total del Rango (S/ sin IGV)", f"S/ {total_rango:,.2f}")
with col_tot2:
    st.metric("🧾 Costo Total con IGV (18%)", f"S/ {total_con_igv:,.2f}")

# ==============================================================================
# 2. TABLA DETALLE DE MANO DE OBRA
# ==============================================================================

st.markdown("---")
st.subheader("🛠️ Detalle de Mano de Obra")

serv_row = {
    "Item": 1,
    "Código": "MO-01",
    "Descripción": "Mano de Obra de Mantenimiento Preventivo"
}
for km in kms:
    serv_row[fmt_km(km)] = serv_horas.get(km, 0.0)

tabla_serv = pd.DataFrame([serv_row])
tot_horas = [tabla_serv[fmt_km(k)].sum() for k in kms]
tabla_serv.loc[len(tabla_serv)] = ["", "", "TOTAL"] + [round(h, 2) for h in tot_horas]

tot_soles = [round(h * precio_hh * (1 - descuento_mo / 100), 2) for h in tot_horas]
tabla_serv.loc[len(tabla_serv)] = ["", "", "TOTAL S/"] + tot_soles

col_config_simple = {
    "Item": st.column_config.Column("Item", width="small"),
    "Código": st.column_config.Column("Código", width="small"),
    "Descripción": st.column_config.Column("Descripción", width="large"),
}
st.dataframe(tabla_serv, column_config=col_config_simple, use_container_width=True)

tiempo_total = sum(serv_horas.get(k, 0.0) for k in kms if k != 1000)
precio_mo_total = df["Servicios"].sum()
st.caption(f"⏱️ **Tiempo total:** {tiempo_total:.2f} horas | **Tarifa:** S/ {precio_hh:,.2f}/h | **Total Mano de Obra:** S/ {precio_mo_total:,.2f}")

# ==============================================================================
# 3. TABLA SERVICIOS TERCEROS
# ==============================================================================

tabla_terc = None
if incluir_terceros and terceros_items:
    st.markdown("---")
    st.subheader("🚙 Detalle de Servicios de Terceros")
    terc_rows = []
    for idx, t_item in enumerate(terceros_items, 1):
        t_row = {
            "Item": idx,
            "Código": t_item["codigo"],
            "Descripción": t_item["descripcion"]
        }
        for km in kms:
            v = t_item["kms"].get(km, 0.0)
            t_row[fmt_km(km)] = v if v > 0 else ""
        terc_rows.append(t_row)

    tabla_terc = pd.DataFrame(terc_rows)
    totales_terc = [
        pd.to_numeric(tabla_terc[fmt_km(k)], errors="coerce").sum().round(2)
        for k in kms
    ]
    tabla_terc.loc[len(tabla_terc)] = ["", "", "TOTAL"] + totales_terc
    st.dataframe(tabla_terc, column_config=col_config_simple, use_container_width=True)

# ==============================================================================
# 4. TABLA DETALLE DE REPUESTOS (CUADRO SEPARADO)
# ==============================================================================

st.markdown("---")
st.subheader("🔩 Detalle de Repuestos")

# Renderizar tabla editable / interactiva para Repuestos
st.caption("💡 *Puedes editar directamente **Cant.**, **V.V.Unit.** o **Dscto. %** en cada ítem de la tabla inferior para aplicar descuentos diferenciados.*")

rep_items_for_edit = tabla_repuestos.iloc[:-1].copy() if len(tabla_repuestos) > 1 else tabla_repuestos.copy()
km_cols_labels = [fmt_km(k) for k in kms]
disabled_cols_rep = [c for c in rep_items_for_edit.columns if c not in ["Cant.", "V.V.Unit.", "Dscto."]]

col_config_materiales = {
    "Item": st.column_config.NumberColumn("Item", width="small", format="%d"),
    "Código": st.column_config.TextColumn("Código", width="small"),
    "Descripción": st.column_config.TextColumn("Descripción", width="large"),
    "Cant.": st.column_config.NumberColumn("Cant.", width="small", format="%.2f"),
    "V.V.Unit.": st.column_config.NumberColumn("V.V.Unit.", width="small", format="%.2f"),
    "V.Venta": st.column_config.NumberColumn("V.Venta", width="small", format="%.2f"),
    "Dscto.": st.column_config.NumberColumn("Dscto. %", width="small", format="%.1f%%"),
    "V.Venta Final": st.column_config.NumberColumn("V.Venta Final", width="small", format="%.2f"),
}
for _k_col in km_cols_labels:
    col_config_materiales[_k_col] = st.column_config.Column(width="small")

edited_rep_df = st.data_editor(
    rep_items_for_edit,
    key="data_editor_repuestos",
    disabled=disabled_cols_rep,
    column_config=col_config_materiales,
    hide_index=True,
    use_container_width=True
)

# Detectar cambios inline en Repuestos
cambio_rep = False
for idx, it in enumerate(st.session_state.items_repuestos):
    if idx < len(edited_rep_df):
        try:
            n_cant = float(edited_rep_df.iloc[idx]["Cant."])
            n_vv = float(edited_rep_df.iloc[idx]["V.V.Unit."])
            n_dsc = float(edited_rep_df.iloc[idx]["Dscto."])
            if (abs(it["cantidad"] - n_cant) > 0.001 or
                abs(it["vv_unit"] - n_vv) > 0.001 or
                abs(it["dscto"] - n_dsc) > 0.001):
                it["cantidad"] = n_cant
                it["vv_unit"] = n_vv
                it["dscto"] = n_dsc
                cambio_rep = True
        except (ValueError, TypeError):
            pass

if cambio_rep:
    st.rerun()

# Fila total de Repuestos para referencia rápida
total_rep_rango = km_totales_rep
st.markdown(
    f"**Total Repuestos en el rango:** `S/ {df['Repuestos'].sum():,.2f}` | "
    f"**Total ítems:** `{len(st.session_state.items_repuestos)}`"
)

# Acciones de Agregar / Retirar Repuesto
col_ar1, col_ar2 = st.columns(2)

with col_ar1:
    with st.expander("➕ Agregar Repuesto (desde MAD o Personalizado)", expanded=False):
        modo_rep = st.radio("Origen del nuevo repuesto:", ["Buscar en Catálogo MAD", "Código Personalizado"], key="modo_add_rep")

        if modo_rep == "Buscar en Catálogo MAD":
            q_rep = st.text_input("Buscar material en MAD (código o nombre):", placeholder="Ej: 90915, pastilla, filtro...", key="txt_search_mad_rep")
            res_mad_rep = pmad.buscar_materiales_mad(df_mad, q_rep, limit=20) if (mad_disponible and q_rep) else []

            if res_mad_rep:
                dic_mad_rep = {r["label"]: r for r in res_mad_rep}
                sel_mad_r = st.selectbox("Materiales encontrados:", list(dic_mad_rep.keys()), key="sel_box_mad_rep")
                mat_sel_r = dic_mad_rep[sel_mad_r]

                c_rep_cod = mat_sel_r["codigo"]
                c_rep_desc = mat_sel_r["descripcion"]
                c_rep_cant = st.number_input("Cantidad:", value=1.0, min_value=0.1, step=1.0, key="cant_mad_rep")
                c_rep_vv = st.number_input("V.V.Unit. (VVP de MAD):", value=float(mat_sel_r["vv_unit"]), step=1.0, key="vv_mad_rep")
                c_rep_dsc = st.number_input("Dscto. % (DCTO de MAD):", value=float(mat_sel_r["dscto"]), min_value=0.0, max_value=100.0, step=1.0, key="dsc_mad_rep")
                es_valido_rep = True
            else:
                if q_rep and len(q_rep.strip()) >= 2:
                    st.info("No se encontraron repuestos con esa búsqueda.")
                es_valido_rep = False
        else:
            c_rep_cod = st.text_input("Código del repuesto:", placeholder="Ej: CUST-REP-01", key="cust_cod_r").strip().upper()
            c_rep_desc = st.text_input("Descripción del repuesto:", placeholder="Ej: Protector de cárter / Accesorio", key="cust_desc_r").strip()
            col_cr1, col_cr2, col_cr3 = st.columns(3)
            c_rep_cant = col_cr1.number_input("Cantidad:", value=1.0, min_value=0.1, step=1.0, key="cust_cant_r")
            c_rep_vv = col_cr2.number_input("V.V.Unit. (S/):", value=0.0, min_value=0.0, step=1.0, key="cust_vv_r")
            c_rep_dsc = col_cr3.number_input("Dscto. %:", value=0.0, min_value=0.0, max_value=100.0, step=1.0, key="cust_dsc_r")
            es_valido_rep = bool(c_rep_cod and c_rep_desc)

        if es_valido_rep:
            km_mode_r = st.radio("Aplicar este repuesto a:", ["Todos los KMs de la cotización", "KMs específicos"], key="km_mode_r")
            if km_mode_r == "KMs específicos":
                kms_elegidos_r = st.multiselect("Seleccionar KMs:", kms, default=kms, key="kms_elegidos_r")
            else:
                kms_elegidos_r = kms

            if st.button("➕ Confirmar y Agregar Repuesto", key="btn_confirm_add_rep"):
                km_cants = {k: c_rep_cant for k in kms_elegidos_r}
                st.session_state.items_repuestos.append({
                    "id": f"REP_NEW_{len(st.session_state.items_repuestos)+1}_{c_rep_cod}",
                    "tipo": "REPUESTO",
                    "codigo": c_rep_cod,
                    "descripcion": c_rep_desc,
                    "cantidad": float(c_rep_cant),
                    "vv_unit": float(c_rep_vv),
                    "dscto": float(c_rep_dsc),
                    "km_cantidades": km_cants,
                    "origen": "MAD" if modo_rep == "Buscar en Catálogo MAD" else "CUSTOM"
                })
                st.success(f"✅ Se agregó el repuesto `{c_rep_cod}` a la cotización.")
                st.rerun()

with col_ar2:
    with st.expander("🗑️ Retirar Repuesto de esta cotización", expanded=False):
        if st.session_state.items_repuestos:
            del_opts_rep = {f"#{idx} | {it['codigo']} — {it['descripcion']}": idx - 1 for idx, it in enumerate(st.session_state.items_repuestos, 1)}
            item_del_r = st.selectbox("Seleccionar repuesto a retirar:", list(del_opts_rep.keys()), key="sel_del_rep_box")
            if st.button("🗑️ Retirar Repuesto Seleccionado", key="btn_do_del_rep"):
                idx_del = del_opts_rep[item_del_r]
                borrado = st.session_state.items_repuestos.pop(idx_del)
                st.success(f"Se retiró el repuesto `{borrado['codigo']}`.")
                st.rerun()
        else:
            st.info("No hay repuestos en la cotización.")

# ==============================================================================
# 5. TABLA DETALLE DE FLUIDOS (CUADRO SEPARADO)
# ==============================================================================

st.markdown("---")
st.subheader("💧 Detalle de Fluidos")

st.caption("💡 *Puedes editar directamente **Cant.**, **V.V.Unit.** o **Dscto. %** en cada ítem de fluidos para aplicar descuentos diferenciados.*")

flu_items_for_edit = tabla_fluidos.iloc[:-1].copy() if len(tabla_fluidos) > 1 else tabla_fluidos.copy()
disabled_cols_flu = [c for c in flu_items_for_edit.columns if c not in ["Cant.", "V.V.Unit.", "Dscto."]]

edited_flu_df = st.data_editor(
    flu_items_for_edit,
    key="data_editor_fluidos",
    disabled=disabled_cols_flu,
    column_config=col_config_materiales,
    hide_index=True,
    use_container_width=True
)

# Detectar cambios inline en Fluidos
cambio_flu = False
for idx, it in enumerate(st.session_state.items_fluidos):
    if idx < len(edited_flu_df):
        try:
            n_cant = float(edited_flu_df.iloc[idx]["Cant."])
            n_vv = float(edited_flu_df.iloc[idx]["V.V.Unit."])
            n_dsc = float(edited_flu_df.iloc[idx]["Dscto."])
            if (abs(it["cantidad"] - n_cant) > 0.001 or
                abs(it["vv_unit"] - n_vv) > 0.001 or
                abs(it["dscto"] - n_dsc) > 0.001):
                it["cantidad"] = n_cant
                it["vv_unit"] = n_vv
                it["dscto"] = n_dsc
                cambio_flu = True
        except (ValueError, TypeError):
            pass

if cambio_flu:
    st.rerun()

st.markdown(
    f"**Total Fluidos en el rango:** `S/ {df['Fluidos'].sum():,.2f}` | "
    f"**Total ítems:** `{len(st.session_state.items_fluidos)}`"
)

# Acciones de Agregar / Retirar Fluido
col_af1, col_af2 = st.columns(2)

with col_af1:
    with st.expander("➕ Agregar Fluido (desde MAD o Personalizado)", expanded=False):
        modo_flu = st.radio("Origen del nuevo fluido:", ["Buscar en Catálogo MAD", "Código Personalizado"], key="modo_add_flu")

        if modo_flu == "Buscar en Catálogo MAD":
            q_flu = st.text_input("Buscar fluido en MAD (código o nombre):", placeholder="Ej: 08880, aceite, refrigerante, freno...", key="txt_search_mad_flu")
            res_mad_flu = pmad.buscar_materiales_mad(df_mad, q_flu, limit=20) if (mad_disponible and q_flu) else []

            if res_mad_flu:
                dic_mad_flu = {r["label"]: r for r in res_mad_flu}
                sel_mad_f = st.selectbox("Fluidos encontrados en MAD:", list(dic_mad_flu.keys()), key="sel_box_mad_flu")
                mat_sel_f = dic_mad_flu[sel_mad_f]

                c_flu_cod = mat_sel_f["codigo"]
                c_flu_desc = mat_sel_f["descripcion"]
                c_flu_cant = st.number_input("Cantidad:", value=1.0, min_value=0.1, step=1.0, key="cant_mad_flu")
                c_flu_vv = st.number_input("V.V.Unit. (VVP de MAD):", value=float(mat_sel_f["vv_unit"]), step=1.0, key="vv_mad_flu")
                c_flu_dsc = st.number_input("Dscto. % (DCTO de MAD):", value=float(mat_sel_f["dscto"]), min_value=0.0, max_value=100.0, step=1.0, key="dsc_mad_flu")
                es_valido_flu = True
            else:
                if q_flu and len(q_flu.strip()) >= 2:
                    st.info("No se encontraron fluidos con esa búsqueda.")
                es_valido_flu = False
        else:
            c_flu_cod = st.text_input("Código del fluido:", placeholder="Ej: CUST-FLU-01", key="cust_cod_f").strip().upper()
            c_flu_desc = st.text_input("Descripción del fluido:", placeholder="Ej: Refrigerante / Líquido especial", key="cust_desc_f").strip()
            col_cf1, col_cf2, col_cf3 = st.columns(3)
            c_flu_cant = col_cf1.number_input("Cantidad:", value=1.0, min_value=0.1, step=1.0, key="cust_cant_f")
            c_flu_vv = col_cf2.number_input("V.V.Unit. (S/):", value=0.0, min_value=0.0, step=1.0, key="cust_vv_f")
            c_flu_dsc = col_cf3.number_input("Dscto. %:", value=0.0, min_value=0.0, max_value=100.0, step=1.0, key="cust_dsc_f")
            es_valido_flu = bool(c_flu_cod and c_flu_desc)

        if es_valido_flu:
            km_mode_f = st.radio("Aplicar este fluido a:", ["Todos los KMs de la cotización", "KMs específicos"], key="km_mode_f")
            if km_mode_f == "KMs específicos":
                kms_elegidos_f = st.multiselect("Seleccionar KMs:", kms, default=kms, key="kms_elegidos_f")
            else:
                kms_elegidos_f = kms

            if st.button("➕ Confirmar y Agregar Fluido", key="btn_confirm_add_flu"):
                km_cants = {k: c_flu_cant for k in kms_elegidos_f}
                st.session_state.items_fluidos.append({
                    "id": f"FLU_NEW_{len(st.session_state.items_fluidos)+1}_{c_flu_cod}",
                    "tipo": "FLUIDO",
                    "codigo": c_flu_cod,
                    "descripcion": c_flu_desc,
                    "cantidad": float(c_flu_cant),
                    "vv_unit": float(c_flu_vv),
                    "dscto": float(c_flu_dsc),
                    "km_cantidades": km_cants,
                    "origen": "MAD" if modo_flu == "Buscar en Catálogo MAD" else "CUSTOM"
                })
                st.success(f"✅ Se agregó el fluido `{c_flu_cod}` a la cotización.")
                st.rerun()

with col_af2:
    with st.expander("🗑️ Retirar Fluido de esta cotización", expanded=False):
        if st.session_state.items_fluidos:
            del_opts_flu = {f"#{idx} | {it['codigo']} — {it['descripcion']}": idx - 1 for idx, it in enumerate(st.session_state.items_fluidos, 1)}
            item_del_f = st.selectbox("Seleccionar fluido a retirar:", list(del_opts_flu.keys()), key="sel_del_flu_box")
            if st.button("🗑️ Retirar Fluido Seleccionado", key="btn_do_del_flu"):
                idx_del = del_opts_flu[item_del_f]
                borrado = st.session_state.items_fluidos.pop(idx_del)
                st.success(f"Se retiró el fluido `{borrado['codigo']}`.")
                st.rerun()
        else:
            st.info("No hay fluidos en la cotización.")

# Botón general para restaurar catálogo original
st.markdown("---")
if st.button("🔄 Restaurar Repuestos y Fluidos originales del modelo (BD/MAD)", key="btn_reset_full_catalog"):
    inicializar_items_modelo()
    st.success("Lista de repuestos y fluidos restaurada al estado original de la base de datos y MAD.")
    st.rerun()

# ==============================================================================
# 6. OPCIONES DE EXPORTACIÓN Y DESCARGAS
# ==============================================================================

st.markdown("---")
st.subheader("📥 Opciones de Exportación")
col_op1, col_op2 = st.columns(2)
with col_op1:
    ocultar_codigos = st.checkbox("Ocultar códigos en el reporte", value=False)
with col_op2:
    ocultar_detalle_rep = st.checkbox("Ocultar detalle de precios unitarios en repuestos y fluidos", value=False)

def preparar_tabla_export(df_in, ocultar_cod, ocultar_det=False):
    t = df_in.copy()
    if ocultar_cod and "Código" in t.columns:
        t = t.drop(columns=["Código"])
    if ocultar_det:
        cols_borrar = [c for c in ["Cant.", "V.V.Unit.", "V.Venta", "Dscto."] if c in t.columns]
        if cols_borrar:
            t = t.drop(columns=cols_borrar)
    return t

tabla_serv_export = preparar_tabla_export(tabla_serv, ocultar_codigos)
tabla_terc_export = preparar_tabla_export(tabla_terc, ocultar_codigos) if tabla_terc is not None else None
tabla_rep_export = preparar_tabla_export(tabla_repuestos, ocultar_codigos, ocultar_detalle_rep)
tabla_flu_export = preparar_tabla_export(tabla_fluidos, ocultar_codigos, ocultar_detalle_rep)

def _hash_df(df_in):
    if df_in is None:
        return ""
    return hashlib.md5(pd.util.hash_pandas_object(df_in).values).hexdigest()

@st.cache_data(show_spinner=False)
def _cached_generar_excel(df_hash, tabla_serv_hash, tabla_rep_hash, tabla_flu_hash, tabla_terc_hash,
                           modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                           incluir_terceros):
    return gep.generar_excel_profesional(
        df=df,
        tabla_serv=tabla_serv_export,
        tabla_repuestos=tabla_rep_export,
        tabla_fluidos=tabla_flu_export,
        tabla_terc=tabla_terc_export if incluir_terceros else None,
        modelo_nombre=modelo_nombre,
        km_inicio=km_inicio,
        km_fin=km_fin,
        precio_hh=precio_hh,
        descuento_mo=descuento_mo,
        descuento_extra=0,
        incluir_terceros=incluir_terceros,
    )

@st.cache_data(show_spinner=False)
def _cached_generar_pdf_resumido(df_hash, tabla_serv_hash, tabla_rep_hash, tabla_flu_hash, tabla_terc_hash,
                                  modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                                  incluir_terceros):
    return gpp.generar_pdf_resumido(
        df=df,
        modelo_nombre=modelo_nombre,
        km_inicio=km_inicio,
        km_fin=km_fin,
        precio_hh=precio_hh,
        descuento_mo=descuento_mo,
        descuento_extra=0,
        incluir_terceros=incluir_terceros,
    )

@st.cache_data(show_spinner=False)
def _cached_generar_pdf_detallado(df_hash, tabla_serv_hash, tabla_rep_hash, tabla_flu_hash, tabla_terc_hash,
                                   modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                                   incluir_terceros, cols_fijas_serv, cols_fijas_rep, cols_fijas_flu):
    return gpp.generar_pdf_detallado(
        df=df,
        tabla_serv=tabla_serv_export,
        tabla_completa=tabla_rep_export,
        tabla_fluidos=tabla_flu_export,
        modelo_nombre=modelo_nombre,
        km_inicio=km_inicio,
        km_fin=km_fin,
        precio_hh=precio_hh,
        descuento_mo=descuento_mo,
        descuento_extra=0,
        incluir_terceros=incluir_terceros,
        tabla_terc=tabla_terc_export,
        cols_fijas_serv=cols_fijas_serv,
        cols_fijas_rep=cols_fijas_rep,
        cols_fijas_flu=cols_fijas_flu,
    )

col_btn1, col_btn2, col_btn3 = st.columns(3)

# 1. EXCEL
with col_btn1:
    if st.button("📥 Generar Preciario en Excel", key="gen_excel"):
        with st.spinner("Generando Excel con Repuestos y Fluidos separados..."):
            df_hash = _hash_df(df)
            t_serv_h = _hash_df(tabla_serv_export)
            t_rep_h = _hash_df(tabla_rep_export)
            t_flu_h = _hash_df(tabla_flu_export)
            t_terc_h = _hash_df(tabla_terc_export)
            st.session_state.excel_bytes = _cached_generar_excel(
                df_hash, t_serv_h, t_rep_h, t_flu_h, t_terc_h,
                modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                incluir_terceros
            )
    if "excel_bytes" in st.session_state and st.session_state.excel_bytes:
        st.download_button(
            label="⬇️ Descargar Archivo Excel",
            data=st.session_state.excel_bytes.getvalue(),
            file_name=f"Preciario_{modelo_info['familia']}_{modelo_info['codigo_modelo']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 2. PDF RESUMIDO
with col_btn2:
    if st.button("📄 Generar PDF Resumido", key="gen_pdf_resum"):
        with st.spinner("Generando PDF resumido..."):
            df_hash = _hash_df(df)
            t_serv_h = _hash_df(tabla_serv_export)
            t_rep_h = _hash_df(tabla_rep_export)
            t_flu_h = _hash_df(tabla_flu_export)
            t_terc_h = _hash_df(tabla_terc_export)
            st.session_state.pdf_resumido = _cached_generar_pdf_resumido(
                df_hash, t_serv_h, t_rep_h, t_flu_h, t_terc_h,
                modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                incluir_terceros
            )
    if "pdf_resumido" in st.session_state and st.session_state.pdf_resumido:
        st.download_button(
            label="⬇️ Descargar PDF Resumido",
            data=st.session_state.pdf_resumido.getvalue(),
            file_name=f"Resumen_{modelo_info['familia']}_{modelo_info['codigo_modelo']}.pdf",
            mime="application/pdf"
        )

# 3. PDF DETALLADO
cols_fijas_serv = 2 if ocultar_codigos else 3
cols_fijas_rep = 8
if ocultar_codigos:
    cols_fijas_rep -= 1
if ocultar_detalle_rep:
    cols_fijas_rep -= 4
cols_fijas_flu = cols_fijas_rep

with col_btn3:
    if st.button("📋 Generar PDF Detallado", key="gen_pdf_det"):
        with st.spinner("Generando PDF detallado con Repuestos y Fluidos..."):
            df_hash = _hash_df(df)
            t_serv_h = _hash_df(tabla_serv_export)
            t_rep_h = _hash_df(tabla_rep_export)
            t_flu_h = _hash_df(tabla_flu_export)
            t_terc_h = _hash_df(tabla_terc_export)
            st.session_state.pdf_detallado = _cached_generar_pdf_detallado(
                df_hash, t_serv_h, t_rep_h, t_flu_h, t_terc_h,
                modelo_nombre, km_inicio, km_fin, precio_hh, descuento_mo,
                incluir_terceros, cols_fijas_serv, cols_fijas_rep, cols_fijas_flu
            )
    if "pdf_detallado" in st.session_state and st.session_state.pdf_detallado:
        st.download_button(
            label="⬇️ Descargar PDF Detallado",
            data=st.session_state.pdf_detallado.getvalue(),
            file_name=f"Detallado_{modelo_info['familia']}_{modelo_info['codigo_modelo']}.pdf",
            mime="application/pdf"
        )
