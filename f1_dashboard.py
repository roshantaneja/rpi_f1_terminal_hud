import fastf1
import matplotlib.pyplot as plt
import io
from PIL import Image, ImageDraw
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
import pandas as pd
from datetime import datetime, timezone
import time
import numpy as np
from matplotlib.collections import LineCollection

# Enable FastF1 cache
fastf1.Cache.enable_cache('cache')

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

def image_to_ascii(image, width=40, height=20):
    """Convert an image to ASCII art with specified dimensions"""
    # Resize image to desired dimensions
    image = image.resize((width, height))
    
    # Convert to grayscale
    image = image.convert('L')
    
    # ASCII characters from darkest to lightest
    ascii_chars = " .:-=+*#%@"
    
    # Convert each pixel to ASCII character
    pixels = image.getdata()
    ascii_str = ""
    for i, pixel in enumerate(pixels):
        # Map pixel value (0-255) to ASCII character index
        char_index = int(pixel / 255 * (len(ascii_chars) - 1))
        ascii_str += ascii_chars[char_index]
        if (i + 1) % width == 0:
            ascii_str += "\n"
    
    return ascii_str

def rotate_points(xy, angle):
    """Rotate points around the origin by given angle in radians"""
    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    rotation_matrix = np.array([[cos_angle, -sin_angle], [sin_angle, cos_angle]])
    return np.dot(xy, rotation_matrix)

def find_optimal_rotation(x, y, num_angles=36):
    """Find the rotation angle that maximizes the track's dimensions"""
    angles = np.linspace(0, np.pi, num_angles)
    max_dimension = 0
    best_angle = 0
    
    for angle in angles:
        rotated = rotate_points(np.column_stack((x, y)), angle)
        x_rot, y_rot = rotated[:, 0], rotated[:, 1]
        dimension = (x_rot.max() - x_rot.min()) * (y_rot.max() - y_rot.min())
        if dimension > max_dimension:
            max_dimension = dimension
            best_angle = angle
            
    return best_angle

def create_track_map(event):
    """Create a track map visualization for the given event"""
    try:
        # Get the session data
        session = fastf1.get_session(event.year, event.RoundNumber, 'R')
        # Load the session data with all required information
        session.load(telemetry=True, laps=True, weather=False, messages=False)
        
        # Get the fastest lap
        lap = session.laps.pick_fastest()
        if lap is None:
            raise Exception("No lap data available")
            
        # Get position data from the lap
        pos = lap.get_pos_data()
        if pos is None:
            raise Exception("No position data available")
            
        # Get track coordinates from position data
        x = pos['X'].to_numpy()
        y = pos['Y'].to_numpy()
        
        if len(x) == 0 or len(y) == 0:
            raise Exception("No track coordinates available")
            
        # Create a PIL image
        width, height = 80, 40  # ASCII art dimensions
        image = Image.new('1', (width, height), 1)  # 1 for white background
        draw = ImageDraw.Draw(image)
        
        # Calculate the range of coordinates
        x_range = x.max() - x.min()
        y_range = y.max() - y.min()
        
        # Calculate scaling factors
        x_scale = (width - 2) / x_range  # Leave 1 pixel margin on each side
        y_scale = (height - 2) / y_range  # Leave 1 pixel margin on each side
        scale = min(x_scale, y_scale)
        
        # Draw the track
        points = []
        for i in range(len(x)):
            # Scale the points to fit the image
            px = int((x[i] - x.min()) * scale + 1)  # Add 1 pixel margin
            py = int((y[i] - y.min()) * scale + 1)  # Add 1 pixel margin
            points.append((px, py))
        
        # Draw the track line
        if len(points) > 1:
            draw.line(points, fill=0, width=1)  # 0 for black line
        
        # Convert to ASCII art
        ascii_art = []
        for y in range(height):
            line = []
            for x in range(width):
                if image.getpixel((x, y)) == 0:  # Black pixel
                    line.append('#')
                else:  # White pixel
                    line.append(' ')
            ascii_art.append(''.join(line))
        
        return '\n'.join(ascii_art)
        
    except Exception as e:
        print(f"Error creating track map: {str(e)}")  # Debug print
        raise  # Re-raise the exception to be caught by the main function

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
            Layout(name="left_header", ratio=2),
            Layout(name="practice_sessions", ratio=3)
        )
        
        # Split left header into calendar and track map
        left_header = Layout()
        left_header.split_row(
            Layout(name="calendar"),
            Layout(name="track_map")
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
        left_header["calendar"].update(Panel(calendar_table))
        
        # Create track map
        try:
            track_map = create_track_map(event)
            # Add some padding around the ASCII art
            track_map_str = "\n" + track_map + "\n"
            left_header["track_map"].update(Panel(track_map_str, title=f"Circuit: {event.Location}"))
        except Exception as e:
            error_msg = f"[red]No track map available[/red]\n[yellow]Error: {str(e)}[/yellow]"
            left_header["track_map"].update(Panel(error_msg, title=f"Circuit: {event.Location}"))
        
        # Update left header in main header layout
        header_layout["left_header"].update(left_header)

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