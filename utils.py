# Team color mapping
TEAM_COLORS = {
    'Red Bull Racing': '#0600ef',  # Red Bull blue
    'Red Bull': '#0600ef',         # Red Bull blue
    'Ferrari': '#dc0000',          # Ferrari red
    'Mercedes': '#00d2be',         # Mercedes teal
    'McLaren': '#ff8700',          # McLaren orange
    'Aston Martin': '#006f62',     # Aston Martin green
    'Alpine': '#0090ff',           # Alpine blue
    'Alpine F1 Team': '#0090ff',   # Alpine blue
    'Williams': '#005aff',         # Williams blue
    'Haas F1 Team': '#E6002B',     # Haas red
    'Kick Sauber': '#52e252',      # Sauber green
    'Sauber': '#52e252',           # Sauber green
    'RB': '#6692ff',               # RB blue
}

def get_team_color(team_name):
    """Get the team color from predefined mapping"""
    return TEAM_COLORS.get(team_name, 'white')  # Default to white if team not found 