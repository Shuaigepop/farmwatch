import sqlite3

conn = sqlite3.connect('farmwatch.db')
c = conn.cursor()
c.execute("DELETE FROM tasks WHERE title NOT LIKE '%⏰%' AND status = 'pending'")
conn.commit()
conn.close()
print('Cleaned up old pending tasks.')
