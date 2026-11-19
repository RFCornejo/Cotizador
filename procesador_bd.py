#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para leer y procesar las bases de datos oficiales de mantenimiento Toyota (archivos XML-Spreadsheet en carpeta BD).
"""

import os
import glob
import xml.etree.ElementTree as ET
import pandas as pd


def _col_letter(col_idx):
    """Convierte índice numérico (1-based) a letra de columna Excel (A, B, ..., Z, AA, AB...)."""
    result = ''
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _get_row_dict(row_elem):
    """Extrae las celdas de una fila XML a un diccionario {col_letter: valor}."""
    cur_col = 0
    row_dict = {}
    for cell in row_elem.findall('{urn:schemas-microsoft-com:office:spreadsheet}Cell'):
        c_idx_attr = cell.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
        cur_col = int(c_idx_attr) if c_idx_attr else cur_col + 1
        data = cell.find('{urn:schemas-microsoft-com:office:spreadsheet}Data')
        if data is not None and data.text is not None:
            row_dict[_col_letter(cur_col)] = data.text.strip()
    return row_dict


def _leer_xml_root(fpath):
    """Lee un archivo XLS (XML Spreadsheet 2003) manejando codificación UTF-8 o CP1252."""
    with open(fpath, 'rb') as fp:
        raw = fp.read()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('cp1252', errors='replace')
    return ET.fromstring(text)


def indexar_modelos_bd(carpeta_bd="BD"):
    """
    Escanea todos los archivos .xls en la carpeta BD y extrae el catálogo de todos los modelos y hojas disponibles.
    Retorna una lista de diccionarios con la información de cada modelo.
    """
    if not os.path.exists(carpeta_bd):
        return []

    bd_files = sorted(glob.glob(os.path.join(carpeta_bd, "*.xls")))
    model_index = []
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

    for fpath in bd_files:
        fname = os.path.basename(fpath)
        # Extraer familia a partir del nombre del archivo: TOYOTA-HILUX.xls -> Hilux
        familia = fname.replace("TOYOTA-", "").replace(".xls", "").title()
        
        try:
            root = _leer_xml_root(fpath)
        except Exception:
            continue

        for ws in root.findall('ss:Worksheet', ns):
            sname = ws.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Name', '')
            if not sname:
                continue

            # Código de modelo (ej: HILUX-2362 -> 2362)
            parts = sname.split('-')
            codigo = parts[-1] if len(parts) > 1 else sname

            # Extraer versión y descripción desde la fila 4
            table = ws.find('ss:Table', ns)
            version = ""
            desc_modelo = ""

            if table is not None:
                cur_r = 0
                for r in table.findall('ss:Row', ns):
                    idx_attr = r.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
                    cur_r = int(idx_attr) if idx_attr else cur_r + 1
                    if cur_r == 4:
                        rd = _get_row_dict(r)
                        desc_modelo = rd.get('B', '').replace('Aplica al siguiente', '').replace(':', '').strip()
                        # Columna H tiene el código de versión
                        version = rd.get('H', '')
                        break

            version_mostrar = version if version else codigo
            label = f"{codigo} — {version_mostrar} — {familia}"

            model_index.append({
                'archivo': fpath,
                'hoja': sname,
                'familia': familia,
                'codigo_modelo': codigo,
                'version': version_mostrar,
                'desc_modelo': desc_modelo or f"{familia} {codigo}",
                'label': label
            })

    return model_index


def cargar_detalle_modelo(fpath, hoja_name):
    """
    Lee una hoja específica de mantenimiento de un archivo XLS y extrae todos los datos:
    KMs, tiempos de mano de obra, precios de terceros, repuestos y fluidos.
    """
    root = _leer_xml_root(fpath)
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

    target_ws = None
    for ws in root.findall('ss:Worksheet', ns):
        if ws.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Name') == hoja_name:
            target_ws = ws
            break

    if target_ws is None:
        raise ValueError(f"No se encontró la hoja '{hoja_name}' en el archivo {fpath}")

    table = target_ws.find('ss:Table', ns)
    rows = {}
    cur_r = 0
    for r in table.findall('ss:Row', ns):
        idx = r.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
        cur_r = int(idx) if idx else cur_r + 1
        rows[cur_r] = _get_row_dict(r)

    # 1. Mapeo de columnas KM (fila 5)
    km_cols = {} # col_letter -> km_int
    for c_let, val in rows.get(5, {}).items():
        v_upper = str(val).upper().strip()
        if v_upper.endswith('K'):
            try:
                km_cols[c_let] = int(v_upper.replace('K', '')) * 1000
            except:
                pass
        elif 'INSPEC' in v_upper or 'GRATUITA' in v_upper:
            km_cols[c_let] = 1000

    kms_ordenados = sorted(km_cols.values())

    # Detectar intervalo estándar (diferencia entre primeros KMs no-1000)
    kms_normales = [k for k in kms_ordenados if k > 1000]
    intervalo_km = (kms_normales[1] - kms_normales[0]) if len(kms_normales) > 1 else 5000

    # 2. Mano de Obra: Tiempo (Row 7) y Servicio (Row 8)
    tiempo_row = rows.get(7, {})
    mo_row = rows.get(8, {})

    # Precio HH sugerido: Celda Col I (5K) Servicio / Tiempo
    mo_5k = float(mo_row.get('I', 0) or 0)
    t_5k = float(tiempo_row.get('I', 0) or 0)
    precio_hh_sugerido = round(mo_5k / t_5k, 2) if t_5k > 0 else 291.0

    serv_horas_mo = {}
    for c_let, km in km_cols.items():
        try:
            serv_horas_mo[km] = float(tiempo_row.get(c_let, 0) or 0)
        except:
            serv_horas_mo[km] = 0.0

    # 3. Servicios adicionales / Terceros (entre fila 8 y REPUESTOS)
    # y Repuestos / Fluidos (separados)
    terceros_items = []
    repuestos_items = []
    fluidos_items = []

    current_sec = 'MO'
    for r_num, rd in sorted(rows.items()):
        cat_b = rd.get('B', '').upper()
        if 'REPUESTOS' in cat_b:
            current_sec = 'REP'
        elif 'FLUIDOS' in cat_b:
            current_sec = 'FLU'
        elif 'SUB TOTALES' in cat_b or 'PRECIO TOTAL' in cat_b:
            current_sec = 'TOTALS'

        desc = rd.get('D', '')
        if not desc:
            continue

        if current_sec == 'MO' and r_num > 8:
            # Servicio tercero o adicional
            item_kms = {}
            for c_let, km in km_cols.items():
                try:
                    item_kms[km] = float(rd.get(c_let, 0) or 0)
                except:
                    item_kms[km] = 0.0
            terceros_items.append({
                'item_num': len(terceros_items) + 1,
                'codigo': f"TERC-{len(terceros_items)+1:02d}",
                'descripcion': desc,
                'kms': item_kms
            })

        elif current_sec in ('REP', 'FLU'):
            code = rd.get('E', '')
            if code:
                qty_str = rd.get('F', '1')
                try:
                    qty = float(qty_str) if qty_str else 1.0
                except:
                    qty = 1.0

                item_kms = {}
                unit_val = None
                for c_let, km in km_cols.items():
                    val_str = rd.get(c_let, '')
                    try:
                        v = float(val_str) if val_str else 0.0
                    except:
                        v = 0.0
                    item_kms[km] = v
                    if v > 0 and unit_val is None:
                        unit_val = (v / qty) if qty > 0 else v

                u_val = round(unit_val or 0.0, 2)
                # Cantidades por cada KM (multiplicador de consumo en ese kilometraje)
                km_cantidades = {}
                for km, v in item_kms.items():
                    if v > 0 and u_val > 0:
                        km_cantidades[km] = round(v / u_val, 2)
                    elif v > 0:
                        km_cantidades[km] = qty
                    else:
                        km_cantidades[km] = 0.0

                target_list = repuestos_items if current_sec == 'REP' else fluidos_items
                tipo_str = 'REPUESTO' if current_sec == 'REP' else 'FLUIDO'

                target_list.append({
                    'item_num': len(target_list) + 1,
                    'tipo': tipo_str,
                    'codigo': code,
                    'descripcion': desc,
                    'cantidad': qty,
                    'vv_unit': u_val,
                    'kms': item_kms,
                    'km_cantidades': km_cantidades
                })

    titulo = rows.get(3, {}).get('B', '')
    desc_modelo = rows.get(4, {}).get('B', '').replace('Aplica al siguiente', '').replace(':', '').strip()
    version_h = rows.get(4, {}).get('H', '')

    return {
        'titulo': titulo,
        'desc_modelo': desc_modelo,
        'version': version_h,
        'kms': kms_ordenados,
        'intervalo_km': intervalo_km,
        'precio_hh_sugerido': precio_hh_sugerido,
        'serv_horas_mo': serv_horas_mo,
        'terceros_items': terceros_items,
        'repuestos_items': repuestos_items,
        'fluidos_items': fluidos_items
    }
