import sqlite3
conn = sqlite3.connect('farmwatch.db')
stmts = [
    'ALTER TABLE farms ADD COLUMN check_time VARCHAR DEFAULT "18:00"',
    'ALTER TABLE farms ADD COLUMN summary_time VARCHAR DEFAULT "19:00"',
    'ALTER TABLE farms ADD COLUMN sop_time VARCHAR DEFAULT "06:00"',
    'ALTER TABLE recurring_tasks ADD COLUMN target_role VARCHAR DEFAULT "worker"',
    'ALTER TABLE tasks ADD COLUMN notify_time VARCHAR',
    'ALTER TABLE tasks ADD COLUMN verified_by INTEGER',
    'ALTER TABLE tasks ADD COLUMN verified_at TIMESTAMP',
    'ALTER TABLE tasks ADD COLUMN target_role VARCHAR DEFAULT "worker"'
]
for s in stmts:
    try:
        conn.execute(s)
    except Exception as e:
        pass
conn.commit()
conn.close()
