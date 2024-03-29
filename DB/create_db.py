#!/usr/bin/env python
import sqlite3
import os


def create_main_db(file_path):
    conn = sqlite3.connect(file_path)
    c = conn.cursor()
    # Create table
    c.execute(
        """CREATE TABLE URLS (
        url_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        url TEXT NOT NULL,
        content TEXT,
        clear_content TEXT,
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
        similarity FLOAT,
        date DATE,
        source TEXT,
        link_type TEXT,
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
        mark_as_ad_count INT,
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
    # Is supposed to be run fron the main folder
    basepath = "DB/databases"
    try:
        os.makedirs(basepath)
    except FileExistsError:
        pass
    create_main_db(file_path=os.path.join(basepath, "propaganda.db"))
    create_vk_db(file_path=os.path.join(basepath, "vk.db"))
