import pandas as pd
import time
import os
import requests
import dotenv
dotenv.load_dotenv()

try:
    df = pd.read_csv("master_candidates.csv")
    df = df.sample(frac=1, random_state=47).reset_index(drop=True)
except FileNotFoundError:
    pass

target_limits = {
    "Walkable Bridge": 400,
    "Abandoned Industrial": 0,
    "Historic Ruins": 0,
    "Terrain": 0,  # Catches cliffs, ridges, rock formations
    "Mountain Peak": 0,
    "Skatepark / BMX Track": 50,
    "Water Pier": 50,
    "Military Bunker": 0,
    "Tower": 50  # Catches chimneys, water towers, silos
}

# Custom zoom levels for each type (Lower number = wider view)
category_zooms = {
    "Walkable Bridge": 17,
    "Abandoned Industrial": 18,
    "Historic Ruins": 17,
    "Terrain": 16,
    "Mountain Peak": 15,
    "Skatepark / BMX Track": 18,
    "Water Pier": 17,
    "Military Bunker": 18,
    "Tower": 18
}


download_counts = {k: 0 for k in target_limits.keys()}

APPLE_MAPS_TOKEN = os.getenv("APPLE_MAPS_TOKEN")