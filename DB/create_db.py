#!/usr/bin/env python
import sqlite3


def create_db(file_path):
    conn = sqlite3.connect(file_path)
    c = conn.cursor()
    # Create table
    c.execute(
        """CREATE TABLE URLS (
        url_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        url TEXT NOT NULL,
        content TEXT,
        date_published DATE,
        date_of_query DATE,
        is_propaganda INT
    );"""
    )
    # Insert a row of data
    c.execute(
        """CREATE TABLE LINKS (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        parent_id INTEGER NOT NULL,
        child_id INTEGER NOT NULL,
        date DATE,
        SOURCE TEXT,
        FOREIGN KEY (parent_id)
          REFERENCES URLS(url_id)
             ON DELETE CASCADE
             ON UPDATE CASCADE,
      FOREIGN KEY (child_id)
          REFERENCES URLS(url_id)
             ON DELETE CASCADE
             ON UPDATE CASCADE
    );"""
    )

    # Save (commit) the changes
    conn.commit()
    # We can also close the -connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


if __name__ == "__main__":
    create_db(file_path="propaganda.db")
