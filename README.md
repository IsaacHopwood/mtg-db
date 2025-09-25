# 🃏 MTG Database Explorer

A comprehensive Magic: The Gathering card database with a Streamlit web interface. This project builds a local SQLite database using the [Scryfall API](https://scryfall.com/docs/api) and provides an interactive web app for exploring MTG cards.

## ✨ Features

- **🗄️ Dual Database Structure**: Raw JSON storage + structured tables for optimal performance
- **🌐 Streamlit Web Interface**: Interactive web app with multiple tabs
- **🔍 Advanced Search**: Search by name, type, oracle text, or set
- **📝 Custom SQL Queries**: Write and execute your own SQL queries
- **🗄️ Database Explorer**: Dynamic table/column browser with data types
- **🔄 Refresh Data**: Update database with latest Scryfall data
- **🌐 Scryfall Integration**: Direct links to Scryfall for detailed card info
- **📊 Statistics & Charts**: Visual database statistics and card distributions
- **⚡ Quick Query Generator**: Auto-generate SQL queries for any table

## 🚀 Quick Start

### 1. Setup Environment

**Windows:**
```cmd
py -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Build Database
```bash
# Windows
.venv\Scripts\python.exe build_db.py

# macOS/Linux
python build_db.py
```

### 4. Launch Web App
```bash
# Windows
.venv\Scripts\streamlit.exe run streamlit_app.py

# macOS/Linux
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📁 Project Structure

```
mtg-db/
├── streamlit_app.py          # Main Streamlit web application
├── build_db.py              # Database builder with dual-table structure
├── create_cards_table.sql   # SQL schema for structured cards table
├── query_cards.py           # Example query script
├── moxfield_pull.py         # Moxfield deck data fetcher
├── requirements.txt         # Python dependencies
├── mtg.db                   # SQLite database (created after build)
└── README.md               # This file
```

## 🗄️ Database Structure

### Tables Created:
- **`cards_raw`**: Raw JSON data from Scryfall API
- **`cards`**: Structured table with 50+ extracted columns including:
  - Basic info (name, mana_cost, type_line, oracle_text)
  - Images (small, normal, large, art_crop)
  - Pricing (USD, EUR, TIX)
  - Legality (Standard, Modern, Commander)
  - Set information and metadata

## 🌐 Web Interface Tabs

### 🔍 Quick Search
- Search cards by name, type, oracle text, or set
- Real-time filtering and results display

### 📝 Custom Query
- Write and execute custom SQL queries
- Example queries included
- Syntax highlighting and error handling

### 🎯 Card Lookup
- Detailed card information display
- Direct Scryfall integration
- JSON data viewer

### 🗄️ Database Explorer
- **Dynamic table browser** with row counts
- **Column information** with data types and constraints
- **Sample data** preview (first 3 rows)
- **Quick query generator** for any table
- **Advanced query options** (COUNT, DISTINCT, PRAGMA)

### 📊 Database Stats
- Card count and distribution statistics
- Rarity distribution charts
- Recent sets information
- Visual analytics

## 🔧 Usage Examples

### Search for Cards
```sql
-- Find all blue instants that draw cards
SELECT name, mana_cost, oracle_text
FROM cards
WHERE type_line LIKE '%Instant%'
  AND oracle_text LIKE '%draw%'
  AND colors LIKE '%U%'
LIMIT 20;
```

### Get Card Statistics
```sql
-- Rarity distribution
SELECT rarity, COUNT(*) as count
FROM cards
GROUP BY rarity
ORDER BY count DESC;
```

### Find Recent Cards
```sql
-- Latest cards from recent sets
SELECT name, set_name, released_at
FROM cards
WHERE released_at >= '2024-01-01'
ORDER BY released_at DESC
LIMIT 10;
```

## 🛠️ Advanced Features

### Refresh Database
Use the "🔄 Refresh Database" button in the web app to update with latest Scryfall data.

### Custom Queries
The Database Explorer tab provides:
- Auto-generated SELECT queries
- COUNT and DISTINCT examples
- Table structure queries (PRAGMA)

### Scryfall Integration
- Click "🌐 Open Scryfall" to browse cards online
- Direct links from card lookups
- Seamless integration with official MTG database

## 📊 Performance

- **Database Size**: ~750MB for complete MTG card database
- **Query Speed**: Structured tables provide fast queries
- **Memory Usage**: Optimized for local development
- **Caching**: Streamlit caching for improved performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [Scryfall](https://scryfall.com/) for the amazing MTG API
- [Streamlit](https://streamlit.io/) for the web framework
- [Wizards of the Coast](https://company.wizards.com/) for Magic: The Gathering