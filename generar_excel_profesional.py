from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter
import pandas as pd
from datetime import date


# ─── Paleta de colores ────────────────────────────────────────────────
AZUL_OSCURO   = "1B3A6B"
AZUL_MEDIO    = "2E5FAC"
AZUL_CLARO    = "D6E4F7"
GRIS_CLARO    = "F5F7FA"
GRIS_MEDIO    = "E2E8F0"
BLANCO        = "FFFFFF"
ROJO_ACC      = "C00000"
TEXTO_BLANCO  = "FFFFFF"
TEXTO_OSCURO  = "1A1A2E"


def _border(style="thin"):
    s = Side(style=style, color="BFCDE0")
    return Border(left=s, right=s, top=s, bottom=s)


def _header_style(cell, bg=AZUL_OSCURO, fg=TEXTO_BLANCO, size=11, bold=True, center=True):
    cell.font = Font(name="Arial", bold=bold, color=fg, size=size)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center" if center else "left",
                               vertical="center", wrap_text=True)
    cell.border = _border()


def _total_style(cell, center=True):
    cell.font = Font(name="Arial", bold=True, color=TEXTO_BLANCO, size=10)
    cell.fill = PatternFill("solid", fgColor=ROJO_ACC)
    cell.alignment = Alignment(horizontal="center" if center else "left", vertical="center")
    cell.border = _border()


def _data_style(cell, alt=False, center=False):
    cell.font = Font(name="Arial", size=10, color=TEXTO_OSCURO)
    cell.fill = PatternFill("solid", fgColor=AZUL_CLARO if alt else BLANCO)
    cell.alignment = Alignment(horizontal="center" if center else "left", vertical="center")
    cell.border = _border()


def _currency(cell):
    cell.number_format = '#,##0.00'


def _set_col_widths(ws, widths: dict):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


