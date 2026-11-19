from io import BytesIO
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import date
import os
import pandas as pd

# ─── Paleta ───────────────────────────────────────────────────────────
AZUL_OSCURO = colors.HexColor("#1B3A6B")
AZUL_MEDIO  = colors.HexColor("#2E5FAC")
AZUL_CLARO  = colors.HexColor("#D6E4F7")
ROJO_ACC    = colors.HexColor("#C00000")
VERDE_ACC   = colors.HexColor("#1A6B3A")
GRIS_CLARO  = colors.HexColor("#F5F7FA")
BLANCO      = colors.white
NEGRO       = colors.HexColor("#1A1A2E")

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
ANCHO_A3 = A3[1] - 2 * MARGIN  # landscape A3 útil


# ─── Estilos ──────────────────────────────────────────────────────────
def _estilos():
    return {
        "titulo": ParagraphStyle(
            "titulo", fontName="Helvetica-Bold", fontSize=20,
            textColor=BLANCO, leading=24, alignment=TA_LEFT
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo", fontName="Helvetica", fontSize=12,
            textColor=colors.HexColor("#BDD7EE"), leading=16, alignment=TA_LEFT
        ),
        "fecha_der": ParagraphStyle(
            "fecha_der", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#9DC3E6"), alignment=TA_RIGHT
        ),
        "seccion": ParagraphStyle(
            "seccion", fontName="Helvetica-Bold", fontSize=11,
            textColor=BLANCO, leading=14, alignment=TA_LEFT
        ),
        "param_label": ParagraphStyle(
            "param_label", fontName="Helvetica", fontSize=9,
            textColor=NEGRO, alignment=TA_LEFT
        ),
        "param_val": ParagraphStyle(
            "param_val", fontName="Helvetica-Bold", fontSize=9,
            textColor=AZUL_MEDIO, alignment=TA_LEFT
        ),
        "nota": ParagraphStyle(
            "nota", fontName="Helvetica-Oblique", fontSize=8,
            textColor=colors.HexColor("#666666"), alignment=TA_LEFT
        ),
    }


# ─── Cabecera ─────────────────────────────────────────────────────────
def _cabecera(story, modelo_nombre, km_inicio, km_fin, tipo, estilos, ancho):
    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_M.png")

    try:
        logo = Image(LOGO_PATH, width=2*cm, height=1.2*cm)
    except Exception:
        logo = Paragraph("", estilos["fecha_der"])

    t1 = Table([[
        Paragraph("PRECIARIO DE MANTENIMIENTO", estilos["titulo"]),
        Paragraph(f"Rango: {km_inicio:,} – {km_fin:,} km | {tipo}", estilos["fecha_der"]),
        logo,
    ]], colWidths=[ancho * 0.55, ancho * 0.30, ancho * 0.15])
    t1.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), AZUL_OSCURO),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
        ("ALIGN",         (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(t1)

    t2 = Table([[
        Paragraph(f"Modelo: {modelo_nombre}", estilos["subtitulo"]),
        Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", estilos["fecha_der"]),
        Paragraph("", estilos["fecha_der"]),
    ]], colWidths=[ancho * 0.55, ancho * 0.30, ancho * 0.15])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), AZUL_OSCURO),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(t2)
    story.append(HRFlowable(width="100%", thickness=4, color=ROJO_ACC, spaceAfter=10))
    
# ─── Bloque de parámetros ─────────────────────────────────────────────
def _bloque_parametros(story, modelo_nombre, km_inicio, km_fin,
                        precio_hh, descuento_mo, descuento_extra, estilos, ancho):
    params = [
        ("Modelo",             modelo_nombre),
        ("Precio Hora Hombre", f"S/ {precio_hh:,.2f}"),
        ("KM inicial",         f"{km_inicio:,} km"),
        ("KM final",           f"{km_fin:,} km"),
        # ("Descuento MO",       f"{descuento_mo}%"),
        # ("Descuento Rep.",     f"{descuento_extra}%"),
    ]
    mid  = (len(params) + 1) // 2
    col1 = params[:mid]
    col2 = params[mid:]
    data = []
    for i in range(mid):
        lbl1, val1 = col1[i]
        row = [Paragraph(lbl1, estilos["param_label"]),
               Paragraph(val1, estilos["param_val"])]
        if i < len(col2):
            lbl2, val2 = col2[i]
            row += [Paragraph(lbl2, estilos["param_label"]),
                    Paragraph(val2, estilos["param_val"])]
        else:
            row += ["", ""]
        data.append(row)

    t = Table(data, colWidths=[ancho / 4] * 4)
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, GRIS_CLARO]),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("GRID",           (0, 0), (-1, -1), 0.3, colors.HexColor("#BFCDE0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))


# ─── Título de sección ────────────────────────────────────────────────
def _titulo_seccion(story, texto, estilos, ancho):
    t = Table([[Paragraph(texto, estilos["seccion"])]], colWidths=[ancho])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), AZUL_MEDIO),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))


