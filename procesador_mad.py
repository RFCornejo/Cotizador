#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para leer, procesar y consultar el catálogo Maestro de Materiales Toyota (MAD).
Optimizado con caché en formato Parquet para carga instantánea (<0.1s).
"""

import os
import pandas as pd

def cargar_catalogo_mad(carpeta_mad="MAD"):
    """
    Carga el catálogo de materiales MAD desde MAD/MAD.parquet si existe y está actualizado.
    Si no existe o si MAD.xlsx fue modificado, lee MAD.xlsx y genera MAD.parquet.
    Retorna (df_mad, lookup_dict).
    """
    mad_xlsx = os.path.join(carpeta_mad, "MAD.xlsx")
    mad_parquet = os.path.join(carpeta_mad, "MAD.parquet")

    regenerar = False
    if not os.path.exists(mad_parquet):
        regenerar = True
    elif os.path.exists(mad_xlsx):
        mtime_xlsx = os.path.getmtime(mad_xlsx)
        mtime_parquet = os.path.getmtime(mad_parquet)
        if mtime_xlsx > mtime_parquet:
            regenerar = True

    if regenerar:
        if not os.path.exists(mad_xlsx):
            raise FileNotFoundError(f"No se encontró el archivo {mad_xlsx}")
        
        # Leer columnas esenciales de MAD.xlsx
        cols = ['Código', 'Descripción', 'VVP', 'DCTO']
        try:
            df_sample = pd.read_excel(mad_xlsx, nrows=1)
            if 'Nombre de familia' in df_sample.columns:
                cols.append('Nombre de familia')
        except Exception:
            pass

        df_mad = pd.read_excel(mad_xlsx, usecols=lambda c: c in cols)
        df_mad['Código_str'] = df_mad['Código'].astype(str).str.strip().str.upper()
        df_mad['Descripción'] = df_mad['Descripción'].astype(str).str.strip()
        df_mad['VVP'] = pd.to_numeric(df_mad['VVP'], errors='coerce').fillna(0.0)
        df_mad['DCTO'] = pd.to_numeric(df_mad['DCTO'], errors='coerce').fillna(0.0)
        
        # Guardar en parquet para lecturas instantáneas posteriores
        df_mad.to_parquet(mad_parquet, engine='pyarrow', index=False)
    else:
        df_mad = pd.read_parquet(mad_parquet, engine='pyarrow')

    lookup = construir_indice_mad(df_mad)
    return df_mad, lookup


def construir_indice_mad(df_mad):
    """
    Construye un diccionario de búsqueda rápida normalizado para códigos de repuestos/materiales.
    Permite coincidencias exactas, sin ceros a la izquierda y sin guiones/espacios.
    """
    lookup = {}
    for _, row in df_mad.iterrows():
        cod = str(row['Código_str']).strip().upper()
        desc = str(row.get('Descripción', '')).strip()
        vvp = float(row.get('VVP', 0.0))
        dcto = float(row.get('DCTO', 0.0))
        familia = str(row.get('Nombre de familia', '')).strip() if 'Nombre de familia' in row else ''

        info = {
            'codigo': cod,
            'descripcion': desc,
            'vv_unit': vvp,
            'dscto': dcto,
            'familia': familia
        }

        # 1. Exacto
        if cod not in lookup:
            lookup[cod] = info
        
        # 2. Sin guiones ni espacios
        cod_clean = cod.replace('-', '').replace(' ', '')
        if cod_clean not in lookup:
            lookup[cod_clean] = info

        # 3. Sin ceros a la izquierda
        cod_no_zeros = cod.lstrip('0')
        if cod_no_zeros:
            if cod_no_zeros not in lookup:
                lookup[cod_no_zeros] = info
            cod_nz_clean = cod_no_zeros.replace('-', '').replace(' ', '')
            if cod_nz_clean not in lookup:
                lookup[cod_nz_clean] = info

    return lookup


def buscar_en_mad(codigo, lookup):
    """
    Busca un código en el diccionario MAD intentando variantes:
    exacto, sin espacios/guiones, sin ceros a la izquierda.
    Retorna el diccionario con {'codigo', 'descripcion', 'vv_unit', 'dscto'} o None.
    """
    if not codigo or not lookup:
        return None

    c = str(codigo).strip().upper()
    if c in lookup:
        return lookup[c]

    c_clean = c.replace('-', '').replace(' ', '')
    if c_clean in lookup:
        return lookup[c_clean]

    c_no_zeros = c.lstrip('0')
    if c_no_zeros in lookup:
        return lookup[c_no_zeros]

    c_nz_clean = c_no_zeros.replace('-', '').replace(' ', '')
    if c_nz_clean in lookup:
        return lookup[c_nz_clean]

    return None


def buscar_materiales_mad(df_mad, query, limit=50):
    """
    Filtra materiales en el catálogo MAD por texto o código para autocompletado en la UI.
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().upper()
    filtro = (
        df_mad['Código_str'].str.contains(q, case=False, na=False) |
        df_mad['Descripción'].str.contains(q, case=False, na=False)
    )
    sub_df = df_mad[filtro].head(limit)
    
    resultados = []
    for _, row in sub_df.iterrows():
        cod = row['Código_str']
        desc = row['Descripción']
        vvp = float(row['VVP'])
        dcto = float(row['DCTO'])
        label = f"{cod} — {desc} | S/ {vvp:,.2f} (Dscto: {dcto:.0f}%)"
        resultados.append({
            'label': label,
            'codigo': cod,
            'descripcion': desc,
            'vv_unit': vvp,
            'dscto': dcto
        })
    return resultados