# ─── PORTADA ──────────────────────────────────────────────────────────
def _hoja_portada(wb, modelo_nombre, km_inicio, km_fin, precio_hh,
                  descuento_mo, descuento_extra,
                  total_mo, total_terc, total_rep, total_flu, incluir_terceros):
    ws = wb.active
    ws.title = "Portada"
    ws.sheet_view.showGridLines = False

    # Cabecera azul oscuro filas 1-8
    for row in range(1, 9):
        for col in range(1, 9):
            ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=AZUL_OSCURO)

    ws.merge_cells("B2:H3")
    t = ws["B2"]
    t.value = "PRECIARIO DE MANTENIMIENTO"
    t.font = Font(name="Arial", bold=True, size=22, color=TEXTO_BLANCO)
    t.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells("B4:H5")
    s = ws["B4"]
    s.value = f"Modelo: {modelo_nombre}"
    s.font = Font(name="Arial", size=14, color="BDD7EE")
    s.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells("B6:H7")
    d = ws["B6"]
    d.value = f"Rango: {km_inicio:,} – {km_fin:,} km  |  Fecha: {date.today().strftime('%d/%m/%Y')}"
    d.font = Font(name="Arial", size=11, color="9DC3E6")
    d.alignment = Alignment(horizontal="left", vertical="center")

    # Línea separadora roja
    for col in range(1, 9):
        ws.cell(row=8, column=col).fill = PatternFill("solid", fgColor=ROJO_ACC)
    ws.row_dimensions[8].height = 4

    for r in [1, 2, 3, 4, 5, 6, 7]:
        ws.row_dimensions[r].height = 24
    ws.row_dimensions[2].height = 34

    # ── Bloque parámetros ──────────────────────────────────────────
    params = [
        ("Parámetros del Preciario",    None,                    True),
        ("",                            None,                    False),
        ("Modelo seleccionado",         modelo_nombre,           False),
        ("KM inicial",                  f"{km_inicio:,} km",     False),
        ("KM final",                    f"{km_fin:,} km",        False),
        ("Precio Hora Hombre",          f"S/ {precio_hh:,.2f}",  False),
        ("Descuento Mano de Obra",      f"{descuento_mo}%",      False),
    ]

    for i, (label, val, is_title) in enumerate(params, start=10):
        for col in range(2, 8):
            ws.cell(row=i, column=col).fill = PatternFill("solid", fgColor=GRIS_CLARO)
        cl = ws.cell(row=i, column=2, value=label)
        cv = ws.cell(row=i, column=5, value=val)
        if is_title:
            cl.font = Font(name="Arial", bold=True, size=12, color=AZUL_OSCURO)
        else:
            cl.font = Font(name="Arial", size=10, color=TEXTO_OSCURO)
            cv.font = Font(name="Arial", bold=True, size=10, color=AZUL_MEDIO)
        cl.alignment = Alignment(horizontal="left", vertical="center")
        cv.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[i].height = 20

    # ── Bloque resumen en soles ────────────────────────────────────
    resumen_start = 10 + len(params) + 2   # 2 filas de separación

    # Título resumen
    for col in range(2, 8):
        ws.cell(row=resumen_start, column=col).fill = PatternFill("solid", fgColor=AZUL_OSCURO)
    tit = ws.cell(row=resumen_start, column=2, value="Resumen de Costos (S/)")
    tit.font = Font(name="Arial", bold=True, size=12, color=TEXTO_BLANCO)
    tit.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[resumen_start].height = 22

    # Encabezados columnas resumen
    r_enc = resumen_start + 1
    for col in range(2, 8):
        ws.cell(row=r_enc, column=col).fill = PatternFill("solid", fgColor=AZUL_MEDIO)
    enc_sec  = ws.cell(row=r_enc, column=2, value="Sección")
    enc_mto  = ws.cell(row=r_enc, column=6, value="Monto Total (S/)")
    for c in [enc_sec, enc_mto]:
        c.font      = Font(name="Arial", bold=True, size=10, color=TEXTO_BLANCO)
        c.alignment = Alignment(horizontal="left" if c == enc_sec else "right",
                                vertical="center")
    ws.row_dimensions[r_enc].height = 20

    # Filas de resumen
    secciones = [
        ("Mano de Obra",        total_mo),
        ("Repuestos",           total_rep),
        ("Fluidos",             total_flu),
    ]
    if incluir_terceros and total_terc > 0:
        secciones.insert(1, ("Servicios de Terceros", total_terc))

    total_general = total_mo + total_rep + total_flu + (total_terc if (incluir_terceros and total_terc > 0) else 0)

    for idx, (seccion, monto) in enumerate(secciones):
        r_sec = r_enc + 1 + idx
        alt   = idx % 2 == 1
        for col in range(2, 8):
            ws.cell(row=r_sec, column=col).fill = PatternFill(
                "solid", fgColor=AZUL_CLARO if alt else BLANCO
            )
        c_sec = ws.cell(row=r_sec, column=2, value=seccion)
        c_mto = ws.cell(row=r_sec, column=6, value=monto)
        c_sec.font      = Font(name="Arial", size=10, color=TEXTO_OSCURO)
        c_mto.font      = Font(name="Arial", size=10, color=TEXTO_OSCURO)
        c_sec.alignment = Alignment(horizontal="left",  vertical="center")
        c_mto.alignment = Alignment(horizontal="right", vertical="center")
        c_mto.number_format = '#,##0.00'
        ws.row_dimensions[r_sec].height = 18

    # Fila TOTAL GENERAL
    r_tot = r_enc + 1 + len(secciones)
    for col in range(2, 8):
        ws.cell(row=r_tot, column=col).fill = PatternFill("solid", fgColor=ROJO_ACC)
    c_tlabel = ws.cell(row=r_tot, column=2, value="TOTAL GENERAL")
    c_tmonto = ws.cell(row=r_tot, column=6, value=total_general)
    c_tlabel.font = Font(name="Arial", bold=True, size=11, color=TEXTO_BLANCO)
    c_tmonto.font = Font(name="Arial", bold=True, size=11, color=TEXTO_BLANCO)
    c_tlabel.alignment = Alignment(horizontal="left",  vertical="center", indent=1)
    c_tmonto.alignment = Alignment(horizontal="right", vertical="center")
    c_tmonto.number_format = '#,##0.00'
    ws.row_dimensions[r_tot].height = 22

    # Anchos de columna
    for col_letter, w in [("A",3),("B",32),("C",4),("D",4),("E",4),("F",20),("G",4),("H",4)]:
        ws.column_dimensions[col_letter].width = w


