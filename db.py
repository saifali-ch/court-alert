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
        duration INTEGER,
        active INTEGER
    )
''')

# Create an 'alerts' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        resource TEXT,
        criteria_id INTEGER,
        FOREIGN KEY(criteria_id) REFERENCES criteria(id)
    )
''')

# Commit changes and close the connection
conn.commit()
conn.close()


def get_criteria(active=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if active:
        cursor.execute('SELECT * FROM criteria WHERE active = 1 and date >= date("now")')
    else:
        cursor.execute('SELECT * FROM criteria WHERE date >= date("now")')

    criteria = cursor.fetchall()

    # Convert date strings to datetime objects
    criteria = [(row[0],  # id
                 datetime.strptime(row[1], '%Y-%m-%d'),  # date
                 datetime.strptime(row[2], '%H:%M'),  # start_time
                 datetime.strptime(row[3], '%H:%M'),  # end_time
                 row[4],  # duration
                 row[5])  # active
                for row in criteria]

    conn.close()
    return criteria


def add_criteria_to_db(date, start_time, end_time, duration, active):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insert new criteria
    cursor.execute('''
        INSERT INTO criteria (date, start_time, end_time, duration, active)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, start_time, end_time, duration, active))

    conn.commit()
    conn.close()


def update_criteria_in_db(criteria_id, date, start_time, end_time, duration, active):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Update existing criteria by id
    cursor.execute('''
        UPDATE criteria
        SET date=?, start_time=?, end_time=?, duration=?, active=?
        WHERE id=?
    ''', (date, start_time, end_time, duration, active, criteria_id))

    conn.commit()
    conn.close()


def update_criteria_status(criteria_id, active):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Update the 'active' status for the specified criteria_id
    cursor.execute('UPDATE criteria SET active=? WHERE id=?', (active, criteria_id))

    conn.commit()
    conn.close()


def delete_criteria_from_db(criteria_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Delete the specified criteria
    cursor.execute('DELETE FROM criteria WHERE id=?', (criteria_id,))

    conn.commit()
    conn.close()


def add_alert(time, resource, criteria_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO alerts (time, resource, criteria_id)
        VALUES (?, ?, ?)
    ''', (time, resource, criteria_id))

    conn.commit()
    conn.close()


def alert_exists(time, resource, criteria_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch existing alerts from the database
    cursor.execute('SELECT time, resource, criteria_id FROM alerts')
    alerts = set(cursor.fetchall())

    conn.close()

    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')

    # Check if an alert already exists for the given time, resource, and criteria_id
    return (formatted_time, resource, criteria_id) in alerts