# ─── Tabla genérica ───────────────────────────────────────────────────
def _tabla_df(story, df, col_widths, fmt_cols=None, font_size=8):
    fmt_cols = fmt_cols or set()

    def _fmt(val, col_name):
        if pd.isna(val) or val == "":
            return ""
        if str(val) == "INCL.":          # ← agregar
            return "INCL."
        
        val_str = str(val).strip()
        if val_str.startswith("0") or any(c.isalpha() for c in val_str):
            return val_str
        
        if col_name in fmt_cols:
            try:
                return f"{float(val):,.2f}"
            except Exception:
                return str(val)
        try:
            f = float(val)
            if str(val).startswith("0"):
                return str(val)
            return str(int(f)) if f == int(f) else f"{f:,.2f}"
        except Exception:
            return str(val)

    headers = [Paragraph(str(c), ParagraphStyle(
        "h", fontName="Helvetica-Bold", fontSize=font_size,
        textColor=BLANCO, alignment=TA_CENTER, leading=font_size + 2
    )) for c in df.columns]

    data   = [headers]
    n_rows = len(df)

    for idx, (_, row) in enumerate(df.iterrows()):
        vals = [str(v) for v in row.values]
        is_total       = "TOTAL" in [v.upper() for v in vals] and "TOTAL S/" not in vals
        is_total_soles = "TOTAL S/" in vals
        is_special     = is_total or is_total_soles
        fila = []
        for col_name, val in row.items():
            txt = _fmt(val, col_name)
            if is_special:
                st = ParagraphStyle("t", fontName="Helvetica-Bold",
                                    fontSize=font_size, textColor=BLANCO,
                                    alignment=TA_CENTER, leading=font_size + 2)
            elif txt == "INCL.":
                st = ParagraphStyle("incl", fontName="Helvetica-Oblique",
                                    fontSize=font_size, textColor=AZUL_MEDIO,
                                    alignment=TA_CENTER, leading=font_size + 2)
            else:
                col_name_str = str(col_name).strip()
                col_lower = col_name_str.lower()
                if col_lower in ("descripción", "descripcion"):
                    align = TA_LEFT
                elif (col_lower in ["item", "código", "codigo", "cant.", "cant", "dscto.", "dscto",
                                    "v.v.unit.", "v.venta", "v.venta final"]
                      or col_name_str in fmt_cols
                      or col_name_str.endswith("K")
                      or col_name_str == "1K"
                      or (col_name_str.isdigit() and int(col_name_str) >= 1000)):
                    align = TA_CENTER
                else:
                    try:
                        float(str(val).replace(",", ""))
                        align = TA_CENTER
                    except (ValueError, TypeError):
                        align = TA_LEFT
                st = ParagraphStyle("d", fontName="Helvetica",
                                    fontSize=font_size, textColor=NEGRO,
                                    alignment=align, leading=font_size + 2)
            fila.append(Paragraph(txt, st))
        data.append(fila)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Encontrar índices de filas especiales
    idx_total    = None
    idx_total_s  = None
    for i, (_, row) in enumerate(df.iterrows()):
        vals = [str(v) for v in row.values]
        if "TOTAL S/" in vals:
            idx_total_s = i + 1  # +1 por header
        elif "TOTAL" in [v.upper() for v in vals]:
            idx_total = i + 1

    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("GRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#BFCDE0")),
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, n_rows + 1):
        if i == idx_total:
            cmds.append(("BACKGROUND", (0, i), (-1, i), AZUL_OSCURO))
            cmds.append(("TEXTCOLOR",  (0, i), (-1, i), BLANCO))
        elif i == idx_total_s:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROJO_ACC))
            cmds.append(("TEXTCOLOR",  (0, i), (-1, i), BLANCO))
        else:
            cmds.append(("BACKGROUND", (0, i), (-1, i),
                         AZUL_CLARO if i % 2 == 0 else BLANCO))
            
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1, 14))