# ─── Función auxiliar para escribir tabla con formato ─────────────────
def _escribir_tabla(ws, df, start_row=1, title=None, km_cols_start=None, currency_cols=None):
    ws.sheet_view.showGridLines = False
    r = start_row

    if title:
        ws.merge_cells(start_row=r, start_column=1,
                       end_row=r, end_column=len(df.columns))
        tc = ws.cell(row=r, column=1, value=title)
        tc.font      = Font(name="Arial", bold=True, size=12, color=TEXTO_BLANCO)
        tc.fill      = PatternFill("solid", fgColor=AZUL_MEDIO)
        tc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        tc.border    = _border()
        ws.row_dimensions[r].height = 22
        r += 1

    for col_idx, col_name in enumerate(df.columns, start=1):
        c = ws.cell(row=r, column=col_idx, value=str(col_name))
        _header_style(c)
    ws.row_dimensions[r].height = 30
    r += 1

    is_total_last = False
    if len(df) > 0:
        if any(str(v).upper() == "TOTAL" for v in df.iloc[-1].values):
            is_total_last = True

    for df_row_idx, (_, row) in enumerate(df.iterrows()):
        is_total       = is_total_last and df_row_idx == len(df) - 1
        is_total_soles = any(str(v) == "TOTAL S/" for v in row.values)
        alt            = df_row_idx % 2 == 1

        for col_idx, (col_name, val) in enumerate(row.items(), start=1):
            c = ws.cell(row=r, column=col_idx)
            if isinstance(val, str) and val not in ("", "nan"):
                try:
                    val = float(val)
                except ValueError:
                    pass
            c.value = val if not (isinstance(val, float) and pd.isna(val)) else ""

            if is_total:
                _total_style(c, center=(col_idx > 2))
            elif is_total_soles:
                c.font      = Font(name="Arial", bold=True, color=TEXTO_BLANCO, size=10)
                c.fill      = PatternFill("solid", fgColor=AZUL_OSCURO)
                c.alignment = Alignment(horizontal="center" if col_idx > 2 else "left",
                                        vertical="center")
                c.border    = _border()
                if isinstance(c.value, (int, float)):
                    _currency(c)
            else:
                _data_style(c, alt=alt,
                            center=(col_idx > 2 and km_cols_start is not None
                                    and col_idx > km_cols_start))

            is_km_col   = km_cols_start is not None and col_idx >= km_cols_start
            is_curr_col = currency_cols and col_name in currency_cols
            if (is_km_col or is_curr_col) and isinstance(c.value, (int, float)):
                _currency(c)

        ws.row_dimensions[r].height = 18
        r += 1
    return r + 1


# ─── HOJA PRECIARIO RESUMEN ───────────────────────────────────────────
def _hoja_preciario(wb, df):
    ws = wb.create_sheet("Preciario")
    _escribir_tabla(ws, df, start_row=2,
                    title="Resumen de Costos por Kilometraje",
                    currency_cols=["Servicios", "Servicios terceros", "Repuestos", "Fluidos", "Total"])
    _set_col_widths(ws, {"A":8, "B":16, "C":20, "D":16, "E":16, "F":16, "G":16, "H":16})


# ─── HOJA SERVICIOS ───────────────────────────────────────────────────
def _hoja_servicios(wb, tabla_serv):
    ws = wb.create_sheet("Servicios MO")
    tiene_codigo = "Código" in tabla_serv.columns
    km_start = 4 if tiene_codigo else 3
    _escribir_tabla(ws, tabla_serv, start_row=2,
                    title="Detalle de Mano de Obra (horas estándar por KM)",
                    km_cols_start=km_start)
    ws.column_dimensions["A"].width = 6
    if tiene_codigo:
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 36
        for i, _ in enumerate(tabla_serv.columns[3:], start=4):
            ws.column_dimensions[get_column_letter(i)].width = 11
    else:
        ws.column_dimensions["B"].width = 46  # descripción más ancha
        for i, _ in enumerate(tabla_serv.columns[2:], start=3):
            ws.column_dimensions[get_column_letter(i)].width = 11


