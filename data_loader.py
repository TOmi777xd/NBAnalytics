import pandas as pd
import streamlit as st
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguedashplayerstats

@st.cache_data(ttl=86400)
def load_teams():
    """
    Fetch all 30 NBA franchises.
    """
    try:
        nba_teams = teams.get_teams()
        df_teams = pd.DataFrame(nba_teams)
        return df_teams
    except Exception as e:
        st.error(f"Error fetching teams: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def load_player_stats(season='2025-26'):
    """
    Fetch player stats for the specified season.
    """
    try:
        # Pidiendo 'Totals' para obtener precisión exacta y evitar el redondeo de la API a 1 decimal
        # Esto soluciona que los jugadores se vean en filas "cuadriculadas" en el scatter plot
        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            per_mode_detailed='Totals'
        )
        df = stats.get_data_frames()[0]
        
        # Columnas que necesitan promediarse por partido para igualar a 'PerGame' pero con máxima precisión
        cols_to_avg = [
            'MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 
            'REB', 'AST', 'TOV', 'STL', 'BLK', 'BLKA', 'PF', 'PFD', 'PTS', 
            'PLUS_MINUS', 'NBA_FANTASY_PTS', 'DD2', 'TD3'
        ]
        
        # Evitar división por cero
        valid_gp = df['GP'] > 0
        for col in cols_to_avg:
            if col in df.columns:
                df.loc[valid_gp, col] = df.loc[valid_gp, col] / df.loc[valid_gp, 'GP']
                
        return df
    except Exception as e:
        st.error(f"Error fetching player stats: {e}")
        return pd.DataFrame()
