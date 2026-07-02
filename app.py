import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_teams, load_player_stats
from streamlit_image_select import image_select
import streamlit.components.v1 as components
import os

st.set_page_config(page_title="2025/2026 NBA Graphics Creator", layout="wide")

# Diccionario de nombres legibles (Español)
STAT_LABELS = {
    'PTS': 'Puntos',
    'REB': 'Rebotes Totales',
    'AST': 'Asistencias',
    'FG_PCT': '% Tiros de Campo',
    'FG3_PCT': '% Triples',
    'FT_PCT': '% Tiros Libres',
    'FGM': 'Tiros de Campo Anotados',
    'FGA': 'Tiros de Campo Intentados',
    'FG3M': 'Triples Anotados',
    'FG3A': 'Triples Intentados',
    'FTM': 'Tiros Libres Anotados',
    'FTA': 'Tiros Libres Intentados',
    'OREB': 'Rebotes Ofensivos',
    'DREB': 'Rebotes Defensivos',
    'STL': 'Robos',
    'BLK': 'Tapones',
    'TOV': 'Pérdidas',
    'PF': 'Faltas Personales',
    'PLUS_MINUS': '+/-',
    'MIN': 'Minutos',
    'GP': 'Partidos Jugados',
    'AGE': 'Edad',
    'NBA_FANTASY_PTS': 'Puntos Fantasy NBA',
    'DD2': 'Dobles-Dobles',
    'TD3': 'Triples-Dobles',
    'PFD': 'Faltas Recibidas',
    'BLKA': 'Tapones Recibidos',
    'W': 'Victorias',
    'L': 'Derrotas',
    'W_PCT': '% Victorias'
}

def format_stat(stat_code):
    return STAT_LABELS.get(stat_code, stat_code)

st.title("🏀 2025/2026 NBA Graphics Creator & Dashboard")
st.markdown("Explora rosters de los equipos y crea comparaciones personalizadas de estadísticas de jugadores para la temporada NBA 2025-26.")

# Load Data
with st.spinner("Descargando datos de la API de la NBA..."):
    teams_df = load_teams()
    stats_df = load_player_stats(season='2025-26')

if stats_df.empty:
    st.error("No se pudieron cargar los datos. Verifica tu conexión a internet o el estado de la API de la NBA.")
    st.stop()

# Tabs
tab1, tab2 = st.tabs(["Roster Explorer", "Graphics Creator"])

