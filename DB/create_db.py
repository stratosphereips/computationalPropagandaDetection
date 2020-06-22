import sqlite3
conn = sqlite3.connect('propaganda.db')
c = conn.cursor()
# Create table
c.execute('''CREATE TABLE URLS (
	url_id INTEGER PRIMARY KEY AUTOINCREMENT,
	url TEXT NOT NULL,
	CONTENT TEXT NOT NULL,
	date_published DATE,
	date_of_query DATE NOT NULL
);''')
# Insert a row of data
c.execute("""CREATE TABLE LINKS (
	link_id INTEGER PRIMARY KEY AUTOINCREMENT,
	parent_id INTEGER NOT NULL,
	child_id INTEGER NOT NULL,
	SOURCE TEXT,
	FOREIGN KEY (parent_id)
      REFERENCES URLS(url_id)
         ON DELETE CASCADE
         ON UPDATE CASCADE,
  FOREIGN KEY (child_id)
      REFERENCES URLS(url_id)
         ON DELETE CASCADE
         ON UPDATE CASCADE
);""")
# Save (commit) the changes
conn.commit()
# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()