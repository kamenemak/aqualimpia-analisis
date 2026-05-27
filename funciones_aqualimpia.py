# =============================================================
# ARCHIVO: funciones_aqualimpia.py
# PROYECTO: Análisis de Plantas de Tratamiento — AquaLimpia S.A.
# ASIGNATURA: Ciencia de Datos — CIEDT1301 — Semana 8
# AUTOR: Juan Bobadilla
# DESCRIPCIÓN: Módulo de funciones reutilizables. Contiene toda
#              la lógica analítica del proyecto. Se importa desde
#              analisis_aqualimpia.py (script principal).
# =============================================================

# ── LIBRERÍAS REQUERIDAS POR LA RÚBRICA ───────────────────────
import numpy as np           # cálculo numérico vectorizado
from scipy import stats      # estadísticas avanzadas (Pearson, Shapiro)
from joblib import dump, load# serialización de objetos Python

# ── LIBRERÍAS ESTÁNDAR ────────────────────────────────────────
import pandas as pd
import matplotlib.pyplot as plt
import os


# =============================================================
# FUNCIÓN 1: cargar_datos
# =============================================================
def cargar_datos(ruta_archivo):
    """
    Carga el dataset de AquaLimpia desde Excel o CSV.
    Convierte la columna fecha_registro al tipo datetime.

    Parámetros:
        ruta_archivo (str): ruta al archivo .xlsx o .csv

    Retorna:
        pd.DataFrame con los datos listos para analizar
    """
    extension = os.path.splitext(ruta_archivo)[1].lower()

    if extension == '.csv':
        # encoding='utf-8-sig' maneja el BOM que genera Excel en CSVs
        df = pd.read_csv(ruta_archivo, encoding='utf-8-sig')
    elif extension in ['.xlsx', '.xls']:
        df = pd.read_excel(ruta_archivo)
    else:
        raise ValueError(f"Formato no soportado: {extension}")

    # Convierte texto a tipo fecha; errores se convierten a NaT
    df['fecha_registro'] = pd.to_datetime(df['fecha_registro'], errors='coerce')

    print(f"  ✓ Dataset cargado: {df.shape[0]} registros × {df.shape[1]} columnas")
    print(f"  ✓ Plantas: {list(df['planta'].unique())}")
    print(f"  ✓ Período: {df['fecha_registro'].min().date()} → {df['fecha_registro'].max().date()}")
    return df


