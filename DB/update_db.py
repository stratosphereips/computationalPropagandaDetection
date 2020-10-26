#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect("propaganda.db")
c = conn.cursor()
# Create table
# c.execute("ALTER TABLE URLS ADD is_propaganda data_type int;")
c.execute("ALTER TABLE LINKS ADD date data_type DATE;")
# Save (commit) the changes
conn.commit()
# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
