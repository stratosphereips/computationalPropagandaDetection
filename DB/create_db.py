#!/usr/bin/env python
import sqlite3


def create_main_db(file_path):
    conn = sqlite3.connect(file_path)
    c = conn.cursor()
    # Create table
    c.execute(
        """CREATE TABLE URLS (
        url_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        url TEXT NOT NULL,
        content TEXT,
        title TEXT,
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


def create_vk_db(file_path):
    conn = sqlite3.connect(file_path)
    c = conn.cursor()
    # Create table
    c.execute(
        """CREATE TABLE SEARCH_VK (
        url TEXT PRIMARY KEY,
        post_id INTEGER,
        date DATE,
        user_id INTEGER,
        from_id INTEGER,
        comments_count INT,
        likes_count INT,
        reposts_count INT,
        views_count INT,
        text TEXT,
        is_private INT
    );"""
    )
    # Save (commit) the changes
    conn.commit()
    # We can also close the -connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


if __name__ == "__main__":
    create_main_db(file_path="DB/databases/propaganda.db")
    create_vk_db(file_path="DB/databases/ mvk.db")
