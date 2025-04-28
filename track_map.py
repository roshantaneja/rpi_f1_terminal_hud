import fastf1
import numpy as np
from PIL import Image, ImageDraw

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