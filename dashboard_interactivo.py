# =============================================================
# ARCHIVO: dashboard_interactivo.py
# PROYECTO: AquaLimpia S.A. — Dashboard Interactivo con Plotly
# ASIGNATURA: Ciencia de Datos — CIEDT1301 — Semana 4 y 8
# AUTOR: Juan Bobadilla
# DESCRIPCIÓN: Genera un dashboard interactivo en HTML usando
#              Plotly (librería vista en Semana 4). El usuario
#              puede hacer hover, zoom, filtrar por planta y
#              cambiar la métrica del gráfico de tendencia.
# =============================================================

# plotly.graph_objects: control avanzado de gráficos
import plotly.graph_objects as go

# make_subplots: crea figuras con múltiples subgráficos
from plotly.subplots import make_subplots

import pandas as pd
import numpy as np


# =============================================================
# FUNCIÓN PRINCIPAL — importable desde analisis_aqualimpia.py
# =============================================================
def generar_dashboard_interactivo(df, ruta='dashboard_interactivo_aqualimpia.html'):
    """
    Genera un dashboard interactivo con Plotly y lo guarda como HTML.
    Funciona en cualquier navegador sin instalaciones adicionales.

    El usuario puede:
    - Hacer hover sobre barras/puntos para ver datos exactos
    - Hacer zoom en cualquier gráfico
    - Filtrar plantas desde la leyenda
    - Cambiar la métrica del gráfico de tendencia con los botones

    Parámetros:
        df (pd.DataFrame): dataset con eficiencia_dbo_pct calculada
        ruta (str): ruta donde guardar el archivo HTML

    Retorna:
        str: ruta del archivo generado
    """
    # Colores consistentes por planta
    COLORES = {
        'Planta Norte' : '#1D9E75',
        'Planta Sur'   : '#3B8BD4',
        'Planta Centro': '#E85D24'
    }
    PLANTAS = list(df['planta'].unique())

    # Prepara columna de mes para agrupaciones temporales
    df = df.copy()
    df['mes_str'] = pd.to_datetime(df['fecha_registro']).dt.strftime('%Y-%m')

    # ── Resumen por planta ────────────────────────────────────
    resumen = df.groupby('planta').agg(
        eficiencia_media   = ('eficiencia_dbo_pct', 'mean'),
        eficiencia_std     = ('eficiencia_dbo_pct', 'std'),
        cumplimiento_pct   = ('cumplimiento_norma', 'mean'),
        dbo_salida_media   = ('DBO_salida_mg_L',    'mean'),
        n_registros        = ('planta',             'count')
    ).reset_index()
    resumen['cumplimiento_pct'] = (resumen['cumplimiento_pct'] * 100).round(1)
    resumen['eficiencia_media'] = resumen['eficiencia_media'].round(2)

    # ── Evolución mensual ─────────────────────────────────────
    mensual = df.groupby(['mes_str','planta']).agg(
        dbo_salida   = ('DBO_salida_mg_L',    'mean'),
        eficiencia   = ('eficiencia_dbo_pct', 'mean'),
        cumplimiento = ('cumplimiento_norma', 'mean')
    ).reset_index()
    mensual['cumplimiento'] = (mensual['cumplimiento'] * 100).round(1)

    # ── Crea la cuadrícula 2×3 con spec para torta en [2,3] ──
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            '📊 Eficiencia DBO por planta',
            '✅ Cumplimiento normativo (%)',
            '🔵 DBO salida vs Caudal entrada',
            '📦 Distribución eficiencia DBO',
            '📈 Evolución mensual (cambia métrica abajo)',
            '🍩 Registros por planta'
        ),
        specs=[
            [{"type": "xy"},     {"type": "xy"},     {"type": "xy"}],
            [{"type": "xy"},     {"type": "xy"},     {"type": "domain"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    # ── G1: Barras — Eficiencia DBO ───────────────────────────
    for _, row in resumen.iterrows():
        fig.add_trace(go.Bar(
            name=row['planta'],
            x=[row['planta']],
            y=[row['eficiencia_media']],
            error_y=dict(type='data', array=[row['eficiencia_std']], visible=True),
            marker_color=COLORES[row['planta']],
            hovertemplate=(
                f"<b>{row['planta']}</b><br>"
                f"Eficiencia: {row['eficiencia_media']:.1f}%<br>"
                f"Std: ±{row['eficiencia_std']:.1f}%<br>"
                f"N: {int(row['n_registros'])}<extra></extra>"
            ),
            showlegend=True, legendgroup=row['planta']
        ), row=1, col=1)

    fig.add_hline(y=85, line_dash='dash', line_color='red',
                  annotation_text='Mínimo 85%', row=1, col=1)

    # ── G2: Barras — Cumplimiento normativo ───────────────────
    for _, row in resumen.iterrows():
        fig.add_trace(go.Bar(
            name=row['planta'],
            x=[row['planta']],
            y=[row['cumplimiento_pct']],
            marker_color=COLORES[row['planta']],
            hovertemplate=(
                f"<b>{row['planta']}</b><br>"
                f"Cumplimiento: {row['cumplimiento_pct']}%<extra></extra>"
            ),
            showlegend=False, legendgroup=row['planta']
        ), row=1, col=2)

    fig.add_hline(y=50, line_dash='dot', line_color='orange',
                  annotation_text='Umbral 50%', row=1, col=2)

    # ── G3: Dispersión — DBO salida vs Caudal ─────────────────
    for p, c in COLORES.items():
        sub = df[df['planta'] == p]
        fig.add_trace(go.Scatter(
            name=p, x=sub['caudal_entrada_m3_d'], y=sub['DBO_salida_mg_L'],
            mode='markers',
            marker=dict(color=c, size=7, opacity=0.6),
            customdata=sub[['eficiencia_dbo_pct']].values,
            hovertemplate=(
                f"<b>{p}</b><br>"
                "Caudal: %{x:,.0f} m³/d<br>"
                "DBO salida: %{y:.1f} mg/L<br>"
                "Eficiencia: %{customdata[0]:.1f}%<extra></extra>"
            ),
            showlegend=False, legendgroup=p
        ), row=1, col=3)

    fig.add_hline(y=35, line_dash='dash', line_color='red',
                  annotation_text='Límite 35 mg/L', row=1, col=3)

    # ── G4: Boxplot — Distribución eficiencia DBO ─────────────
    for p, c in COLORES.items():
        sub = df[df['planta'] == p]
        fig.add_trace(go.Box(
            name=p, y=sub['eficiencia_dbo_pct'],
            marker_color=c, boxpoints='all', jitter=0.3, pointpos=-1.8,
            hovertemplate=f"<b>{p}</b><br>Eficiencia: %{{y:.1f}}%<extra></extra>",
            showlegend=False, legendgroup=p
        ), row=2, col=1)

    fig.add_hline(y=85, line_dash='dash', line_color='red', row=2, col=1)

    # ── G5: Líneas — Evolución mensual DBO salida ─────────────
    for p, c in COLORES.items():
        sub = mensual[mensual['planta'] == p]
        fig.add_trace(go.Scatter(
            name=p, x=sub['mes_str'], y=sub['dbo_salida'],
            mode='lines+markers',
            marker=dict(size=8), line=dict(color=c, width=2.5),
            hovertemplate=f"<b>{p}</b><br>Mes: %{{x}}<br>DBO: %{{y:.1f}} mg/L<extra></extra>",
            showlegend=False, legendgroup=p
        ), row=2, col=2)

    fig.add_hline(y=35, line_dash='dash', line_color='red',
                  annotation_text='Norma 35 mg/L', row=2, col=2)

    # ── G6: Torta — Registros por planta ─────────────────────
    fig.add_trace(go.Pie(
        labels=resumen['planta'],
        values=resumen['n_registros'],
        marker_colors=[COLORES[p] for p in resumen['planta']],
        hole=0.4,
        hovertemplate="<b>%{label}</b><br>Registros: %{value}<br>%{percent}<extra></extra>",
        showlegend=False, textinfo='label+percent'
    ), row=2, col=3)

    # ── Botones para cambiar métrica en G5 ────────────────────
    # Los índices de las trazas del gráfico 5 (líneas) son 12, 13, 14
    fig.update_layout(
        title=dict(
            text=(
                '<b>AquaLimpia S.A. — Dashboard Interactivo</b>'
                '<br><sup>Hover: datos exactos | Zoom: arrastra | '
                'Leyenda: filtra plantas | Botones: cambia métrica</sup>'
            ),
            x=0.5, font=dict(size=16)
        ),
        height=850,
        template='plotly_white',
        legend=dict(title='<b>Plantas</b>', orientation='h',
                    yanchor='bottom', y=1.01, xanchor='right', x=1),
        updatemenus=[dict(
            type='buttons', direction='right',
            x=0.38, y=-0.06, bgcolor='#F0F0F0', bordercolor='#CCCCCC',
            buttons=[
                dict(label='📉 DBO Salida', method='update',
                     args=[{'y': [mensual[mensual['planta']==p]['dbo_salida'].tolist()
                                  for p in PLANTAS]},
                           {'yaxis6.title.text': 'DBO salida (mg/L)'}]),
                dict(label='⚡ Eficiencia DBO', method='update',
                     args=[{'y': [mensual[mensual['planta']==p]['eficiencia'].tolist()
                                  for p in PLANTAS]},
                           {'yaxis6.title.text': 'Eficiencia (%)'}]),
                dict(label='✅ Cumplimiento', method='update',
                     args=[{'y': [mensual[mensual['planta']==p]['cumplimiento'].tolist()
                                  for p in PLANTAS]},
                           {'yaxis6.title.text': 'Cumplimiento (%)'}]),
            ]
        )],
        annotations=[dict(
            text='<b>Cambiar métrica tendencia:</b>',
            x=0.05, y=-0.06, xref='paper', yref='paper',
            showarrow=False, font=dict(size=11)
        )]
    )

    # Etiquetas de ejes
    fig.update_yaxes(title_text='Eficiencia (%)',    row=1, col=1)
    fig.update_yaxes(title_text='Cumplimiento (%)',  row=1, col=2)
    fig.update_yaxes(title_text='DBO salida (mg/L)', row=1, col=3)
    fig.update_xaxes(title_text='Caudal (m³/d)',     row=1, col=3)
    fig.update_yaxes(title_text='Eficiencia (%)',    row=2, col=1)
    fig.update_yaxes(title_text='DBO salida (mg/L)', row=2, col=2)
    fig.update_xaxes(title_text='Mes',               row=2, col=2)

    # Guarda el HTML con toda la librería incluida (funciona sin internet)
    fig.write_html(
        ruta,
        include_plotlyjs='cdn',
        full_html=True,
        config={
            'displayModeBar': True,
            'toImageButtonOptions': {
                'format': 'png', 'filename': 'dashboard_aqualimpia',
                'height': 900, 'width': 1400, 'scale': 2
            }
        }
    )
    print(f"Dashboard interactivo guardado: {ruta}")
    return ruta

