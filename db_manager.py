import psycopg2
from contextlib import contextmanager
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    filename="earthquake.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": 5432
}

@contextmanager
def db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        logging.error(f"Ошибка при работе с БД: {str(e)}")
    finally:
        if conn:
            conn.close()

def create_table():
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS earthquakes (
                        id VARCHAR(255) PRIMARY KEY,
                        location VARCHAR(255),
                        magnitude REAL,
                        event_time TIMESTAMP,
                        url VARCHAR(255),
                        radius INTEGER,
                        notified BOOLEAN DEFAULT FALSE
                    );
                    CREATE TABLE IF NOT EXISTS users (
                        chat_id BIGINT PRIMARY KEY,
                        username TEXT,
                        last_notified TIMESTAMP
                    );
                """)
                conn.commit()


def save_earthquakes_to_db(earthquakes):
    with db_connection() as conn:
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                for earthquake in earthquakes:
                    earthquake_id = earthquake.get("id")
                    place = earthquake.get("place")
                    mag = earthquake.get("mag")
                    time = earthquake.get("time")
                    url = earthquake.get("url")

                    if time is not None:
                        time = datetime.fromtimestamp(time / 1000)

                    query = """
                        INSERT INTO earthquakes (id, location, magnitude, event_time, url)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING;
                    """
                    cur.execute(query, (earthquake_id, place, mag, time, url))
                conn.commit()

        except psycopg2.Error as e:
            logging.error(f"Ошибка сохранения данных: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

def save_user(chat_id, username):
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (chat_id, username)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) DO UPDATE
                    SET username = EXCLUDED.username;
                """, (chat_id, username))
                conn.commit()

def get_all_users():
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_id FROM users;")
                return [row[0] for row in cur.fetchall()]
    return []

def get_new_earthquakes():
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, location, magnitude, 
                           event_time, url, radius 
                    FROM earthquakes 
                    WHERE notified = FALSE;
                """)
                return cur.fetchall()
    return []

def get_stats():
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        MAX(magnitude) as max_mag,
                        AVG(magnitude) as avg_mag 
                    FROM earthquakes;
                """)
                return cur.fetchone()

def mark_as_notified(earthquake_ids):
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE earthquakes 
                    SET notified = TRUE 
                    WHERE id = ANY(%s);
                """, (earthquake_ids,))
                conn.commit()