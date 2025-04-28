import fastf1
from datetime import datetime, timezone
import pandas as pd

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
                    return event  # Return the event row
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
                return event  # Return the event row
        except Exception:
            continue
    
    return None  # Return None if no completed events found

def get_session_data(event, session_type):
    """Get session data for a specific session type"""
    session = fastf1.get_session(event.year, event.RoundNumber, session_type)
    # Only load essential data for results display
    session.load(telemetry=False, weather=False, messages=False, laps=False)
    return session

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