# =============================================================
# ARCHIVO: analisis_aqualimpia.py
# PROYECTO: Análisis de Plantas de Tratamiento — AquaLimpia S.A.
# ASIGNATURA: Ciencia de Datos — CIEDT1301 — Semana 8
# AUTOR: Juan Bobadilla
# DESCRIPCIÓN: Flujo principal del ciclo completo de análisis.
#              Importa funciones desde funciones_aqualimpia.py
#              y el dashboard interactivo desde dashboard_interactivo.py
#
# PREGUNTAS DE INVESTIGACIÓN:
#   1. ¿Qué planta tiene mejor eficiencia de remoción de DBO?
#   2. ¿Existe correlación entre caudal de entrada y DBO de salida?
#   3. ¿Cuál es la tendencia mensual de cumplimiento normativo?
#   4. ¿Qué factores operativos se asocian al incumplimiento?
#
# EJECUCIÓN:
#   python analisis_aqualimpia.py
#   (o ejecutar celda por celda en Google Colab)
# =============================================================

# ── LIBRERÍAS ─────────────────────────────────────────────────
import pandas as pd
import numpy as np
import os

# ── MÓDULOS DEL PROYECTO ──────────────────────────────────────
# Importa todas las funciones analíticas desde el módulo externo
from funciones_aqualimpia import (
    cargar_datos,
    evaluar_calidad_datos,
    calcular_eficiencia_dbo,
    analisis_estadistico_planta,
    guardar_resumen_joblib,
    generar_dashboard_estatico,
    exportar_reportes_excel
)

# Importa la función del dashboard interactivo (Plotly — Semana 4)
from dashboard_interactivo import generar_dashboard_interactivo


