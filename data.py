import json
import os
from datetime import datetime

DATA_FILE = "roulette_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(data, user_id: str):
    """S'assure que l'utilisateur a une entrée dans les données."""
    if user_id not in data:
        data[user_id] = {
            "current_team": [],
            "previous_team": [],
            "last_used": None,
            "history": []
        }

def get_user_data(data, user_id: str):
    ensure_user(data, user_id)
    return data[user_id]

def set_last_used(data, user_id: str):
    ensure_user(data, user_id)
    data[user_id]["last_used"] = datetime.utcnow().isoformat()

def get_last_used(data, user_id: str):
    ensure_user(data, user_id)
    return data[user_id]["last_used"]

def set_current_team(data, user_id: str, team: list):
    ensure_user(data, user_id)
    data[user_id]["previous_team"] = data[user_id].get("current_team", [])
    data[user_id]["current_team"] = team
    # Ajoute la team au history, en évitant les doublons facultativement
    data[user_id]["history"] = data[user_id].get("history", []) + team

def get_current_team(data, user_id: str):
    ensure_user(data, user_id)
    return data[user_id].get("current_team", [])

def get_previous_team(data, user_id: str):
    ensure_user(data, user_id)
    return data[user_id].get("previous_team", [])

def get_history(data, user_id: str):
    ensure_user(data, user_id)
    return data[user_id].get("history", [])
