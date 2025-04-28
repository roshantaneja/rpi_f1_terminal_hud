import pandas as pd
from rich.table import Table
from rich.panel import Panel
from utils import get_team_color

def create_session_table(session, title, show_time=True, show_position=True):
    """Create a rich table for session results"""
    table = Table(title=title)
    
    # Add columns
    if show_position:
        table.add_column("Pos", justify="right", style="cyan")
    table.add_column("Driver", style="magenta")
    table.add_column("Team", style="green")
    if show_time:
        table.add_column("Time", justify="right", style="yellow")
    
    # Add rows
    for _, result in session.results.iterrows():
        team_color = get_team_color(result['TeamName'])
        
        # Handle NaN position values
        position = result['Position']
        if pd.isna(position):
            position_str = "N/A"
        else:
            position_str = str(int(position))
        
        if show_time:
            time_str = str(result['Time']).split()[-1] if pd.notna(result['Time']) else "N/A"
            if show_position:
                table.add_row(
                    position_str,
                    result['BroadcastName'],
                    f"[{team_color}]{result['TeamName']}[/{team_color}]",
                    time_str
                )
            else:
                table.add_row(
                    result['BroadcastName'],
                    f"[{team_color}]{result['TeamName']}[/{team_color}]",
                    time_str
                )
        else:
            if show_position:
                table.add_row(
                    position_str,
                    result['BroadcastName'],
                    f"[{team_color}]{result['TeamName']}[/{team_color}]"
                )
            else:
                table.add_row(
                    result['BroadcastName'],
                    f"[{team_color}]{result['TeamName']}[/{team_color}]"
                )
    
    return table

def create_standings_table(standings, title):
    """Create a rich table for season standings"""
    table = Table(title=title)
    
    # Add columns
    table.add_column("Pos", justify="right", style="cyan")
    table.add_column("Driver", style="magenta")
    table.add_column("Team", style="green")
    table.add_column("Points", justify="right", style="yellow")
    
    # Add rows
    for _, result in standings.iterrows():
        # Get the constructor name from the flattened response
        constructor_name = result['constructorNames'][0] if isinstance(result['constructorNames'], list) else result['constructorName']
        team_color = get_team_color(constructor_name)
        
        # Get driver name from the flattened response
        driver_name = f"{result['givenName']} {result['familyName']}"
        
        table.add_row(
            str(int(result['position'])),
            driver_name,
            f"[{team_color}]{constructor_name}[/{team_color}]",
            str(int(result['points']))
        )
    
    return table

def create_constructors_table(standings, title):
    """Create a rich table for constructors championship"""
    table = Table(title=title)
    
    # Add columns
    table.add_column("Pos", justify="right", style="cyan")
    table.add_column("Team", style="green")
    table.add_column("Points", justify="right", style="yellow")
    
    # Add rows
    for _, team in standings.iterrows():
        # Get the constructor name from the flattened response
        constructor_name = team['constructorName']
        team_color = get_team_color(constructor_name)
        
        table.add_row(
            str(int(team['position'])),
            f"[{team_color}]{constructor_name}[/{team_color}]",
            str(int(team['points']))
        )
    
    return table

def create_calendar_table(calendar, current_event):
    """Create a rich table for the race calendar with different styling based on race status"""
    table = Table(title="2024 F1 Calendar", show_header=True, header_style="bold magenta")
    
    # Add columns
    table.add_column("Round", style="cyan", justify="right")
    table.add_column("Date", style="cyan")
    table.add_column("Event", style="green")
    table.add_column("Circuit", style="yellow")
    
    # Add rows
    for _, event in calendar.iterrows():
        # Format the date
        date = event.Session5Date  # Race date
        if pd.isna(date):
            date_str = "TBD"
        else:
            try:
                date_str = date.strftime("%b %d")
            except (AttributeError, ValueError):
                date_str = "TBD"
        
        # Determine the style based on race status
        if event.RoundNumber < current_event.RoundNumber:
            # Past races - greyed out
            style = "dim"
        elif event.RoundNumber == current_event.RoundNumber:
            # Current race - highlighted
            style = "bold cyan"
        else:
            # Future races - normal
            style = "white"
        
        table.add_row(
            str(event.RoundNumber),
            date_str,
            f"[{style}]{event.EventName}[/{style}]",
            f"[{style}]{event.Location}[/{style}]"
        )
    
    return table 