# =============================================================
# FLUJO PRINCIPAL — encapsulado en main() para buenas prácticas
# =============================================================
def main():
    """
    Ejecuta el ciclo completo de ciencia de datos en 9 etapas:
    carga → exploración → calidad → limpieza → métricas →
    estadísticas → serialización → dashboards → reportes
    """

    # ─────────────────────────────────────────────────────────
    # ETAPA 1: CARGA DE DATOS
    # ─────────────────────────────────────────────────────────
    print("=" * 62)
    print("  ETAPA 1 — CARGA DE DATOS")
    print("=" * 62)

    RUTA = 'dataset_set_A_aguas_residuales.xlsx'
    df = cargar_datos(RUTA)

    # ─────────────────────────────────────────────────────────
    # ETAPA 2: EXPLORACIÓN INICIAL
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 2 — EXPLORACIÓN INICIAL")
    print("=" * 62)

    # .head(): primeras 5 filas — equivale a SELECT TOP 5 en SQL
    print("\n  Primeras 5 filas:")
    print(df.head().to_string())

    # .info(): tipos de datos y nulos por columna
    print("\n  Estructura del dataset:")
    df.info()

    # .describe(): count, mean, std, min, percentiles, max
    print("\n  Estadísticos descriptivos:")
    print(df.describe().round(2).to_string())

    # ─────────────────────────────────────────────────────────
    # ETAPA 3: EVALUACIÓN DE CALIDAD DE DATOS
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 3 — CALIDAD DE DATOS")
    print("=" * 62)

    # Evalúa: nulos, duplicados, outliers (z-score + IQR), rangos
    informe_calidad = evaluar_calidad_datos(df)

    # ─────────────────────────────────────────────────────────
    # ETAPA 4: LIMPIEZA
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 4 — LIMPIEZA DE DATOS")
    print("=" * 62)

    filas_antes = len(df)

    # Elimina filas con cualquier valor nulo
    df.dropna(inplace=True)

    # Elimina filas completamente duplicadas
    df.drop_duplicates(inplace=True)

    # Filtra pH fuera del rango físico válido (5.5 – 9.5)
    df = df[(df['pH_entrada'] >= 5.5) & (df['pH_entrada'] <= 9.5)]

    # Filtra DBO de entrada negativa (imposible físicamente)
    df = df[df['DBO_entrada_mg_L'] > 0]

    print(f"  Filas antes  : {filas_antes}")
    print(f"  Filas después: {len(df)}")
    print(f"  Eliminadas   : {filas_antes - len(df)}")

    # ─────────────────────────────────────────────────────────
    # ETAPA 5: CÁLCULO DE MÉTRICAS CON NUMPY
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 5 — MÉTRICAS CON NUMPY")
    print("=" * 62)

    # Calcula eficiencia de remoción DBO con arrays NumPy
    df = calcular_eficiencia_dbo(df)

    # ─────────────────────────────────────────────────────────
    # ETAPA 6: ANÁLISIS ESTADÍSTICO CON SCIPY
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 6 — ESTADÍSTICAS CON SCIPY")
    print("=" * 62)

    # Correlación de Pearson + test de normalidad Shapiro-Wilk
    resumen = analisis_estadistico_planta(df)

    # ─────────────────────────────────────────────────────────
    # ETAPA 7: PERSISTENCIA CON JOBLIB
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 7 — PERSISTENCIA CON JOBLIB")
    print("=" * 62)

    # Serializa el resumen para reutilización sin recalcular
    guardar_resumen_joblib(resumen, 'resumen_plantas.joblib')

    # ─────────────────────────────────────────────────────────
    # ETAPA 8A: DASHBOARD ESTÁTICO (Matplotlib)
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 8A — DASHBOARD ESTÁTICO (Matplotlib)")
    print("=" * 62)

    generar_dashboard_estatico(df, resumen, 'dashboard_aqualimpia.png')

    # ─────────────────────────────────────────────────────────
    # ETAPA 8B: DASHBOARD INTERACTIVO (Plotly — Semana 4)
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 8B — DASHBOARD INTERACTIVO (Plotly HTML)")
    print("=" * 62)

    # Llamada correcta: importa la función y la llama con el DataFrame
    generar_dashboard_interactivo(df, 'dashboard_interactivo_aqualimpia.html')
    
    # Lee el contenido del HTML y lo renderiza directo en el output
    from IPython.display import display, HTML

    with open('dashboard_interactivo_aqualimpia.html', 'r', encoding='utf-8') as f:
        contenido = f.read()

    display(HTML(contenido))

    # ─────────────────────────────────────────────────────────
    # ETAPA 9: EXPORTACIÓN DE REPORTES EXCEL
    # ─────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  ETAPA 9 — REPORTES EXCEL")
    print("=" * 62)

    exportar_reportes_excel(df, resumen)

    # ─────────────────────────────────────────────────────────
    # RESUMEN EJECUTIVO
    # ─────────────────────────────────────────────────────────
    mejor = resumen.loc[resumen['eficiencia_media_pct'].idxmax(), 'planta']
    peor  = resumen.loc[resumen['eficiencia_media_pct'].idxmin(), 'planta']
    ef_m  = resumen.loc[resumen['planta']==mejor, 'eficiencia_media_pct'].values[0]
    ef_p  = resumen.loc[resumen['planta']==peor,  'eficiencia_media_pct'].values[0]
    tasa  = round(df['cumplimiento_norma'].mean() * 100, 1)

    print(f"""
{"=" * 62}
  CICLO COMPLETO — HALLAZGOS CLAVE
{"=" * 62}
  Mejor eficiencia DBO : {mejor} ({ef_m:.1f}%)
  Menor eficiencia DBO : {peor} ({ef_p:.1f}%)
  Cumplimiento global  : {tasa}%
  Incumplimientos      : {informe_calidad['incumplimientos']} / {len(df)} registros

  Archivos generados:
  ├── funciones_aqualimpia.py                (módulo funciones)
  ├── analisis_aqualimpia.py                 (flujo principal)
  ├── dashboard_interactivo.py               (módulo Plotly)
  ├── dashboard_aqualimpia.png               (PNG estático)
  ├── dashboard_interactivo_aqualimpia.html  (HTML interactivo)
  ├── reporte_area_operaciones.xlsx          (Área Operaciones)
  ├── reporte_gestion_ambiental.xlsx         (Gestión Ambiental)
  ├── resumen_plantas.joblib                 (resultados serializados)
  └── README.md                              (documentación técnica)

""")


# =============================================================
# PUNTO DE ENTRADA — buenas prácticas (S7 del curso)
# Solo ejecuta main() cuando se corre directamente este archivo.
# Si se importa como módulo, NO ejecuta main() automáticamente.
# =============================================================
if __name__ == "__main__":
    main()