# ─── Separar columnas fijas y KMs dinámicamente ───────────────────────
def _separar_fijas_y_km(df):
    cols = list(df.columns)
    idx_km = None
    for i, c in enumerate(cols):
        c_str = str(c).strip().upper()
        if (c_str.endswith("K") and (c_str[:-1].isdigit() or c_str == "1K")) or c_str in ("1000", "1K") or (c_str.isdigit() and int(c_str) >= 1000):
            idx_km = i
            break
    if idx_km is None:
        return cols, []
    return cols[:idx_km], cols[idx_km:]


def _calcular_anchos_fijas(cols_fijas):
    # Anchos milimétricamente ajustados para reporte ejecutivo A3
    anchos_base = {
        "item": 0.7 * cm,
        "código": 2.3 * cm,
        "codigo": 2.3 * cm,
        "cant.": 0.9 * cm,
        "cant": 0.9 * cm,
        "v.v.unit.": 1.5 * cm,
        "v.venta": 1.5 * cm,
        "dscto.": 1.0 * cm,
        "dscto": 1.0 * cm,
        "v.venta final": 1.7 * cm,
    }

    cols_lower = [str(c).strip().lower() for c in cols_fijas]
    es_materiales = any(k in cols_lower for k in ["v.venta final", "v.v.unit.", "cant.", "dscto."])

    if es_materiales:
        # Base amplia para descripción de repuestos o fluidos
        w_desc = 8.3 * cm
        if "código" not in cols_lower and "codigo" not in cols_lower:
            w_desc += 2.3 * cm
        if "cant." not in cols_lower and "cant" not in cols_lower:
            w_desc += 4.0 * cm
    else:
        # Mano de Obra o Terceros (pocas columnas fijas: Item, Código, Descripción)
        w_desc = 9.0 * cm
        if "código" not in cols_lower and "codigo" not in cols_lower:
            w_desc += 2.3 * cm

    anchos = []
    for c in cols_fijas:
        cl = str(c).strip().lower()
        if cl in ("descripción", "descripcion"):
            anchos.append(w_desc)
        elif cl in anchos_base:
            anchos.append(anchos_base[cl])
        else:
            anchos.append(1.5 * cm)

    return anchos


# ─── Tabla por grupos de KMs (sin duplicados y con anchos proporcionales) ─
def _tabla_por_grupos(story, df, col_widths_fijas=None, cols_fijas=None,
                       fmt_cols=None, font_size=7, grupo=22):
    fmt_cols = fmt_cols or set()
    cols_fijas_detected, cols_km_detected = _separar_fijas_y_km(df)

    cols_fijas_names = cols_fijas_detected
    cols_km_names = cols_km_detected

    col_widths_fijas = _calcular_anchos_fijas(cols_fijas_names)
    ancho_fijo = sum(col_widths_fijas)
    ancho_km_disp = ANCHO_A3 - ancho_fijo

    n_kms = len(cols_km_names)
    MAX_KMS = max(grupo, 22)

    if n_kms <= MAX_KMS or n_kms == 0:
        # Entra perfectamente en una sola tabla sin dividir (caso habitual hasta 100K)
        w_km_col = ancho_km_disp / max(n_kms, 1)
        col_widths = col_widths_fijas + [w_km_col] * n_kms
        df_sub = df[cols_fijas_names + cols_km_names].copy()
        _tabla_df(story, df_sub, col_widths, fmt_cols=fmt_cols, font_size=font_size)
    else:
        # Dividir equitativamente en grupos sin dejar 1 sola columna suelta
        n_grupos = (n_kms + MAX_KMS - 1) // MAX_KMS
        tam_grupo = (n_kms + n_grupos - 1) // n_grupos

        for g_idx in range(n_grupos):
            start = g_idx * tam_grupo
            end = min(start + tam_grupo, n_kms)
            grupo_cols = cols_km_names[start:end]
            if not grupo_cols:
                continue

            w_km_col = ancho_km_disp / max(len(grupo_cols), 1)
            col_widths = col_widths_fijas + [w_km_col] * len(grupo_cols)
            df_sub = df[cols_fijas_names + grupo_cols].copy()
            _tabla_df(story, df_sub, col_widths, fmt_cols=fmt_cols, font_size=font_size)


