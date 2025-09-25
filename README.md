# MTG Database (Scryfall + SQLite)

This project builds a local SQLite database of Magic: The Gathering cards using the [Scryfall API](https://scryfall.com/docs/api).

## Setup

1. Clone repo:
   ```bash
   git clone https://github.com/YOURNAME/mtg-db.git
   cd mtg-db

2. Create a virtual environment:
   ```bash
    python -m venv .venv
    source .venv/bin/activate   # macOS/Linux
    .venv\Scripts\Activate      # Windows

3. Install dependencies:
   ```bash
    pip install -r requirements.txt