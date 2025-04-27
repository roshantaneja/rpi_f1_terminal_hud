import fastf1
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
import pandas as pd
from datetime import datetime, timezone
import time

# Enable FastF1 cache
fastf1.Cache.enable_cache('cache')

# Team color mapping
TEAM_COLORS = {
    'Red Bull Racing': '#0600ef',  # Red Bull blue
    'Ferrari': '#dc0000',          # Ferrari red
    'Mercedes': '#00d2be',         # Mercedes teal
    'McLaren': '#ff8700',          # McLaren orange
    'Aston Martin': '#006f62',     # Aston Martin green
    'Alpine': '#0090ff',           # Alpine blue
    'Williams': '#005aff',         # Williams blue
    'Haas F1 Team': '#ffffff',     # Haas white
    'Kick Sauber': '#52e252',      # Sauber green
    'RB': '#6692ff',              # RB blue
}

def get_team_color(team_name):
    """Get the team color from predefined mapping"""
    return TEAM_COLORS.get(team_name, 'white')  # Default to white if team not found

def get_latest_completed_event():
    """Get the latest completed F1 event"""
    current_year = datetime.now().year
    schedule = fastf1.get_event_schedule(current_year)
    
    # Get current date in UTC to match FastF1's timezone
    current_date = datetime.now(timezone.utc)
    
    # Iterate through events in reverse order (newest first)
    for _, event in schedule.iloc[::-1].iterrows():
        try:
            # Check if the event's date is in the past
            event_date = event.Session5Date  # Race date
            if event_date and event_date.replace(tzinfo=timezone.utc) < current_date:
                race = fastf1.get_session(event.year, event.RoundNumber, 'R')
                # Only load essential data for checking if event is complete
                race.load(telemetry=False, weather=False, messages=False)
                if not race.results.empty:
                    return event  # Return immediately when we find a completed event
        except Exception:
            continue
    
    # If no events found in current year, try previous year
    schedule = fastf1.get_event_schedule(current_year - 1)
    for _, event in schedule.iloc[::-1].iterrows():
        try:
            race = fastf1.get_session(event.year, event.RoundNumber, 'R')
            # Only load essential data for checking if event is complete
            race.load(telemetry=False, weather=False, messages=False)
            if not race.results.empty:
                return event  # Return immediately when we find a completed event
        except Exception:
            continue
    
    raise Exception("No completed events found!")

def get_session_data(event, session_type):
    """Get session data for a specific session type"""
    session = fastf1.get_session(event.year, event.RoundNumber, session_type)
    # Only load essential data for results display
    session.load(telemetry=False, weather=False, messages=False, laps=False)
    return session

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

def get_season_standings(event):
    """Get the current drivers championship standings from Ergast API"""
    ergast = fastf1.ergast.Ergast()
    standings = ergast.get_driver_standings(season=event.year, round=event.RoundNumber)
    # The standings are in the first element of the content list
    return standings.content[0]

def get_constructors_standings(event):
    """Get the current constructors championship standings from Ergast API"""
    ergast = fastf1.ergast.Ergast()
    standings = ergast.get_constructor_standings(season=event.year, round=event.RoundNumber)
    # The standings are in the first element of the content list
    return standings.content[0]

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

def get_next_races(current_event):
    """Get the next 3 races after the current event"""
    current_year = current_event.year
    schedule = fastf1.get_event_schedule(current_year)
    
    # Find the current event in the schedule
    current_round = current_event.RoundNumber
    
    # Get the next 3 races
    next_races = []
    for _, event in schedule.iterrows():
        if event.RoundNumber > current_round:
            next_races.append(event)
            if len(next_races) == 3:
                break
    
    # If we don't have 3 races in the current year, get races from next year
    if len(next_races) < 3:
        next_year = current_year + 1
        next_schedule = fastf1.get_event_schedule(next_year)
        for _, event in next_schedule.iterrows():
            next_races.append(event)
            if len(next_races) == 3:
                break
    
    return next_races

def get_race_calendar(current_event):
    """Get the complete race calendar for the current season"""
    current_year = current_event.year
    schedule = fastf1.get_event_schedule(current_year)
    return schedule

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

def main():
    console = Console()
    
    try:
        # Get latest completed event
        event = get_latest_completed_event()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header"),
            Layout(name="body")
        )
        layout["body"].split_row(
            Layout(name="qualifying"),
            Layout(name="race"),
            Layout(name="drivers"),
            Layout(name="constructors")
        )
        
        # Create header with practice sessions
        header_layout = Layout()
        header_layout.split_row(
            Layout(name="calendar"),
            Layout(name="practice_sessions")
        )
        practice_layout = Layout()
        practice_layout.split_row(
            Layout(name="fp1"),
            Layout(name="fp2"),
            Layout(name="fp3")
        )
        
        # Create calendar
        calendar = get_race_calendar(event)
        calendar_table = create_calendar_table(calendar, event)
        header_layout["calendar"].update(Panel(calendar_table))
        
        # Get session data
        try:
            fp1 = get_session_data(event, 'FP1')
            fp1_table = create_session_table(fp1, "FP1 Results", show_time=False, show_position=False)
            practice_layout["fp1"].update(Panel(fp1_table))
        except Exception as e:
            practice_layout["fp1"].update(Panel("[red]No FP1 data available[/red]"))
        
        try:
            fp2 = get_session_data(event, 'FP2')
            fp2_table = create_session_table(fp2, "FP2 Results", show_time=False, show_position=False)
            practice_layout["fp2"].update(Panel(fp2_table))
        except Exception as e:
            practice_layout["fp2"].update(Panel("[red]No FP2 data available[/red]"))
        
        try:
            fp3 = get_session_data(event, 'FP3')
            fp3_table = create_session_table(fp3, "FP3 Results", show_time=False, show_position=False)
            practice_layout["fp3"].update(Panel(fp3_table))
        except Exception as e:
            practice_layout["fp3"].update(Panel("[red]No FP3 data available[/red]"))
        
        # Get session and standings data
        qualifying = get_session_data(event, 'Q')
        race = get_session_data(event, 'R')
        drivers_standings = get_season_standings(event)
        constructors_standings = get_constructors_standings(event)
        
        # Create tables
        qual_table = create_session_table(qualifying, "Qualifying Results", show_time=False, show_position=True)
        race_table = create_session_table(race, "Race Results", show_time=True, show_position=True)
        drivers_table = create_standings_table(drivers_standings, f"{event.year} Drivers Championship")
        constructors_table = create_constructors_table(constructors_standings, f"{event.year} Constructors Championship")
        
        # Update layouts
        header_layout["practice_sessions"].update(practice_layout)
        layout["header"].update(header_layout)
        layout["qualifying"].update(Panel(qual_table))
        layout["race"].update(Panel(race_table))
        layout["drivers"].update(Panel(drivers_table))
        layout["constructors"].update(Panel(constructors_table))
        
        # Display dashboard
        console.print(layout)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print("[yellow]This might be because:[/yellow]")
        console.print("1. No internet connection")
        console.print("2. No completed events found")
        console.print("3. FastF1 API is temporarily unavailable")
        console.print("\n[yellow]Please try again later.[/yellow]")

if __name__ == "__main__":
    main() 