import sqlite3

db_path = 'travel_chats.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM message_store ORDER BY rowid ASC;")
    print([description[0] for description in cursor.description])
    rows = cursor.fetchall()
    print("Rows in message_store:")
    for row in rows:
        print(row[2])  # Assuming the content is in the third column
except Exception as e:
    print(f"Error fetching data: {e}")

conn.close()