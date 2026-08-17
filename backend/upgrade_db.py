import sqlite3
import os

db_path = 'farmwatch.db'
if not os.path.exists(db_path):
    print("DB not found")
    exit(0)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create farm_zones table
c.execute('''
CREATE TABLE IF NOT EXISTS farm_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    parent_zone VARCHAR(100),
    name VARCHAR(100),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(farm_id) REFERENCES farms(id)
)
''')
c.execute('CREATE INDEX IF NOT EXISTS ix_farm_zones_name ON farm_zones (name)')
c.execute('CREATE INDEX IF NOT EXISTS ix_farm_zones_id ON farm_zones (id)')

# Add zone_id to tasks, photos, messages
def add_column(table, col_def):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            raise e

add_column('tasks', 'zone_id INTEGER REFERENCES farm_zones(id)')
add_column('photos', 'zone_id INTEGER REFERENCES farm_zones(id)')
add_column('messages', 'zone_id INTEGER REFERENCES farm_zones(id)')

conn.commit()
conn.close()
print("DB upgraded successfully.")
