import requests
import json
import sqlite3
import time

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
    headers = {"User-Agent": "Mozilla/5.0"}
    all_decks = []
    page = 1
    per_page = 24  # Default page size for Moxfield API (can be changed)
    total = None
    while True:
        print(f"Fetching page {page} for user {username}...")
        url = f"https://api2.moxfield.com/v2/users/{username}/decks?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        data = response.json()
        decks = data.get("data", [])
        meta = data.get("meta", {})
        if total is None:
            total = meta.get("total", 0)
        if not decks:
            break

        all_decks.extend(decks)
        # Check if we've fetched all decks
        if len(all_decks) >= total:
            break
        page += 1
        time.sleep(0.5)

    return all_decks

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

def is_deck_legal_in_its_format(deck_data: dict):
    # Check if the deck is legal in its declared format
    # The deck_data is expected to have a 'format' field and a 'formatLegalities' field
    # 'formatLegalities' is a dict with format keys and boolean values
    # Return True if the deck is legal in its declared format, False otherwise
    format_name = deck_data.get("format")
    legalities = deck_data.get("formatLegalities", {})
    if not format_name or not legalities:
        return False
    return legalities.get(format_name, False)

if __name__ == "__main__":
    usernames = ["RIHTZ", "lasagna_man", "noahbfreeman", "k_khangg", "Flynnagin", "TROLLIGANS", "AsianBoi01", "Sethalopod"]  # list of usernames

    for username in usernames:
        print(f"Fetching decks for user {username}...")
        decks = fetch_user_decks(username)
        print(f"Found {len(decks)} decks for user {username}")

        for deck in decks:
            deck_id = deck["publicId"]
            deck_data = fetch_moxfield_deck(deck_id)
            if deck_data:
                if is_deck_legal_in_its_format(deck_data):
                    save_deck(deck_id, username, deck_data)
                else:
                    print(f"Skipping deck {deck_id} for user {username} because it is not legal in its format.")