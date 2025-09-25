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
            # Create two columns for better layout
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.subheader("📊 Database Overview")
                
                # Table selector
                selected_table = st.selectbox(
                    "Select a table to explore:",
                    options=list(schema_info.keys()),
                    format_func=lambda x: f"{x} ({schema_info[x]['row_count']:,} rows)"
                )
                
                if selected_table:
                    table_info = schema_info[selected_table]
                    
                    # Display table information
                    st.metric("Table Name", selected_table)
                    st.metric("Total Rows", f"{table_info['row_count']:,}")
                    st.metric("Total Columns", len(table_info['columns']))
                    
                    st.divider()
                    
                    # Column selector
                    st.subheader("📋 Column Explorer")
                    
                    if table_info['columns']:
                        # Create column dropdown
                        column_names = [col[1] for col in table_info['columns']]
                        selected_column = st.selectbox(
                            "Select a column to explore:",
                            options=column_names,
                            help="Choose a column to see detailed information and sample data"
                        )
                        
                        if selected_column:
                            # Find the selected column info
                            selected_col_info = None
                            for col in table_info['columns']:
                                if col[1] == selected_column:
                                    selected_col_info = col
                                    break
                            
                            if selected_col_info:
                                col_id, col_name, data_type, not_null, default_val, primary_key = selected_col_info
                                
                                # Format data type
                                if not data_type:
                                    data_type = "TEXT"
                                
                                st.markdown(f"**Column: `{col_name}`**")
                                st.markdown(f"- **Type:** `{data_type}`")
                                st.markdown(f"- **Primary Key:** {'Yes' if primary_key else 'No'}")
                                st.markdown(f"- **Not Null:** {'Yes' if not_null else 'No'}")
                                st.markdown(f"- **Default:** `{default_val if default_val else 'None'}`")
                                
                                # Get sample values for this column
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    cur = conn.cursor()
                                    
                                    # Get distinct values
                                    cur.execute(f"SELECT DISTINCT {col_name} FROM {selected_table} WHERE {col_name} IS NOT NULL LIMIT 10")
                                    distinct_values = [row[0] for row in cur.fetchall()]
                                    
                                    # Get value count
                                    cur.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {selected_table}")
                                    distinct_count = cur.fetchone()[0]
                                    
                                    # Get null count
                                    cur.execute(f"SELECT COUNT(*) FROM {selected_table} WHERE {col_name} IS NULL")
                                    null_count = cur.fetchone()[0]
                                    
                                    conn.close()
                                    
                                    st.markdown(f"- **Distinct Values:** {distinct_count:,}")
                                    st.markdown(f"- **Null Values:** {null_count:,}")
                                    
                                    if distinct_values:
                                        st.markdown("**Sample Values:**")
                                        for value in distinct_values[:5]:
                                            st.code(str(value)[:100] + ("..." if len(str(value)) > 100 else ""))
                                        
                                        if len(distinct_values) > 5:
                                            st.markdown(f"... and {len(distinct_values) - 5} more")
                                    
                                except Exception as e:
                                    st.error(f"Error getting column details: {e}")
                            
                            st.divider()
                            
                            # Column-specific queries
                            st.subheader("🔍 Column Queries")
                            
                            # Count values
                            if st.button(f"Count {selected_column} values", key=f"count_{selected_column}_{selected_table}"):
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    cur = conn.cursor()
                                    cur.execute(f"SELECT {selected_column}, COUNT(*) as count FROM {selected_table} GROUP BY {selected_column} ORDER BY count DESC LIMIT 20")
                                    results = cur.fetchall()
                                    conn.close()
                                    
                                    if results:
                                        df = pd.DataFrame(results, columns=[selected_column, 'Count'])
                                        st.dataframe(df, use_container_width=True)
                                    else:
                                        st.info("No data found")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            # Get distinct values
                            if st.button(f"Get distinct {selected_column} values", key=f"distinct_{selected_column}_{selected_table}"):
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    cur = conn.cursor()
                                    cur.execute(f"SELECT DISTINCT {selected_column} FROM {selected_table} WHERE {selected_column} IS NOT NULL ORDER BY {selected_column} LIMIT 50")
                                    results = [row[0] for row in cur.fetchall()]
                                    conn.close()
                                    
                                    if results:
                                        st.write("**Distinct Values:**")
                                        for value in results:
                                            st.code(str(value))
                                    else:
                                        st.info("No distinct values found")
                                except Exception as e:
                                    st.error(f"Error: {e}")
            
            with col_right:
                if selected_table:
                    table_info = schema_info[selected_table]
                    
                    st.subheader(f"📄 {selected_table} - Sample Data")
                    
                    # Sample data with column selection
                    if table_info['sample_data']:
                        column_names = [col[1] for col in table_info['columns']]
                        
                        # Column selection for display
                        selected_columns = st.multiselect(
                            "Select columns to display:",
                            options=column_names,
                            default=column_names[:10] if len(column_names) > 10 else column_names,
                            help="Choose which columns to show in the sample data"
                        )
                        
                        if selected_columns:
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                cur = conn.cursor()
                                
                                # Build query with selected columns
                                columns_str = ", ".join(selected_columns)
                                cur.execute(f"SELECT {columns_str} FROM {selected_table} LIMIT 20")
                                sample_data = cur.fetchall()
                                conn.close()
                                
                                if sample_data:
                                    sample_df = pd.DataFrame(sample_data, columns=selected_columns)
                                    st.dataframe(sample_df, use_container_width=True)
                                    
                                    # Show raw data
                                    with st.expander("🔍 Raw Sample Data"):
                                        for i, row in enumerate(sample_data):
                                            st.markdown(f"**Row {i+1}:**")
                                            st.code(str(row))
                                            st.markdown("---")
                                else:
                                    st.info("No sample data available for selected columns")
                            except Exception as e:
                                st.error(f"Error displaying sample data: {e}")
                        else:
                            st.info("Please select at least one column to display")
                    else:
                        st.info("No sample data available")
                    
                    st.divider()
                    
                    # Advanced table queries
                    st.subheader("⚡ Table Query Generator")
                    
                    # Query type selector
                    query_type = st.selectbox(
                        "Query Type:",
                        ["Basic SELECT", "COUNT", "DISTINCT", "GROUP BY", "Custom"]
                    )
                    
                    if query_type == "Basic SELECT":
                        limit = st.slider("Number of rows:", 1, 100, 10, key=f"basic_limit_{selected_table}")
                        basic_query = f"SELECT * FROM {selected_table} LIMIT {limit};"
                        st.code(basic_query, language='sql')
                        
                        if st.button("Execute Query", key=f"execute_basic_{selected_table}"):
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                df = pd.read_sql_query(basic_query, conn)
                                conn.close()
                                st.dataframe(df, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    elif query_type == "COUNT":
                        count_query = f"SELECT COUNT(*) as total_rows FROM {selected_table};"
                        st.code(count_query, language='sql')
                        
                        if st.button("Execute Count", key=f"execute_count_{selected_table}"):
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                result = pd.read_sql_query(count_query, conn)
                                conn.close()
                                st.metric("Total Rows", result['total_rows'].iloc[0])
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    elif query_type == "DISTINCT":
                        if table_info['columns']:
                            col_for_distinct = st.selectbox(
                                "Column for DISTINCT:",
                                options=[col[1] for col in table_info['columns']],
                                key=f"distinct_col_{selected_table}"
                            )
                            limit = st.slider("Number of distinct values:", 1, 100, 20, key=f"distinct_limit_{selected_table}")
                            distinct_query = f"SELECT DISTINCT {col_for_distinct} FROM {selected_table} LIMIT {limit};"
                            st.code(distinct_query, language='sql')
                            
                            if st.button("Execute DISTINCT", key=f"execute_distinct_{selected_table}"):
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    df = pd.read_sql_query(distinct_query, conn)
                                    conn.close()
                                    st.dataframe(df, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    elif query_type == "GROUP BY":
                        if table_info['columns']:
                            group_col = st.selectbox(
                                "Group by column:",
                                options=[col[1] for col in table_info['columns']],
                                key=f"group_col_{selected_table}"
                            )
                            group_query = f"SELECT {group_col}, COUNT(*) as count FROM {selected_table} GROUP BY {group_col} ORDER BY count DESC LIMIT 20;"
                            st.code(group_query, language='sql')
                            
                            if st.button("Execute GROUP BY", key=f"execute_group_{selected_table}"):
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    df = pd.read_sql_query(group_query, conn)
                                    conn.close()
                                    st.dataframe(df, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    elif query_type == "Custom":
                        custom_query = st.text_area(
                            "Enter custom SQL query:",
                            value=f"SELECT * FROM {selected_table} LIMIT 10;",
                            height=100,
                            key=f"custom_query_{selected_table}"
                        )
                        
                        if st.button("Execute Custom Query", key=f"execute_custom_{selected_table}"):
                            if custom_query.strip():
                                try:
                                    conn = sqlite3.connect(DB_PATH)
                                    df = pd.read_sql_query(custom_query, conn)
                                    conn.close()
                                    st.dataframe(df, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Query error: {e}")
                            else:
                                st.warning("Please enter a query")
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
