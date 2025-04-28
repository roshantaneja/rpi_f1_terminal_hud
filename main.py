import fastf1
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from data import (
    get_latest_completed_event,
    get_session_data,
    get_season_standings,
    get_constructors_standings,
    get_race_calendar
)
from track_map import create_track_map
from tables import (
    create_session_table,
    create_standings_table,
    create_constructors_table,
    create_calendar_table
)

def main():
    # Enable FastF1 cache
    fastf1.Cache.enable_cache('cache')
    
    # Create console
    console = Console()
    
    # Get the latest completed event
    event = get_latest_completed_event()
    if not event:
        console.print("[red]No completed events found![/red]")
        return
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header"),
        Layout(name="body"),
        Layout(name="footer")
    )
    
    # Header
    layout["header"].update(Panel(
        Text(f"F1 Dashboard - {event.EventName}", justify="center", style="bold cyan")
    ))
    
    # Body
    body_layout = Layout()
    body_layout.split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Left side - Session results and standings
    left_layout = Layout()
    left_layout.split_column(
        Layout(name="qualifying"),
        Layout(name="race"),
        Layout(name="standings")
    )
    
    # Get session data
    qualifying = get_session_data(event, "Qualifying")
    race = get_session_data(event, "Race")
    
    # Create tables
    qualifying_table = create_session_table(qualifying, "Qualifying Results")
    race_table = create_session_table(race, "Race Results")
    
    # Get standings
    driver_standings = get_season_standings(event)
    constructor_standings = get_constructors_standings(event)
    
    # Create standings tables
    driver_standings_table = create_standings_table(driver_standings, "Drivers' Championship")
    constructor_standings_table = create_constructors_table(constructor_standings, "Constructors' Championship")
    
    # Update left layout
    left_layout["qualifying"].update(qualifying_table)
    left_layout["race"].update(race_table)
    left_layout["standings"].update(driver_standings_table)
    
    # Right side - Track map and calendar
    right_layout = Layout()
    right_layout.split_column(
        Layout(name="track_map"),
        Layout(name="calendar")
    )
    
    # Create track map
    track_map = create_track_map(event)
    
    # Get calendar
    calendar = get_race_calendar(event)
    calendar_table = create_calendar_table(calendar, event)
    
    # Update right layout
    right_layout["track_map"].update(Panel(track_map, title="Track Map"))
    right_layout["calendar"].update(calendar_table)
    
    # Update body layout
    body_layout["left"].update(left_layout)
    body_layout["right"].update(right_layout)
    
    # Update main layout
    layout["body"].update(body_layout)
    
    # Footer
    layout["footer"].update(Panel(
        Text("Data provided by FastF1 and Ergast API", justify="center", style="dim")
    ))
    
    # Print the layout
    console.print(layout)

if __name__ == "__main__":
    main() 