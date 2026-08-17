import sqlite3
import datetime

conn = sqlite3.connect('farmwatch.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS delivery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    photo_id INTEGER,
    total_weight_kg REAL,
    baskets_out INTEGER,
    baskets_in INTEGER,
    uploader_id INTEGER,
    is_reconciled BOOLEAN DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY(farm_id) REFERENCES farms(id),
    FOREIGN KEY(photo_id) REFERENCES photos(id),
    FOREIGN KEY(uploader_id) REFERENCES users(id)
)
''')

c.execute("SELECT id FROM inventory_items WHERE farm_id=6 AND name='空篮子 (Bal Kosong)'")
if not c.fetchone():
    c.execute('INSERT INTO inventory_items (farm_id, item_type, name, quantity, unit, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (6, 'other', '空篮子 (Bal Kosong)', 0, '个', datetime.datetime.now(), datetime.datetime.now()))
                 
conn.commit()
print('DB schema updated.')
