#!/usr/bin/env python
import sqlite3


def create_db(file_path):
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
        text TEXT
    );"""
    )
    # Save (commit) the changes
    conn.commit()
    # We can also close the -connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()


if __name__ == "__main__":
    create_db(file_path="vk.db")
