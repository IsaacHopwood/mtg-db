import streamlit as st
import sqlite3
import pandas as pd
import json
import subprocess
import webbrowser
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MTG Database Explorer",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database path
DB_PATH = "mtg.db"

@st.cache_data
def get_database_info():
    """Get basic database statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get table info
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        
        # Get card count
        card_count = 0
        if 'cards_raw' in tables:
            cur.execute("SELECT COUNT(*) FROM cards_raw")
            card_count = cur.fetchone()[0]
        
        conn.close()
        return tables, card_count
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return [], 0

@st.cache_data
def get_table_schema():
    """Get detailed schema information for all tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        
        schema_info = {}
        
        for table in tables:
            # Get column information
            cur.execute(f"PRAGMA table_info({table})")
            columns = cur.fetchall()
            
            # Get sample data (first 3 rows)
            cur.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cur.fetchall()
            
            # Get row count
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cur.fetchone()[0]
            
            schema_info[table] = {
                'columns': columns,
                'sample_data': sample_data,
                'row_count': row_count
            }
        
        conn.close()
        return schema_info
    except Exception as e:
        st.error(f"Error getting schema: {e}")
        return {}

def refresh_database():
    """Refresh the database by running build_db.py"""
    try:
        # Run the build_db.py script
        result = subprocess.run([
            ".venv\\Scripts\\python.exe", 
            "build_db.py"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            st.success("Database refreshed successfully!")
            st.cache_data.clear()
            return True
        else:
            st.error(f"Error refreshing database: {result.stderr}")
            return False
    except Exception as e:
        st.error(f"Error running refresh: {e}")
        return False

def execute_custom_query(query):
    """Execute a custom SQL query"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

def get_card_by_name(card_name):
    """Get card data by name"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT json FROM cards_raw 
            WHERE json_extract(json, '$.name') LIKE ?
            LIMIT 1
        """, (f"%{card_name}%",))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    except Exception as e:
        st.error(f"Error fetching card: {e}")
        return None

def open_scryfall(card_name=None):
    """Open Scryfall in browser"""
    if card_name:
        url = f"https://scryfall.com/search?q={card_name.replace(' ', '+')}"
    else:
        url = "https://scryfall.com"
    
    webbrowser.open(url)
    st.success(f"Opening Scryfall: {url}")

# Main app
def main():
    st.title("🃏 MTG Database Explorer")
    st.markdown("Explore your local Magic: The Gathering card database")
    
    # Sidebar
    with st.sidebar:
        st.header("Database Info")
        tables, card_count = get_database_info()
        
        if card_count > 0:
            st.success(f"📊 **{card_count:,}** cards in database")
            st.info(f"📋 Tables: {', '.join(tables)}")
        else:
            st.warning("No cards found in database")
        
        st.divider()
        
        # Refresh button
        st.header("Actions")
        if st.button("🔄 Refresh Database", type="primary"):
            with st.spinner("Refreshing database..."):
                refresh_database()
        
        st.divider()
        
        # Database Explorer
        st.header("Database Explorer")
        schema_info = get_table_schema()
        if schema_info:
            st.markdown("**Available Tables:**")
            for table_name, info in schema_info.items():
                st.markdown(f"• **{table_name}** ({info['row_count']:,} rows)")
        else:
            st.warning("No tables found")
        
        st.divider()
        
        # Scryfall button
        st.header("External Links")
        if st.button("🌐 Open Scryfall"):
            open_scryfall()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Quick Search", "📝 Custom Query", "🎯 Card Lookup", "🗄️ Database Explorer", "📊 Database Stats"])
    
    with tab1:
        st.header("Quick Card Search")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input("Search for cards:", placeholder="Enter card name, type, or text...")
        
        with col2:
            search_type = st.selectbox("Search by:", ["Name", "Type", "Oracle Text", "Set"])
        
        if st.button("Search") and search_term:
            with st.spinner("Searching..."):
                if search_type == "Name":
                    query = f"""
                        SELECT 
                            json_extract(json, '$.name') as name,
                            json_extract(json, '$.mana_cost') as mana_cost,
                            json_extract(json, '$.type_line') as type_line,
                            json_extract(json, '$.set') as set_code,
                            json_extract(json, '$.rarity') as rarity
                        FROM cards_raw 
                        WHERE json_extract(json, '$.name') LIKE '%{search_term}%'
                        ORDER BY json_extract(json, '$.name')
                        LIMIT 50
                    """
                elif search_type == "Type":
                    query = f"""
                        SELECT 
                            json_extract(json, '$.name') as name,
                            json_extract(json, '$.mana_cost') as mana_cost,
                            json_extract(json, '$.type_line') as type_line,
                            json_extract(json, '$.set') as set_code
                        FROM cards_raw 
                        WHERE json_extract(json, '$.type_line') LIKE '%{search_term}%'
                        ORDER BY json_extract(json, '$.name')
                        LIMIT 50
                    """
                elif search_type == "Oracle Text":
                    query = f"""
                        SELECT 
                            json_extract(json, '$.name') as name,
                            json_extract(json, '$.mana_cost') as mana_cost,
                            json_extract(json, '$.oracle_text') as oracle_text
                        FROM cards_raw 
                        WHERE json_extract(json, '$.oracle_text') LIKE '%{search_term}%'
                        ORDER BY json_extract(json, '$.name')
                        LIMIT 50
                    """
                else:  # Set
                    query = f"""
                        SELECT 
                            json_extract(json, '$.name') as name,
                            json_extract(json, '$.mana_cost') as mana_cost,
                            json_extract(json, '$.set') as set_code,
                            json_extract(json, '$.set_name') as set_name
                        FROM cards_raw 
                        WHERE json_extract(json, '$.set') LIKE '%{search_term}%' 
                           OR json_extract(json, '$.set_name') LIKE '%{search_term}%'
                        ORDER BY json_extract(json, '$.name')
                        LIMIT 50
                    """
                
                df = execute_custom_query(query)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No cards found matching your search.")
    
    with tab2:
        st.header("Custom SQL Query")
        st.markdown("Write your own SQL queries to explore the database.")
        
        # Example queries
        with st.expander("📚 Example Queries"):
            st.code("""
-- Find all blue instants that draw cards
SELECT 
    json_extract(json, '$.name') as name,
    json_extract(json, '$.mana_cost') as mana_cost,
    json_extract(json, '$.oracle_text') as oracle_text
FROM cards_raw 
WHERE json_extract(json, '$.type_line') LIKE '%Instant%'
  AND json_extract(json, '$.oracle_text') LIKE '%draw%'
  AND json_extract(json, '$.colors') LIKE '%U%'
LIMIT 20;
            """)
            
            st.code("""
-- Find all planeswalkers
SELECT 
    json_extract(json, '$.name') as name,
    json_extract(json, '$.mana_cost') as mana_cost,
    json_extract(json, '$.type_line') as type_line
FROM cards_raw 
WHERE json_extract(json, '$.type_line') LIKE '%Planeswalker%'
ORDER BY json_extract(json, '$.name')
LIMIT 20;
            """)
        
        query = st.text_area(
            "Enter your SQL query:",
            height=200,
            placeholder="SELECT * FROM cards_raw LIMIT 10;"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Execute Query"):
                if query.strip():
                    with st.spinner("Executing query..."):
                        df = execute_custom_query(query)
                        if not df.empty:
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Query executed successfully but returned no results.")
                else:
                    st.warning("Please enter a query.")
    
    with tab3:
        st.header("Card Lookup")
        
        card_name = st.text_input("Enter card name:", placeholder="Lightning Bolt")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Get Card Info"):
                if card_name:
                    card_data = get_card_by_name(card_name)
                    if card_data:
                        st.json(card_data)
                    else:
                        st.warning("Card not found.")
                else:
                    st.warning("Please enter a card name.")
        
        with col2:
            if st.button("Open in Scryfall") and card_name:
                open_scryfall(card_name)
    
    with tab4:
        st.header("🗄️ Database Explorer")
        st.markdown("Explore your database structure, tables, columns, and sample data.")
        
        # Get schema information
        schema_info = get_table_schema()
        
        if schema_info:
            # Table selector
            selected_table = st.selectbox(
                "Select a table to explore:",
                options=list(schema_info.keys()),
                format_func=lambda x: f"{x} ({schema_info[x]['row_count']:,} rows)"
            )
            
            if selected_table:
                table_info = schema_info[selected_table]
                
                # Display table information
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Table Name", selected_table)
                with col2:
                    st.metric("Total Rows", f"{table_info['row_count']:,}")
                with col3:
                    st.metric("Total Columns", len(table_info['columns']))
                
                st.divider()
                
                # Column information
                st.subheader("📋 Column Information")
                
                if table_info['columns']:
                    # Create a DataFrame for better display
                    columns_df = pd.DataFrame(table_info['columns'], 
                                            columns=['Column ID', 'Column Name', 'Data Type', 'Not Null', 'Default Value', 'Primary Key'])
                    
                    # Format the DataFrame
                    columns_df['Data Type'] = columns_df['Data Type'].replace('', 'TEXT')
                    columns_df['Not Null'] = columns_df['Not Null'].map({0: 'No', 1: 'Yes'})
                    columns_df['Primary Key'] = columns_df['Primary Key'].map({0: 'No', 1: 'Yes'})
                    columns_df['Default Value'] = columns_df['Default Value'].fillna('None')
                    
                    st.dataframe(columns_df, use_container_width=True)
                    
                    # Column details in expandable sections
                    with st.expander("🔍 Detailed Column Information"):
                        for col in table_info['columns']:
                            col_id, col_name, data_type, not_null, default_val, primary_key = col
                            
                            # Format data type
                            if not data_type:
                                data_type = "TEXT"
                            
                            st.markdown(f"**{col_name}**")
                            st.markdown(f"- **Type:** `{data_type}`")
                            st.markdown(f"- **Primary Key:** {'Yes' if primary_key else 'No'}")
                            st.markdown(f"- **Not Null:** {'Yes' if not_null else 'No'}")
                            st.markdown(f"- **Default:** `{default_val if default_val else 'None'}`")
                            st.markdown("---")
                else:
                    st.info("No column information available.")
                
                st.divider()
                
                # Sample data
                st.subheader("📄 Sample Data (First 3 Rows)")
                
                if table_info['sample_data']:
                    # Get column names for the sample data
                    column_names = [col[1] for col in table_info['columns']]
                    
                    # Create DataFrame for sample data
                    sample_df = pd.DataFrame(table_info['sample_data'], columns=column_names)
                    
                    # Display sample data
                    st.dataframe(sample_df, use_container_width=True)
                    
                    # Show raw data in expandable section
                    with st.expander("🔍 Raw Sample Data"):
                        for i, row in enumerate(table_info['sample_data']):
                            st.markdown(f"**Row {i+1}:**")
                            st.code(str(row))
                            st.markdown("---")
                else:
                    st.info("No sample data available.")
                
                st.divider()
                
                # Quick query generator
                st.subheader("⚡ Quick Query Generator")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Generate a basic SELECT query
                    basic_query = f"SELECT * FROM {selected_table} LIMIT 10;"
                    st.code(basic_query, language='sql')
                
                with col2:
                    if st.button("Copy Query"):
                        st.code(basic_query, language='sql')
                        st.success("Query copied!")
                
                # Advanced query options
                with st.expander("🔧 Advanced Query Options"):
                    st.markdown("**Count all rows:**")
                    st.code(f"SELECT COUNT(*) FROM {selected_table};", language='sql')
                    
                    st.markdown("**Get distinct values from a column:**")
                    if table_info['columns']:
                        first_col = table_info['columns'][0][1]  # Get first column name
                        st.code(f"SELECT DISTINCT {first_col} FROM {selected_table} LIMIT 20;", language='sql')
                    
                    st.markdown("**Get table structure:**")
                    st.code(f"PRAGMA table_info({selected_table});", language='sql')
        else:
            st.warning("No database schema information available. Please refresh the database.")
    
    with tab5:
        st.header("Database Statistics")
        
        if card_count > 0:
            # Get some basic stats
            stats_query = """
                SELECT 
                    COUNT(*) as total_cards,
                    COUNT(DISTINCT json_extract(json, '$.set')) as total_sets,
                    COUNT(DISTINCT json_extract(json, '$.artist')) as total_artists
                FROM cards_raw;
            """
            
            stats_df = execute_custom_query(stats_query)
            if not stats_df.empty:
                stats = stats_df.iloc[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Cards", f"{stats['total_cards']:,}")
                with col2:
                    st.metric("Total Sets", f"{stats['total_sets']:,}")
                with col3:
                    st.metric("Total Artists", f"{stats['total_artists']:,}")
            
            # Rarity distribution
            st.subheader("Rarity Distribution")
            rarity_query = """
                SELECT 
                    json_extract(json, '$.rarity') as rarity,
                    COUNT(*) as count
                FROM cards_raw 
                WHERE json_extract(json, '$.rarity') IS NOT NULL
                GROUP BY json_extract(json, '$.rarity')
                ORDER BY count DESC;
            """
            
            rarity_df = execute_custom_query(rarity_query)
            if not rarity_df.empty:
                st.bar_chart(rarity_df.set_index('rarity'))
            
            # Recent sets
            st.subheader("Recent Sets")
            recent_sets_query = """
                SELECT 
                    json_extract(json, '$.set_name') as set_name,
                    json_extract(json, '$.set') as set_code,
                    json_extract(json, '$.released_at') as released_at,
                    COUNT(*) as card_count
                FROM cards_raw 
                WHERE json_extract(json, '$.released_at') IS NOT NULL
                GROUP BY json_extract(json, '$.set')
                ORDER BY json_extract(json, '$.released_at') DESC
                LIMIT 10;
            """
            
            recent_sets_df = execute_custom_query(recent_sets_query)
            if not recent_sets_df.empty:
                st.dataframe(recent_sets_df, use_container_width=True)
        else:
            st.warning("No data available. Please refresh the database first.")

if __name__ == "__main__":
    main()
