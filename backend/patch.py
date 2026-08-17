import sqlite3

conn = sqlite3.connect("farmwatch.db")
c = conn.cursor()
c.execute("UPDATE tasks SET stage = 'general' WHERE stage IS NULL")
print(f"Updated {c.rowcount} tasks")
conn.commit()
conn.close()
