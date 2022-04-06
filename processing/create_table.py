import sqlite3

conn = sqlite3.connect('stats.sqlite')

c = conn.cursor()

c.execute('''
            CREATE TABLE stats
            (id INTEGER PRIMARY KEY ASC,
            num_bs_readings INTEGER NOT NULL,
            max_bs_readings INTEGER,
            min_bs_readings INTEGER,
            num_cl_readings INTEGER NOT NULL,
            max_cl_readings INTEGER,
            min_cl_readings INTEGER,
            last_updated VARCHAR(100) NOT NULL)
            ''')

conn.commit()
conn.close()