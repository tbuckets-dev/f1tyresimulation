import fastf1
import pandas as pd
from datetime import datetime


def collect_race_data(year, race_name):
    """Collect tire degradation data for a specific race"""

    # Load race session
    session = fastf1.get_session(year, race_name, "R")
    session.load()

    # Get laps with tire data
    laps = session.laps

    # Extract relevant columns
    tire_data = laps[
        [
            "Driver",
            "LapNumber",
            "LapTime",
            "Compound",
            "TyreLife",
            "Stint",
            "TrackStatus",
            "IsPersonalBest",
        ]
    ].copy()

    # Add race metadata
    tire_data["Year"] = year
    tire_data["Race"] = race_name
    tire_data["Circuit"] = session.event["Location"]

    # Get weather data
    weather = session.weather_data
    tire_data = tire_data.merge(
        weather[["Time", "AirTemp", "TrackTemp", "Humidity"]],
        left_on="Time",
        right_on="Time",
        how="left",
    )

    return tire_data


# Collect data for multiple races
races_2023 = [
    "Bahrain",
    "Saudi Arabia",
    "Australia",
    "Azerbaijan",
    "Miami",
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Great Britain",
    "Hungary",
    "Belgium",
    "Netherlands",
    "Italy",
    "Singapore",
    "Japan",
    "Qatar",
    "United States",
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Abu Dhabi",
]

all_data = []
for race in races_2023:
    print(f"Collecting data for {race}...")
    race_data = collect_race_data(2023, race)
    all_data.append(race_data)

# Combine and save
df = pd.concat(all_data, ignore_index=True)
df.to_csv("f1_tire_data_2023.csv", index=False)
