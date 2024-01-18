import sqlite3
from datetime import datetime

DB_NAME = 'criteria.db'

# Connect to SQLite database (create it if not exists)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create a 'criteria' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS criteria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        duration INTEGER
    )
''')

# Create an 'alerts' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        resource TEXT,
        duration INTEGER
    )
''')

# Commit changes and close the connection
conn.commit()
conn.close()


def get_criteria_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch criteria from the database
    cursor.execute('SELECT * FROM criteria order by id desc')
    criteria = cursor.fetchall()

    # Convert date strings to datetime objects
    criteria = [(row[0],
                 datetime.strptime(row[1], '%Y-%m-%d'),
                 datetime.strptime(row[2], '%H:%M'),
                 datetime.strptime(row[3], '%H:%M'),
                 row[4])
                for row in criteria]

    conn.close()
    return criteria


def update_criteria_in_db(date, start_time, end_time, duration):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if criteria for the given date already exist
    cursor.execute('SELECT * FROM criteria')
    existing_criteria = cursor.fetchone()

    if existing_criteria:
        # Update existing criteria
        cursor.execute('''
            UPDATE criteria
            SET date=?, start_time=?, end_time=?, duration=?
            WHERE id=1
        ''', (date, start_time, end_time, duration))
    else:
        # Insert new criteria
        cursor.execute('''
            INSERT INTO criteria (date, start_time, end_time, duration)
            VALUES (?, ?, ?, ?)
        ''', (date, start_time, end_time, duration))

    conn.commit()
    conn.close()


def add_alert_to_db(date, time, resource, duration):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insert a new alert
        cursor.execute('''
            INSERT INTO alerts (date, time, resource, duration)
            VALUES (?, ?, ?, ?)
        ''', (date, time, resource, duration))
    except sqlite3.IntegrityError:
        print("Duplicate alert. Skipping insertion.")

    conn.commit()
    conn.close()


def alert_exists(date, time, resource, duration):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch existing alerts from the database
    cursor.execute('SELECT date, time, resource, duration FROM alerts')
    alerts = set(cursor.fetchall())

    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')
    formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')

    conn.close()

    # Check if an alert already exists for the given date, time, resource, and duration
    return (formatted_date, formatted_time, resource, duration) in alerts