# =============================================================
# FUNCIÓN 2: evaluar_calidad_datos
# Librerías: NumPy (z-score) y SciPy (zscore)
# =============================================================
def evaluar_calidad_datos(df):
    """
    Evalúa la calidad del dataset con cuatro criterios:
    nulos, duplicados, outliers (z-score Y IQR), rangos físicos.

    Parámetros:
        df (pd.DataFrame): dataset cargado

    Retorna:
        dict con el informe completo de calidad
    """
    informe = {}

    # ── Nulos ─────────────────────────────────────────────────
    nulos = df.isnull().sum()
    informe['nulos_por_columna'] = nulos
    informe['total_nulos'] = int(nulos.sum())

    # ── Duplicados ────────────────────────────────────────────
    informe['total_duplicados'] = int(df.duplicated().sum())

    columnas_num = [
        'caudal_entrada_m3_d', 'DBO_entrada_mg_L', 'DBO_salida_mg_L',
        'energia_aeracion_kWh', 'lodos_generados_kg_d', 'pH_entrada'
    ]

    # ── Outliers método Z-score (NumPy + SciPy) ───────────────
    # z-score: cuántas desviaciones estándar se aleja un valor de la media
    # |z| > 3 → outlier estadístico
    outliers_z = {}
    for col in columnas_num:
        valores = np.array(df[col].dropna())             # NumPy array
        z = np.abs(stats.zscore(valores))                # SciPy zscore
        outliers_z[col] = int(np.sum(z > 3))
    informe['outliers_zscore'] = outliers_z

    # ── Outliers método IQR (NumPy) ───────────────────────────
    # IQR = Q3 - Q1; outlier si valor < Q1-1.5*IQR o > Q3+1.5*IQR
    # Más robusto que z-score para datos ambientales no normales
    outliers_iqr = {}
    for col in columnas_num:
        Q1  = np.percentile(df[col].dropna(), 25)  # primer cuartil
        Q3  = np.percentile(df[col].dropna(), 75)  # tercer cuartil
        IQR = Q3 - Q1
        n   = int(((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum())
        outliers_iqr[col] = n
    informe['outliers_iqr'] = outliers_iqr
    informe['total_outliers'] = sum(outliers_iqr.values())

    # ── Rangos físicos inválidos ──────────────────────────────
    informe['pH_fuera_rango']   = int(((df['pH_entrada'] < 5.5) | (df['pH_entrada'] > 9.5)).sum())
    informe['DBO_salida_extr']  = int((df['DBO_salida_mg_L'] > 80).sum())

    # ── Cumplimiento normativo ────────────────────────────────
    informe['tasa_cumplimiento_pct'] = round(df['cumplimiento_norma'].mean() * 100, 1)
    informe['incumplimientos']       = int((df['cumplimiento_norma'] == 0).sum())

    print("\n  ── INFORME DE CALIDAD ────────────────────────────────")
    print(f"  Nulos              : {informe['total_nulos']}")
    print(f"  Duplicados         : {informe['total_duplicados']}")
    print(f"  Outliers (z>3)     : {sum(outliers_z.values())}")
    print(f"  Outliers (IQR×1.5) : {informe['total_outliers']}")
    print(f"  pH fuera de rango  : {informe['pH_fuera_rango']}")
    print(f"  Tasa cumplimiento  : {informe['tasa_cumplimiento_pct']}%")
    print(f"  Incumplimientos    : {informe['incumplimientos']} registros")
    return informe


# =============================================================
# FUNCIÓN 3: calcular_eficiencia_dbo
# Librería: NumPy (operaciones vectorizadas sobre arrays)
# =============================================================
def calcular_eficiencia_dbo(df):
    """
    Calcula la eficiencia de remoción de DBO por registro.
    Fórmula: eficiencia = (DBO_entrada - DBO_salida) / DBO_entrada × 100

    Usa operaciones vectorizadas de NumPy sobre arrays completos,
    lo que es más eficiente que iterar fila por fila.

    Parámetros:
        df (pd.DataFrame): dataset con columnas DBO_entrada y DBO_salida

    Retorna:
        pd.DataFrame con columna 'eficiencia_dbo_pct' agregada
    """
    entrada = np.array(df['DBO_entrada_mg_L'], dtype=float)  # NumPy array
    salida  = np.array(df['DBO_salida_mg_L'],  dtype=float)

    # np.where evita división por cero
    eficiencia = np.where(entrada > 0, (entrada - salida) / entrada * 100, 0)
    df['eficiencia_dbo_pct'] = np.round(eficiencia, 2)      # NumPy round

    print(f"\n  ── EFICIENCIA DBO (global) ───────────────────────────")
    print(f"  Promedio : {np.mean(eficiencia):.1f}%")
    print(f"  Mínimo   : {np.min(eficiencia):.1f}%  |  Máximo: {np.max(eficiencia):.1f}%")
    print(f"  Std Dev  : {np.std(eficiencia):.1f}%")
    return df


# =============================================================
# FUNCIÓN 4: analisis_estadistico_planta
# Librería: SciPy (pearsonr, shapiro)
# =============================================================
def analisis_estadistico_planta(df):
    """
    Aplica estadísticas avanzadas con SciPy para cada planta:
    - Correlación de Pearson: relación caudal vs DBO de salida
    - Test de normalidad Shapiro-Wilk sobre eficiencia DBO

    Parámetros:
        df (pd.DataFrame): dataset con eficiencia_dbo_pct calculada

    Retorna:
        pd.DataFrame: tabla resumen con métricas por planta
    """
    filas = []
    for planta in df['planta'].unique():
        sub = df[df['planta'] == planta]

        # Correlación de Pearson (SciPy)
        # r: coeficiente (-1 a 1); p: significancia (< 0.05 = significativa)
        r, p = stats.pearsonr(sub['caudal_entrada_m3_d'], sub['DBO_salida_mg_L'])

        # Test de normalidad Shapiro-Wilk (SciPy)
        # H0: los datos son normales; p > 0.05 = no se rechaza normalidad
        _, p_norm = stats.shapiro(sub['eficiencia_dbo_pct'])

        efi = np.array(sub['eficiencia_dbo_pct'])
        filas.append({
            'planta'               : planta,
            'n_registros'          : len(sub),
            'eficiencia_media_pct' : round(float(np.mean(efi)), 2),
            'eficiencia_std'       : round(float(np.std(efi)), 2),
            'DBO_salida_media'     : round(float(sub['DBO_salida_mg_L'].mean()), 2),
            'tasa_cumplimiento_pct': round(float(sub['cumplimiento_norma'].mean() * 100), 1),
            'correlacion_r'        : round(float(r), 3),
            'correlacion_p'        : round(float(p), 4),
            'normalidad_p'         : round(float(p_norm), 4),
            'caudal_medio_m3_d'    : round(float(sub['caudal_entrada_m3_d'].mean()), 0),
            'energia_media_kWh'    : round(float(sub['energia_aeracion_kWh'].mean()), 1),
        })

    resultado = pd.DataFrame(filas)
    print("\n  ── ESTADÍSTICAS POR PLANTA ───────────────────────────")
    print(resultado[['planta','eficiencia_media_pct','tasa_cumplimiento_pct',
                      'correlacion_r','correlacion_p']].to_string(index=False))
    return resultado


# =============================================================
# FUNCIÓN 5: guardar_resumen_joblib / cargar_resumen_joblib
# Librería: Joblib (serialización de objetos Python)
# =============================================================
def guardar_resumen_joblib(resumen, ruta='resumen_plantas.joblib'):
    """
    Guarda el DataFrame de resumen en formato binario con Joblib.
    Permite reutilizar los resultados en otros scripts sin recalcular.

    Parámetros:
        resumen (pd.DataFrame): métricas estadísticas por planta
        ruta (str): nombre del archivo de salida

    Retorna:
        str: ruta donde se guardó el archivo
    """
    dump(resumen, ruta)   # Joblib dump: serializa a disco
    print(f"  ✓ Resumen guardado (joblib): {ruta}")
    return ruta


def cargar_resumen_joblib(ruta):
    """
    Carga un DataFrame previamente guardado con Joblib.

    Parámetros:
        ruta (str): ruta al archivo .joblib

    Retorna:
        El objeto deserializado (DataFrame)
    """
    obj = load(ruta)      # Joblib load: deserializa desde disco
    print(f"  ✓ Resumen cargado (joblib): {ruta}")
    return obj


# =============================================================
# FUNCIÓN 6: generar_dashboard_estatico
# Librería: Matplotlib
# =============================================================
def generar_dashboard_estatico(df, resumen, ruta='dashboard_aqualimpia.png'):
    """
    Genera un dashboard estático con 6 gráficos usando Matplotlib.
    Lo muestra en pantalla Y lo guarda como PNG.

    Parámetros:
        df (pd.DataFrame): dataset completo con eficiencia_dbo_pct
        resumen (pd.DataFrame): métricas por planta
        ruta (str): ruta del archivo PNG de salida
    """
    COLORES = {'Planta Norte':'#1D9E75', 'Planta Sur':'#3B8BD4', 'Planta Centro':'#E85D24'}
    plantas  = list(df['planta'].unique())
    colores  = [COLORES.get(p, '#888') for p in plantas]

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('AquaLimpia S.A. — Dashboard Estático\nPeríodo: Jul–Oct 2025',
                 fontsize=15, fontweight='bold', y=1.01)

    # ── G1: Eficiencia DBO por planta ─────────────────────────
    ax = axes[0, 0]
    bars = ax.bar(resumen['planta'], resumen['eficiencia_media_pct'],
                  color=colores, edgecolor='white')
    ax.axhline(85, color='red', linestyle='--', linewidth=1.2, label='Mínimo 85%')
    ax.set_title('Eficiencia DBO por planta', fontweight='bold')
    ax.set_ylabel('Eficiencia (%)')
    ax.set_ylim(0, 100)
    ax.legend(fontsize=9)
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                f'{b.get_height():.1f}%', ha='center', fontsize=10)

    # ── G2: Tasa cumplimiento normativo ───────────────────────
    ax = axes[0, 1]
    bars2 = ax.bar(resumen['planta'], resumen['tasa_cumplimiento_pct'],
                   color=colores, edgecolor='white')
    ax.axhline(50, color='orange', linestyle='--', linewidth=1.2, label='Umbral 50%')
    ax.set_title('Tasa de cumplimiento normativo', fontweight='bold')
    ax.set_ylabel('Cumplimiento (%)')
    ax.set_ylim(0, 100)
    ax.legend(fontsize=9)
    for b in bars2:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                f'{b.get_height():.1f}%', ha='center', fontsize=10)

    # ── G3: Dispersión DBO salida vs Caudal ───────────────────
    ax = axes[0, 2]
    for p, c in COLORES.items():
        sub = df[df['planta'] == p]
        ax.scatter(sub['caudal_entrada_m3_d'], sub['DBO_salida_mg_L'],
                   alpha=0.5, color=c, label=p, s=20)
    ax.axhline(35, color='red', linestyle='--', linewidth=1.2, label='Norma 35 mg/L')
    ax.set_title('DBO salida vs Caudal entrada', fontweight='bold')
    ax.set_xlabel('Caudal (m³/d)')
    ax.set_ylabel('DBO salida (mg/L)')
    ax.legend(fontsize=8)

    # ── G4: Boxplot eficiencia DBO ────────────────────────────
    ax = axes[1, 0]
    datos = [df[df['planta'] == p]['eficiencia_dbo_pct'].values for p in plantas]
    bp = ax.boxplot(datos, patch_artist=True, labels=plantas)
    for patch, c in zip(bp['boxes'], colores):
        patch.set_facecolor(c); patch.set_alpha(0.7)
    ax.axhline(85, color='red', linestyle='--', linewidth=1.2, label='Mínimo 85%')
    ax.set_title('Distribución eficiencia DBO', fontweight='bold')
    ax.set_ylabel('Eficiencia (%)')
    ax.legend(fontsize=9)

    # ── G5: Evolución mensual DBO salida ──────────────────────
    ax = axes[1, 1]
    for p, c in COLORES.items():
        sub = df[df['planta'] == p].sort_values('fecha_registro')
        mensual = sub.set_index('fecha_registro')['DBO_salida_mg_L'].resample('ME').mean()
        ax.plot(mensual.index, mensual.values, marker='o', color=c, label=p, linewidth=1.8)
    ax.axhline(35, color='red', linestyle='--', linewidth=1.2, label='Norma 35 mg/L')
    ax.set_title('Evolución mensual DBO salida', fontweight='bold')
    ax.set_xlabel('Mes')
    ax.set_ylabel('DBO salida (mg/L)')
    ax.legend(fontsize=8)
    ax.tick_params(axis='x', rotation=30)

    # ── G6: Cumplimiento por mes (barras apiladas) ────────────
    ax = axes[1, 2]
    tmp = df.copy()
    tmp['mes'] = tmp['fecha_registro'].dt.to_period('M')
    rm = tmp.groupby('mes')['cumplimiento_norma'].agg(
        cumple=lambda x: (x==1).sum(),
        no_cumple=lambda x: (x==0).sum()
    ).reset_index()
    meses = rm['mes'].astype(str)
    ax.bar(meses, rm['cumple'], label='Cumple', color='#1D9E75', alpha=0.85)
    ax.bar(meses, rm['no_cumple'], bottom=rm['cumple'],
           label='No cumple', color='#E24B4A', alpha=0.85)
    ax.set_title('Cumplimiento normativo por mes', fontweight='bold')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Número de registros')
    ax.legend(fontsize=9)
    ax.tick_params(axis='x', rotation=30)

    plt.tight_layout()
    # PASO 1: guardar PNG antes de mostrar (show limpia la figura)
    plt.savefig(ruta, dpi=150, bbox_inches='tight')
    print(f"  ✓ Dashboard estático guardado: {ruta}")
    # PASO 2: mostrar en pantalla (ventana emergente o inline en Colab)
    plt.show()
    plt.close()