with tab1:
    st.header("Roster Explorer")
    if not teams_df.empty:
        # Create a mapping of Team Name to Team ID
        team_dict = dict(zip(teams_df['full_name'], teams_df['id']))
        sorted_team_names = sorted(list(team_dict.keys()))
        team_ids = [team_dict[name] for name in sorted_team_names]
        
        st.markdown("#### Selecciona un Equipo NBA (Arrastra para girar 🔄)")
        img_urls = [f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg" for tid in team_ids]
        
        # Load the custom 3D carousel component
        carousel_component = components.declare_component(
            "custom_carousel", 
            path=os.path.join(os.path.dirname(__file__), "custom_carousel")
        )
        
        # Pass images and captions, and a default index
        selected_index = carousel_component(images=img_urls, captions=sorted_team_names, default=0)
        
        if selected_index is None:
            selected_index = 0
            
        selected_team_name = sorted_team_names[selected_index]
        selected_team_id = team_ids[selected_index]
        
        # Filter stats for the selected team
        team_roster = stats_df[stats_df['TEAM_ID'] == selected_team_id]
        
        if not team_roster.empty:
            st.subheader(f"Roster de {selected_team_name}")
            # Mostrar tabla básica
            st.dataframe(team_roster[['PLAYER_NAME', 'GP', 'MIN', 'PTS', 'REB', 'AST']], use_container_width=True)
            
            selected_player = st.selectbox("Selecciona un Jugador para ver sus estadísticas:", sorted(team_roster['PLAYER_NAME'].tolist()))
            
            player_stats = team_roster[team_roster['PLAYER_NAME'] == selected_player].iloc[0]
            
            st.subheader(f"Promedios de Temporada: {selected_player}")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Puntos", round(player_stats.get('PTS', 0), 1))
            col2.metric("Rebotes", round(player_stats.get('REB', 0), 1))
            col3.metric("Asistencias", round(player_stats.get('AST', 0), 1))
            col4.metric("% TC", f"{round(player_stats.get('FG_PCT', 0) * 100, 1)}%")
            col5.metric("% 3P", f"{round(player_stats.get('FG3_PCT', 0) * 100, 1)}%")
            
            col6, col7, col8, col9, col10 = st.columns(5)
            col6.metric("Partidos (GP)", int(player_stats.get('GP', 0)))
            col7.metric("Minutos (MIN)", round(player_stats.get('MIN', 0), 1))
            col8.metric("Robos (STL)", round(player_stats.get('STL', 0), 1))
            col9.metric("Tapones (BLK)", round(player_stats.get('BLK', 0), 1))
            col10.metric("Pérdidas (TOV)", round(player_stats.get('TOV', 0), 1))
            
        else:
            st.info("No se encontraron estadísticas para el equipo seleccionado.")
            
with tab2:
    st.header("Graphics Creator")
    st.markdown("Crea gráficos personalizados y exactos para comparar jugadores con estética NBA.")
    
    # Filter valid metrics (numerical and in our label dictionary to avoid weird columns like RANK)
    available_metrics = sorted([c for c in stats_df.columns if c in STAT_LABELS])
    
    # Presets
    presets = {
        "Personalizado (Selección Manual)": None,
        "Eficiencia Anotadora (Puntos vs % TC)": {"x": "FG_PCT", "y": "PTS"},
        "Volumen vs Eficiencia (Tiros Intentados vs % TC)": {"x": "FGA", "y": "FG_PCT"},
        "Creación de Juego (Asistencias vs Pérdidas)": {"x": "TOV", "y": "AST"},
        "Tiro Exterior (Triples Intentados vs % Triples)": {"x": "FG3A", "y": "FG3_PCT"},
        "Todoterrenos (Rebotes vs Puntos)": {"x": "REB", "y": "PTS"}
    }
    
    selected_preset = st.selectbox("Análisis Rápido (Presets):", list(presets.keys()))
    
    # Options layout
    col_x, col_y, col_type = st.columns(3)
    
    preset_x = presets[selected_preset]["x"] if presets[selected_preset] else "MIN"
    preset_y = presets[selected_preset]["y"] if presets[selected_preset] else "PTS"
    
    with col_x:
        x_axis = st.selectbox(
            "Eje X (o Métrica Principal):", 
            available_metrics, 
            index=available_metrics.index(preset_x) if preset_x in available_metrics else 0,
            format_func=format_stat
        )
    with col_y:
        y_axis = st.selectbox(
            "Eje Y:", 
            available_metrics, 
            index=available_metrics.index(preset_y) if preset_y in available_metrics else 1,
            format_func=format_stat
        )
    with col_type:
        chart_type = st.radio("Tipo de Gráfico:", ["Dispersión (Scatter)", "Barras (Top N)", "Cajas (Box Plot) por Equipo"])
        
    # Filters
    st.markdown("#### Filtros")
    team_abbrevs = sorted(stats_df['TEAM_ABBREVIATION'].dropna().unique().tolist())
    selected_teams_filter = st.multiselect("Filtrar por Equipo(s) (Dejar vacío para Todos):", team_abbrevs)
    
    col_min1, col_min2, col_topN = st.columns(3)
    with col_min1:
        min_games = st.slider("Mínimo de Partidos Jugados:", 0, 82, 20)
    with col_min2:
        max_min_avail = int(stats_df['MIN'].max()) if not stats_df.empty and 'MIN' in stats_df.columns and not pd.isna(stats_df['MIN'].max()) else 40
        min_minutes = st.slider("Mínimo de Minutos por Partido:", 0, max_min_avail, 15)
    with col_topN:
        if chart_type == "Barras (Top N)":
            top_n = st.slider("Mostrar Top N Jugadores:", 5, 50, 15)
        
    # Apply filters
    filtered_df = stats_df.copy()
    if selected_teams_filter:
        filtered_df = filtered_df[filtered_df['TEAM_ABBREVIATION'].isin(selected_teams_filter)]
        
    filtered_df = filtered_df[filtered_df['GP'] >= min_games]
    if 'MIN' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['MIN'] >= min_minutes]
        
    if filtered_df.empty:
        st.warning("Ningún jugador cumple con estos filtros. Prueba a bajarlos.")
    else:
        st.metric("Jugadores Mostrados", len(filtered_df))
        
        if chart_type == "Dispersión (Scatter)":
            # For scatter, size by minutes played for context if available
            size_col = 'MIN' if 'MIN' in filtered_df.columns else None
            
            fig = px.scatter(
                filtered_df,
                x=x_axis,
                y=y_axis,
                color='TEAM_ABBREVIATION',
                size=size_col,
                size_max=8,  # Hace las burbujas mucho más pequeñas
                opacity=0.8, # Añade un poco de transparencia para cuando se superponen
                hover_name='PLAYER_NAME',
                hover_data={
                    'TEAM_ABBREVIATION': True,
                    'GP': True,
                    'MIN': True,
                    x_axis: True,
                    y_axis: True
                },
                title=f"Comparación: {format_stat(x_axis)} vs {format_stat(y_axis)}",
                labels={
                    x_axis: format_stat(x_axis), 
                    y_axis: format_stat(y_axis),
                    'TEAM_ABBREVIATION': 'Equipo',
                    'GP': 'Partidos',
                    'MIN': 'Minutos'
                }
            )
        elif chart_type == "Barras (Top N)":
            # Sort and slice
            top_df = filtered_df.sort_values(by=x_axis, ascending=False).head(top_n)
            
            fig = px.bar(
                top_df,
                x='PLAYER_NAME',
                y=x_axis,
                color='TEAM_ABBREVIATION',
                hover_name='PLAYER_NAME',
                hover_data={
                    'TEAM_ABBREVIATION': True,
                    'GP': True,
                    'MIN': True,
                    x_axis: True
                },
                title=f"Top {top_n} Jugadores en {format_stat(x_axis)}",
                labels={
                    x_axis: format_stat(x_axis),
                    'PLAYER_NAME': 'Jugador',
                    'TEAM_ABBREVIATION': 'Equipo',
                    'GP': 'Partidos',
                    'MIN': 'Minutos'
                }
            )
            # Ensure proper ordering of bars
            fig.update_layout(xaxis={'categoryorder':'total descending'})
            
        else: # Box Plot
            fig = px.box(
                filtered_df,
                x='TEAM_ABBREVIATION',
                y=x_axis,
                color='TEAM_ABBREVIATION',
                hover_name='PLAYER_NAME',
                hover_data={
                    'TEAM_ABBREVIATION': False,
                    'GP': True,
                    'MIN': True,
                    x_axis: True
                },
                title=f"Distribución de {format_stat(x_axis)} por Equipo",
                labels={
                    x_axis: format_stat(x_axis),
                    'TEAM_ABBREVIATION': 'Equipo',
                    'GP': 'Partidos',
                    'MIN': 'Minutos'
                }
            )
            fig.update_layout(xaxis={'categoryorder':'mean descending'})

        # Mejoras estéticas
        fig.update_layout(
            template='plotly_dark',
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode="closest",
            font=dict(family="Arial, sans-serif", size=12),
            title_font=dict(size=20, family="Arial Black, sans-serif", color="white"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        # Añadir grid lines sutiles
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        
        st.plotly_chart(fig, use_container_width=True)
