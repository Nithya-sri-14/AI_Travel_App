import sqlite3
import mysql.connector
import os
import logging
from backend import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_connection")

def get_connection():
    """
    Returns a database connection and a boolean indicating if it's SQLite.
    If MySQL connection fails, it will fall back to SQLite automatically.
    """
    if config.DB_TYPE == "mysql":
        try:
            conn = mysql.connector.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE
            )
            return conn, False
        except Exception as e:
            logger.warning(f"MySQL connection failed: {e}. Falling back to SQLite database at {config.SQLITE_DB_PATH}")
            # Fallback to SQLite
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            return conn, True
    else:
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        return conn, True

def execute_query(query, params=None):
    """
    Executes a write query (INSERT, UPDATE, DELETE).
    Automatically handles parameter placeholders differences between MySQL (%s) and SQLite (?).
    """
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    if is_sqlite:
        # SQLite uses '?' placeholder instead of '%s'
        query = query.replace("%s", "?")
        # SQLite doesn't support AUTO_INCREMENT, replace in schema migration if running schema
        query = query.replace("AUTO_INCREMENT", "")
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        last_row_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_row_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        logger.error(f"Error executing write query: {e}\nQuery: {query}")
        raise e

def execute_read(query, params=None):
    """
    Executes a read query (SELECT).
    Returns a list of dicts.
    """
    conn, is_sqlite = get_connection()
    
    # Configure to return row as dicts
    if is_sqlite:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = query.replace("%s", "?")
    else:
        cursor = conn.cursor(dictionary=True)
        
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        rows = cursor.fetchall()
        
        # Format sqlite rows as dictionary list
        if is_sqlite:
            result = [dict(row) for row in rows]
        else:
            result = rows
            
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        cursor.close()
        conn.close()
        logger.error(f"Error executing read query: {e}\nQuery: {query}")
        raise e

def init_db():
    """
    Initializes the database using the schema.sql file.
    Creates tables if they do not exist.
    """
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}")
        return
        
    with open(schema_path, "r") as f:
        schema_sql = f.read()
        
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    # MySQL server database creation check
    if not is_sqlite and config.DB_TYPE == "mysql":
        try:
            # Reconnect without specifying database first, to ensure it exists
            temp_conn = mysql.connector.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD
            )
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_DATABASE}")
            temp_cursor.close()
            temp_conn.close()
        except Exception as e:
            logger.warning(f"Could not create database via MySQL: {e}")
            
    # For SQLite, we need to adapt schema.sql (remove engine declarations, auto_increment syntax)
    statements = schema_sql.split(";")
    
    for statement in statements:
        statement = statement.strip()
        if not statement:
            continue
            
        if is_sqlite:
            # Modify SQL statements to be SQLite compatible
            statement = statement.replace("AUTO_INCREMENT", "")
            # SQLite doesn't need to specify ENGINE/charset
            if "ENGINE=" in statement:
                statement = statement.split("ENGINE=")[0]
                
        try:
            cursor.execute(statement)
        except Exception as e:
            # For SQLite, ignore errors on things it doesn't fully support or if they exist
            logger.error(f"Failed to execute schema statement: {statement}. Error: {e}")
            
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database initialized successfully.")