# =============================================================
# FUNCIÓN 7: exportar_reportes_excel
# =============================================================
def exportar_reportes_excel(df, resumen):
    """
    Genera 2 archivos Excel diferenciados por área:
    - reporte_area_operaciones.xlsx  (Área Operaciones)
    - reporte_gestion_ambiental.xlsx (Área Gestión Ambiental)

    Parámetros:
        df (pd.DataFrame): dataset completo con eficiencia calculada
        resumen (pd.DataFrame): métricas estadísticas por planta
    """
    # ── Área Operaciones ──────────────────────────────────────
    with pd.ExcelWriter('reporte_area_operaciones.xlsx', engine='openpyxl') as w:
        cols_op = ['fecha_registro','planta','caudal_entrada_m3_d',
                   'DBO_entrada_mg_L','DBO_salida_mg_L',
                   'energia_aeracion_kWh','lodos_generados_kg_d','eficiencia_dbo_pct']
        df[cols_op].to_excel(w, sheet_name='Detalle_Operativo', index=False)
        # Hoja de alertas: eficiencia menor al 75%
        df[df['eficiencia_dbo_pct'] < 75][cols_op].to_excel(
            w, sheet_name='Alertas_Criticas', index=False)
        resumen.to_excel(w, sheet_name='Resumen_Por_Planta', index=False)

    alertas = len(df[df['eficiencia_dbo_pct'] < 75])
    print(f"  ✓ reporte_area_operaciones.xlsx ({alertas} alertas críticas)")

    # ── Área Gestión Ambiental ────────────────────────────────
    with pd.ExcelWriter('reporte_gestion_ambiental.xlsx', engine='openpyxl') as w:
        cols_ga = ['fecha_registro','planta','DBO_salida_mg_L',
                   'cumplimiento_norma','pH_entrada','eficiencia_dbo_pct']
        df_ga = df[cols_ga].copy()
        df_ga['estado_norma'] = df_ga['cumplimiento_norma'].map({1:'CUMPLE', 0:'INCUMPLE'})
        df_ga.to_excel(w, sheet_name='Detalle_Ambiental', index=False)
        df_ga[df_ga['cumplimiento_norma']==0].to_excel(
            w, sheet_name='Incumplimientos', index=False)
        # Resumen mensual de cumplimiento
        tmp = df.copy()
        tmp['mes'] = tmp['fecha_registro'].dt.to_period('M').astype(str)
        rm = tmp.groupby(['mes','planta']).agg(
            registros=('cumplimiento_norma','count'),
            cumplimientos=('cumplimiento_norma','sum'),
            DBO_salida_media=('DBO_salida_mg_L','mean')
        ).round(2).reset_index()
        rm['tasa_cumplimiento_pct'] = (rm['cumplimientos']/rm['registros']*100).round(1)
        rm.to_excel(w, sheet_name='Resumen_Mensual', index=False)

    incumpl = len(df[df['cumplimiento_norma']==0])
    print(f"  ✓ reporte_gestion_ambiental.xlsx ({incumpl} incumplimientos)")


# =============================================================
# BLOQUE PRINCIPAL — solo se ejecuta si corres este archivo
# directamente (python funciones_aqualimpia.py), no cuando
# se importa desde analisis_aqualimpia.py
# =============================================================
if __name__ == "__main__":
    print("Este archivo es un módulo de funciones.")
    print("Ejecútalo desde analisis_aqualimpia.py")
    print("Funciones disponibles:")
    funciones = [k for k,v in globals().items()
                 if callable(v) and not k.startswith('_')]
    for f in funciones:
        print(f"  - {f}()")
