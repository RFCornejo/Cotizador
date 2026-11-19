# 🚗 Simulador de Preciario de Mantenimientos Toyota

Aplicación web interactiva para cotizar y simular precios de mantenimientos preventivos para toda la gama de vehículos Toyota del Perú. Permite buscar por código de modelo, versión, familia, filtrar por rango de kilometraje, aplicar descuentos de mano de obra y repuestos, y exportar reportes en **Excel y PDF profesional**.

---

## ⚡ Uso Local Rápido (1 Clic)

Simplemente haz doble clic en el archivo:
```bash
iniciar.bat
```
La aplicación se abrirá automáticamente en tu navegador web (`http://localhost:8501`).

---

## 📦 Maestro de Materiales (`MAD/`): Precios VVP y Descuentos Oficiales

La aplicación integra el catálogo maestro de repuestos y materiales oficiales de Toyota (`MAD/MAD.xlsx`):
- **Carga ultrarrápida (<0.1s)** mediante caché binaria automática Parquet (`MAD/MAD.parquet`).
- **Sincronización de precios**:
  - `V.V.Unit.`: Valor de Venta al Público (`VVP` columna F del MAD).
  - `Cant.`: Cantidad especificada en el mantenimiento.
  - `V.Venta`: `V.V.Unit. × Cant.`
  - `Dscto.`: Descuento oficial (`DCTO` columna G del MAD, convertido a porcentaje).
  - `V.Venta Final`: `V.Venta × (1 - Dscto./100)`.
- **Cuadros Separados para Repuestos y Fluidos**: Cada categoría cuenta con su propia tabla, subtotales, totales por kilometraje y hoja/sección independiente en Excel y PDF.
- **Edición en vivo y descuentos diferenciados**:
  - Descuentos de mano de obra y materiales configurables en un rango de **0% a 100%**.
  - Posibilidad de aplicar descuentos masivos o editar celda por celda el descuento de cada ítem.
- **Agregar y retirar ítems**:
  - Búsqueda e incorporación de nuevos repuestos o fluidos directamente desde el catálogo MAD (149,000+ materiales).
  - Incorporación de códigos personalizados (*custom*) no listados en MAD indicando precio unitario y descuento.
  - Retiro de cualquier ítem para cotizaciones a medida.

---

## 📊 Base de Datos (`BD/`): 25 Familias y 296 Modelos

La aplicación lee directamente los archivos de mantenimiento oficiales ubicados en la carpeta `BD/`:
- **25 archivos de familias**: `TOYOTA-HILUX.xls`, `TOYOTA-YARIS.xls`, `TOYOTA-COROLLA.xls`, `TOYOTA-RAV4.xls`, `TOYOTA-FORTUNER.xls`, `TOYOTA-4RUNNER.xls`, etc.
- **Hojas individuales por modelo**: Cada pestaña representa un código de modelo específico (ej. `HILUX-2362`, `HILUX-2363`, `YARIS-1590`, `COROLLA-1095`).
- **Formato del buscador**:
  ```
  {codigo_modelo} — {version} — {familia}
  Ejemplo: 2362 — GUN125L-BGFLXF_B6 — Hilux
  Ejemplo: 2363 — GUN126L-BGFLXF3_A2 — Hilux
  ```
- **Cálculo automático de Hora Hombre (S/ HH)**:
  La tarifa por hora hombre se calcula automáticamente a partir de la celda de mano de obra dividida entre el tiempo estándar (`I8 / I7`, ej. `203.70 / 0.7 = S/ 291.00`), adaptable a cualquier variación por modelo.

### ¿Cómo agregar más modelos o actualizar precios?
Simplemente copia o reemplaza el archivo `.xls` correspondiente en la carpeta `BD/`. La aplicación lo detectará e indexará automáticamente al iniciar sin necesidad de tocar código.

---

## 🌐 Cómo Compartir la Aplicación con Otras Personas (Streamlit Cloud)

Para que tus compañeros o asesores puedan usar el cotizador desde cualquier dispositivo (computadora, tablet o celular) sin instalar nada:

1. **Subir la carpeta a GitHub**:
   - Crea un repositorio en [github.com](https://github.com).
   - Sube los archivos del proyecto (incluyendo la carpeta `BD/`, `procesador_bd.py`, `app_preciario.py`, `generar_excel_profesional.py`, `generar_pdf_profesional.py`, `logo_M.png`, `requirements.txt` y `.streamlit/config.toml`).
2. **Publicar en Streamlit Cloud**:
   - Entra a [share.streamlit.io](https://share.streamlit.io).
   - Haz clic en **"New app"**, selecciona tu repositorio y como archivo principal elige: `app_preciario.py`.
   - Haz clic en **"Deploy"**.
3. **¡Listo!**:
   - Obtendrás un enlace web público o privado para compartirlo por correo o WhatsApp.