# ─── HOJA TERCEROS ────────────────────────────────────────────────────
def _hoja_terceros(wb, tabla_terc):
    ws = wb.create_sheet("Servicios Terceros")
    tiene_codigo = "Código" in tabla_terc.columns
    km_start = 4 if tiene_codigo else 3
    _escribir_tabla(ws, tabla_terc, start_row=2,
                    title="Detalle de Servicios de Terceros (S/) por KM",
                    km_cols_start=km_start)
    ws.column_dimensions["A"].width = 6
    if tiene_codigo:
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 36
        for i in range(4, len(tabla_terc.columns) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 12
    else:
        ws.column_dimensions["B"].width = 46
        for i in range(3, len(tabla_terc.columns) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 12


# ─── HOJA DETALLE DE MATERIALES (REPUESTOS O FLUIDOS) ──────────────────
def _hoja_materiales(wb, tabla_mat, sheet_name="Repuestos", title="Detalle de Repuestos por Kilometraje (S/)"):
    ws = wb.create_sheet(sheet_name)
    tiene_codigo   = "Código" in tabla_mat.columns
    tiene_cant     = "Cant." in tabla_mat.columns
    # km_start = número de columnas fijas + 1
    cols_fijas = sum([
        1,                        # Descripción siempre
        1 if tiene_codigo else 0,
        4 if tiene_cant else 0,   # Cant, VVUnit, VVenta, Dscto
        1,                        # V.Venta Final siempre
    ])
    km_start = cols_fijas + 1

    _escribir_tabla(ws, tabla_mat, start_row=2,
                    title=title,
                    km_cols_start=km_start,
                    currency_cols={"V.V.Unit.", "V.Venta", "V.Venta Final"})

    col_idx = 1
    if tiene_codigo:
        ws.column_dimensions[get_column_letter(col_idx)].width = 16
        col_idx += 1
    ws.column_dimensions[get_column_letter(col_idx)].width = 40  # Descripción
    col_idx += 1
    if tiene_cant:
        for w in [8, 12, 14, 10]:
            ws.column_dimensions[get_column_letter(col_idx)].width = w
            col_idx += 1
    ws.column_dimensions[get_column_letter(col_idx)].width = 16  # V.Venta Final
    col_idx += 1
    for i in range(col_idx, len(tabla_mat.columns) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 13


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────
def generar_excel_profesional(df, tabla_serv, tabla_repuestos, tabla_fluidos=None,
                               tabla_terc=None,
                               modelo_nombre="", km_inicio=0, km_fin=0,
                               precio_hh=0, descuento_mo=0, descuento_extra=0,
                               incluir_terceros=True):

    # Calcular totales por sección desde df
    total_mo   = df["Servicios"].sum() if "Servicios" in df.columns else 0.0
    total_terc = df["Servicios terceros"].sum() if ("Servicios terceros" in df.columns and incluir_terceros) else 0.0
    total_rep  = df["Repuestos"].sum() if "Repuestos" in df.columns else 0.0
    total_flu  = df["Fluidos"].sum() if "Fluidos" in df.columns else 0.0

    wb = Workbook()

    _hoja_portada(wb, modelo_nombre, km_inicio, km_fin, precio_hh,
                  descuento_mo, descuento_extra,
                  total_mo, total_terc, total_rep, total_flu, incluir_terceros)

    _hoja_preciario(wb, df)
    _hoja_servicios(wb, tabla_serv)

    if incluir_terceros and tabla_terc is not None:
        _hoja_terceros(wb, tabla_terc)

    _hoja_materiales(wb, tabla_repuestos, sheet_name="Repuestos",
                     title="Detalle de Repuestos por Kilometraje (S/)")

    if tabla_fluidos is not None and not tabla_fluidos.empty:
        _hoja_materiales(wb, tabla_fluidos, sheet_name="Fluidos",
                         title="Detalle de Fluidos por Kilometraje (S/)")

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output