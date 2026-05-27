# AquaLimpia S.A. — Análisis de Plantas de Tratamiento de Aguas Residuales

## Descripción del Proyecto

Proyecto de ciencia de datos desarrollado para **AquaLimpia S.A.**, empresa dedicada al tratamiento de aguas residuales urbanas e industriales. Analiza el desempeño de tres plantas de tratamiento (Norte, Sur, Centro) durante jul–oct 2025, generando evidencia analítica reproducible para apoyar la gestión ambiental y operaciones.

---

## Objetivos

1. Evaluar la **eficiencia de remoción de DBO** por planta de tratamiento.
2. Identificar **patrones de incumplimiento normativo** y su distribución temporal.
3. Analizar la **relación entre caudal de entrada y calidad del efluente**.
4. Generar **reportes diferenciados** para Operaciones y Gestión Ambiental.

## Preguntas de Investigación

- ¿Qué planta presenta mayor eficiencia de remoción de DBO?
- ¿Existe correlación estadística significativa entre el caudal de entrada y la DBO de salida?
- ¿Cuál es la tendencia mensual del cumplimiento normativo?
- ¿Qué limitaciones presenta la calidad del dataset para el análisis?

---

## Estructura del Repositorio

```
aqualimpia/
├── funciones_aqualimpia.py                  # Módulo de funciones reutilizables
├── analisis_aqualimpia.py                   # Flujo principal (9 etapas)
├── dashboard_interactivo.py                 # Módulo de dashboard Plotly
├── dataset_set_A_aguas_residuales.xlsx      # Dataset fuente (200 registros)
├── dashboard_aqualimpia.png                 # Dashboard estático (Matplotlib)
├── dashboard_interactivo_aqualimpia.html    # Dashboard interactivo (Plotly)
├── reporte_area_operaciones.xlsx            # Reporte Área Operaciones
├── reporte_gestion_ambiental.xlsx           # Reporte Gestión Ambiental
├── resumen_plantas.joblib                   # Resultados serializados (Joblib)
└── README.md                                # Documentación técnica
```

---

## Dataset

| Campo | Tipo | Descripción |
|---|---|---|
| fecha_registro | Fecha | Fecha del registro diario |
| planta | Texto | Planta Norte / Sur / Centro |
| caudal_entrada_m3_d | Entero | Caudal de entrada (m³/día) |
| DBO_entrada_mg_L | Entero | DBO de entrada (mg/L) |
| SST_entrada_mg_L | Entero | Sólidos suspendidos totales (mg/L) |
| pH_entrada | Decimal | pH del agua de entrada |
| energia_aeracion_kWh | Decimal | Energía en aireación (kWh) |
| lodos_generados_kg_d | Decimal | Lodos producidos (kg/día) |
| DBO_salida_mg_L | Decimal | DBO del efluente tratado (mg/L) |
| cumplimiento_norma | Entero | 1 = cumple norma, 0 = incumple |

**200 registros | Jul–Oct 2025 | 3 plantas**

---

## Flujo de Trabajo Reproducible

```
Etapa 1 → cargar_datos()                    pandas
Etapa 2 → df.head(), df.info(), describe()  pandas
Etapa 3 → evaluar_calidad_datos()           NumPy + SciPy
Etapa 4 → dropna(), filtros físicos         pandas
Etapa 5 → calcular_eficiencia_dbo()         NumPy
Etapa 6 → analisis_estadistico_planta()     SciPy
Etapa 7 → guardar_resumen_joblib()          Joblib
Etapa 8A→ generar_dashboard_estatico()      Matplotlib
Etapa 8B→ generar_dashboard_interactivo()   Plotly
Etapa 9 → exportar_reportes_excel()         pandas/openpyxl
```

---

## Librerías Utilizadas

| Librería | Versión mín. | Uso |
|---|---|---|
| pandas | 2.0 | Carga, limpieza, exportación Excel |
| numpy | 1.24 | Eficiencia DBO, outliers IQR/z-score |
| scipy | 1.10 | Correlación Pearson, test Shapiro-Wilk |
| joblib | 1.3 | Serialización del resumen estadístico |
| matplotlib | 3.7 | Dashboard estático PNG |
| plotly | 5.0 | Dashboard interactivo HTML |
| openpyxl | 3.1 | Motor escritura Excel |

**Instalar todo:**
```bash
pip install pandas numpy scipy joblib matplotlib plotly openpyxl
```

---

## Instrucciones para ejecutar en Google Colab

```python
# Celda 1: instalar librerías
!pip install scipy joblib plotly openpyxl

# Celda 2: subir archivos al panel de archivos de Colab (ícono 📁)
# Subir: funciones_aqualimpia.py, analisis_aqualimpia.py,
#        dashboard_interactivo.py, dataset_set_A_aguas_residuales.xlsx

# Celda 3: ejecutar el análisis completo
%run analisis_aqualimpia.py
```

---

## Instrucciones Git — Control de Versiones

```bash
# 1. Inicializar repositorio (solo la primera vez)
git init

# 2. Agregar todos los archivos
git add .

# 3. Primer commit
git commit -m "Análisis AquaLimpia S.A. - Ciclo completo Semana 8"

# 4. Conectar con GitHub (reemplaza con tu URL)
git remote add origin https://github.com/[tu-usuario]/aqualimpia-analisis.git

# 5. Subir a GitHub
git push -u origin main

# Para commits futuros (después de cambios):
git add .
git commit -m "Descripción del cambio"
git push
```

---

## Resultados Principales

| Planta | N | Eficiencia DBO (%) | Cumplimiento (%) | Corr. r (p) |
|---|---|---|---|---|
| Planta Centro | 75 | 87.51 ± 3.16 | 22.7% | -0.059 (p=0.612) |
| Planta Sur | 54 | 87.10 ± 2.58 | 29.6% | 0.295 (p=0.030)* |
| Planta Norte | 71 | 86.65 ± 3.31 | 16.9% | 0.135 (p=0.262) |
| **Global** | **200** | **87.09** | **22.5%** | — |

*Correlación estadísticamente significativa (p < 0.05)

**Tasa de incumplimiento global: 77.5%** — principal hallazgo del análisis.

---

## Calidad de los Datos

| Criterio | Resultado |
|---|---|
| Valores nulos | 0 |
| Duplicados | 0 |
| Outliers (z-score > 3) | 4 |
| Outliers (IQR × 1.5) | 9 |
| pH fuera de rango | 0 |
| Incumplimientos norma | 155 / 200 (77.5%) |

---

## Referencias

- IACC (2026). *Aplicación práctica y reflexión ética. Ciencia de Datos. Semana 8.*
- IACC (2026). *Trabajo colaborativo en ciencias de datos. Semana 7.*
- IACC (2026). *Principios y tipos de visualización de datos. Semana 4.*
- Ortega Candel, J. M. (2022). *Big data, machine learning y data science en Python*. https://elibro.net/es/ereader/iacc/230290
- Anthropic. (2026). Claude (versión Sonnet 4.6) [Modelo de lenguaje de gran escala]. https://claude.ai
"Para el desarrollo del presente trabajo se utilizó el asistente de inteligencia artificial Claude (Anthropic, 2026) como herramienta de apoyo en la revisión de código, sugerencias de buenas prácticas y validación de la estructura del proyecto."
---

*Autor: Juan Bobadilla | CIEDT1301 | IACC 2026*