# ─── PDF RESUMIDO (vertical) ──────────────────────────────────────────
def generar_pdf_resumido(df, modelo_nombre, km_inicio, km_fin,
                          precio_hh, descuento_mo, descuento_extra,
                          incluir_terceros):
    buffer  = BytesIO()
    ancho   = PAGE_W - 2 * MARGIN
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN
    )
    estilos = _estilos()
    story   = []

    _cabecera(story, modelo_nombre, km_inicio, km_fin, "Resumen Ejecutivo", estilos, ancho)
    _bloque_parametros(story, modelo_nombre, km_inicio, km_fin,
                       precio_hh, descuento_mo, descuento_extra, estilos, ancho)

    _titulo_seccion(story, "Resumen de Costos por Sección", estilos, ancho)

    total_mo   = df["Servicios"].sum() if "Servicios" in df.columns else 0.0
    total_terc = df["Servicios terceros"].sum() if ("Servicios terceros" in df.columns and incluir_terceros) else 0.0
    total_rep  = df["Repuestos"].sum() if "Repuestos" in df.columns else 0.0
    total_flu  = df["Fluidos"].sum() if "Fluidos" in df.columns else 0.0
    total_gral = df["Total"].sum() if "Total" in df.columns else 0.0

    secciones = [("Mano de Obra", total_mo), ("Repuestos", total_rep)]
    if "Fluidos" in df.columns:
        secciones.append(("Fluidos", total_flu))
    if incluir_terceros and total_terc > 0:
        secciones.insert(1, ("Servicios de Terceros", total_terc))
    secciones.append(("TOTAL GENERAL", total_gral))

    res_data = [[
        Paragraph("Sección", ParagraphStyle("h", fontName="Helvetica-Bold",
                  fontSize=9, textColor=BLANCO, alignment=TA_LEFT)),
        Paragraph("Monto Total (S/)", ParagraphStyle("h", fontName="Helvetica-Bold",
                  fontSize=9, textColor=BLANCO, alignment=TA_RIGHT)),
    ]]
    for i, (sec, monto) in enumerate(secciones):
        is_t = sec == "TOTAL GENERAL"
        s_s  = ParagraphStyle("s", fontName="Helvetica-Bold" if is_t else "Helvetica",
                              fontSize=9, textColor=BLANCO if is_t else NEGRO, alignment=TA_LEFT)
        s_m  = ParagraphStyle("m", fontName="Helvetica-Bold" if is_t else "Helvetica",
                              fontSize=9, textColor=BLANCO if is_t else NEGRO, alignment=TA_RIGHT)
        res_data.append([Paragraph(sec, s_s), Paragraph(f"S/ {monto:,.2f}", s_m)])

    res_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), AZUL_OSCURO),
        ("BACKGROUND",    (0, len(secciones)), (-1, len(secciones)), ROJO_ACC),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#BFCDE0")),
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
    ]
    for i in range(1, len(secciones)):
        res_cmds.append(("BACKGROUND", (0, i), (-1, i),
                         AZUL_CLARO if i % 2 == 0 else BLANCO))

    res_t = Table(res_data, colWidths=[ancho * 0.65, ancho * 0.35])
    res_t.setStyle(TableStyle(res_cmds))
    story.append(res_t)
    story.append(Spacer(1, 14))

    _titulo_seccion(story, "Costos por Kilometraje", estilos, ancho)

    cols_show = ["KM", "Servicios"]
    if incluir_terceros and "Servicios terceros" in df.columns and total_terc > 0:
        cols_show.append("Servicios terceros")
    if "Repuestos" in df.columns:
        cols_show.append("Repuestos")
    if "Fluidos" in df.columns:
        cols_show.append("Fluidos")
    cols_show.append("Total")

    df_res = df[cols_show].copy()
    fila_t = {c: df_res[c].sum() if c != "KM" else "TOTAL" for c in cols_show}
    df_res = pd.concat([df_res, pd.DataFrame([fila_t])], ignore_index=True)
    df_res["KM"] = df_res["KM"].apply(
        lambda x: f"{int(x) // 1000}K" if str(x).isdigit() else ("1K" if str(x) == "1000" else str(x))
    )

    n_cols  = len(cols_show)
    w_km    = ancho * 0.12
    w_resto = (ancho - w_km) / (n_cols - 1)
    _tabla_df(story, df_res, [w_km] + [w_resto] * (n_cols - 1),
              fmt_cols=set(cols_show) - {"KM"})

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─── PDF DETALLADO (landscape A3) ────────────────────────────────────
def generar_pdf_detallado(df, tabla_serv, tabla_completa,
                           modelo_nombre, km_inicio, km_fin,
                           precio_hh, descuento_mo, descuento_extra=0,
                           incluir_terceros=True, tabla_terc=None,
                           tabla_fluidos=None,
                           cols_fijas_serv=3, cols_fijas_rep=7, cols_fijas_flu=7):
    buffer = BytesIO()
    ancho  = ANCHO_A3
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A3),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN
    )
    estilos = _estilos()
    story   = []

    _cabecera(story, modelo_nombre, km_inicio, km_fin, "Reporte Detallado", estilos, ancho)
    _bloque_parametros(story, modelo_nombre, km_inicio, km_fin,
                       precio_hh, descuento_mo, descuento_extra, estilos, ancho)

    # ── 1. Mano de Obra ───────────────────────────────────────────────
    _titulo_seccion(story, "1. Mano de Obra — Horas Estándar por KM", estilos, ancho)
    cols_fijas_s, cols_km_s = _separar_fijas_y_km(tabla_serv)
    km_cols_s = [c for c in cols_km_s
                 if pd.to_numeric(tabla_serv[c], errors="coerce").sum() > 0
                 or tabla_serv[c].astype(str).str.contains("INCL.").any()
                 or str(c) == "1K"]
    tabla_serv_pdf = tabla_serv[cols_fijas_s + km_cols_s]
    _tabla_por_grupos(story, tabla_serv_pdf, font_size=7, grupo=22)

    # Notas de servicios agrupados
    NOTAS_SERVICIOS = {
        "A101": "[1] Incluye: Encendido de motor, Revisión de niveles, Presión de llantas (5), Revisión de luces",
        "A102": "[2] Incluye: Encendido de motor, Revisión de niveles, Presión de llantas (5), Revisión de luces",
        "A103": "[3] Incluye: Encendido de motor, Revisión de niveles, Regulación de frenos, Presión de llantas (5), Revisión de luces",
    }
    codigos_en_tabla = tabla_serv.iloc[:, 1].tolist()
    notas_aplicables = [texto for cod, texto in NOTAS_SERVICIOS.items()
                        if cod in codigos_en_tabla]
    if notas_aplicables:
        for nota_texto in notas_aplicables:
            story.append(Paragraph(nota_texto, ParagraphStyle(
                "nota_serv", fontName="Helvetica-Oblique", fontSize=7,
                textColor=colors.HexColor("#444444"),
                leading=10, alignment=TA_LEFT, leftIndent=4
            )))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 8))

    # ── 2. Terceros ───────────────────────────────────────────────────
    sec_num = 2
    if incluir_terceros and tabla_terc is not None:
        _titulo_seccion(story, f"{sec_num}. Servicios de Terceros (S/) por KM", estilos, ancho)
        sec_num += 1
        cols_fijas_t, cols_km_t = _separar_fijas_y_km(tabla_terc)
        km_cols_t = [c for c in cols_km_t
                     if pd.to_numeric(tabla_terc[c], errors="coerce").sum() > 0
                     or tabla_terc[c].astype(str).str.contains("INCL.").any()
                     or str(c) == "1K"]
        tabla_terc_pdf = tabla_terc[cols_fijas_t + km_cols_t]
        _tabla_por_grupos(story, tabla_terc_pdf,
                          fmt_cols=set(km_cols_t), font_size=7, grupo=22)

    # ── 3. Repuestos ──────────────────────────────────────────────────
    _titulo_seccion(story, f"{sec_num}. Repuestos — Detalle y Precios por KM", estilos, ancho)
    sec_num += 1

    cols_fijas_r, cols_km_r = _separar_fijas_y_km(tabla_completa)
    km_cols_r = [c for c in cols_km_r
                 if tabla_completa[c].replace("", None).notna().any()
                 or str(c) == "1K"]
    tabla_completa_pdf = tabla_completa[cols_fijas_r + km_cols_r]
    fmt_rep = {"V.V.Unit.", "V.Venta", "V.Venta Final"} | set(km_cols_r)
    _tabla_por_grupos(story, tabla_completa_pdf,
                      fmt_cols=fmt_rep, font_size=7, grupo=22)

    # ── 4. Fluidos ────────────────────────────────────────────────────
    if tabla_fluidos is not None and not tabla_fluidos.empty:
        _titulo_seccion(story, f"{sec_num}. Fluidos — Detalle y Precios por KM", estilos, ancho)
        sec_num += 1
        cols_fijas_f, cols_km_f = _separar_fijas_y_km(tabla_fluidos)
        km_cols_f = [c for c in cols_km_f
                     if tabla_fluidos[c].replace("", None).notna().any()
                     or str(c) == "1K"]
        tabla_fluidos_pdf = tabla_fluidos[cols_fijas_f + km_cols_f]
        fmt_flu = {"V.V.Unit.", "V.Venta", "V.Venta Final"} | set(km_cols_f)
        _tabla_por_grupos(story, tabla_fluidos_pdf,
                          fmt_cols=fmt_flu, font_size=7, grupo=22)

    # ── Resumen por KM con IGV ────────────────────────────────────────
    _titulo_seccion(story, "Resumen de Costos por Kilometraje", estilos, ancho)

    cols_km = ["KM", "Servicios"]
    if incluir_terceros and "Servicios terceros" in df.columns:
        cols_km.append("Servicios terceros")
    if "Repuestos" in df.columns:
        cols_km.append("Repuestos")
    if "Fluidos" in df.columns:
        cols_km.append("Fluidos")
    cols_km.append("Total")

    df_res = df[cols_km].copy()
    df_res["Sin IGV"]       = df_res["Total"].round(2)
    df_res["Con IGV (18%)"] = (df_res["Total"] * 1.18).round(2)
    df_res["KM"] = df_res["KM"].apply(lambda x: f"{int(x) // 1000}K" if str(x).isdigit() else str(x))
    df_res = df_res[(df_res["Total"].fillna(0) > 0) | (df_res["KM"] == "1K")]

    df_t = df_res.set_index("KM").T
    df_t.index.name = "Concepto"
    df_t = df_t.reset_index()

    km_cols_all = list(df_t.columns[1:])
    GRUPO       = 22
    ROW_COLORS  = {
        "Sin IGV":       ROJO_ACC,
        "Con IGV (18%)": NEGRO,
    }

    for g_start in range(0, len(km_cols_all), GRUPO):
        grupo_cols = km_cols_all[g_start:g_start + GRUPO]
        df_grupo   = df_t[["Concepto"] + grupo_cols].copy()

        if g_start + GRUPO >= len(km_cols_all):
            df_grupo["TOTAL"] = df_t.iloc[:, 1:].apply(
                lambda row: pd.to_numeric(row, errors="coerce").sum(), axis=1
            ).round(2)

        n_cols     = len(df_grupo.columns)
        w_concepto = ancho * 0.10
        w_km_col   = (ancho - w_concepto) / max(n_cols - 1, 1)
        fmt_cols_t = set(df_grupo.columns) - {"Concepto"}
        fs         = 7

        def _fmt_val(val, col_name, _fmt_cols=fmt_cols_t):
            if pd.isna(val) or val == "":
                return ""
            if col_name in _fmt_cols:
                try:
                    return f"{float(val):,.2f}"
                except Exception:
                    return str(val)
            return str(val)

        headers = [Paragraph(str(c), ParagraphStyle(
            "h", fontName="Helvetica-Bold", fontSize=fs,
            textColor=BLANCO, alignment=TA_CENTER, leading=fs + 2
        )) for c in df_grupo.columns]

        data_t   = [headers]
        n_rows_t = len(df_grupo)

        for idx, (_, row) in enumerate(df_grupo.iterrows()):
            concepto  = str(row["Concepto"])
            row_color = ROW_COLORS.get(concepto, None)
            txt_color = BLANCO if row_color else NEGRO
            fila = []
            for col_name, val in row.items():
                txt   = _fmt_val(val, col_name)
                align = TA_CENTER if col_name in fmt_cols_t else TA_LEFT
                st    = ParagraphStyle("d",
                                       fontName="Helvetica-Bold" if row_color else "Helvetica",
                                       fontSize=fs, textColor=txt_color,
                                       alignment=align, leading=fs + 2)
                fila.append(Paragraph(txt, st))
            data_t.append(fila)

        t_res = Table(data_t,
                      colWidths=[w_concepto] + [w_km_col] * (n_cols - 1),
                      repeatRows=1)
        cmds_t = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#BFCDE0")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i in range(1, n_rows_t + 1):
            concepto  = df_grupo.iloc[i - 1]["Concepto"]
            row_color = ROW_COLORS.get(str(concepto), AZUL_CLARO if i % 2 == 0 else BLANCO)
            cmds_t.append(("BACKGROUND", (0, i), (-1, i), row_color))

        t_res.setStyle(TableStyle(cmds_t))
        story.append(t_res)
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer
