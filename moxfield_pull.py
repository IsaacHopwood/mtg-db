import requests
import json
import sqlite3

DB_PATH = "mtg.db"  # adjust path if needed

def fetch_moxfield_deck(deck_id: str):
    url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def fetch_user_decks(username: str):
    url = f"https://api2.moxfield.com/v2/users/{username}/decks"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []

def save_deck(deck_id: str, username: str, deck_data: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS moxfield_raw (
            deck_id TEXT PRIMARY KEY,
            username TEXT,
            data JSON
        )
    """)
    c.execute("""
        INSERT OR REPLACE INTO moxfield_raw (deck_id, username, data) VALUES (?, ?, ?)
    """, (deck_id, username, json.dumps(deck_data)))
    conn.commit()
    conn.close()
    print(f"Deck {deck_id} (user {username}) saved to database.")

if __name__ == "__main__":
    username = "RIHTZ"

    decks = fetch_user_decks(username)
    print(f"Found {len(decks)} decks for user {username}")

    for deck in decks:
        deck_id = deck["publicId"]   # deck id key from the API response
        deck_data = fetch_moxfield_deck(deck_id)
        if deck_data:
            save_deck(deck_id, username, deck_data)