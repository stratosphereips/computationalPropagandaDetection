#!/usr/bin/env python
import sqlite3
from typing import List, Tuple


class DB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()

    def url_exist(self, url):
        url_exist = self.c.execute("""SELECT url_id FROM URLS WHERE url=(?);""", (url,))
        if len(url_exist.fetchall()) > 0:
            return True
        return False

    def get_url_by_id(self, url_id):
        return self.c.execute("""SELECT url FROM URLS WHERE url_id=(?)""", (url_id,)).fetchall()

    def link_exist(self, parent_id, child_id):
        url_exist = self.c.execute("""SELECT LINK_ID FROM LINKS WHERE parent_id=(?) and child_id=(?);""", (parent_id, child_id))
        if len(url_exist.fetchall()) > 0:
            return True

        return False

    def get_url_id(self, url):
        ids = self.c.execute("""SELECT URL_ID FROM URLS WHERE url=(?)""", (url,)).fetchall()
        if len(ids) > 1:
            raise Exception("There are multiple ids for this url")
        if len(ids) == 0:
            raise Exception("URLS is not in DB")
        else:
            return ids[0][0]

    def update_url_content(self, url, content):
        self.c.execute("""UPDATE URLS SET content = ?  WHERE url = ?""", (content, url))
        self.commit()

    def insert_url(self, url, content=None, date_published=None, date_of_query=None, is_propaganda=None):
        url_exist = self.url_exist(url)

        if not url_exist:
            self.c.execute("""INSERT INTO URLS(url, content, date_published, date_of_query, is_propaganda) VALUES  (?, ?, ?, ?, ?) """, (url, content, date_published, date_of_query, is_propaganda))
            self.commit()
        else:
            # assuming that the new date_of_query will be always newer which is already in DB, we will change it with the new date
            self.update_date_of_query(url, date_of_query)

    def insert_link_id(self, parent_id: int, child_id: int, link_date: str, source: str = None):
        self.c.execute("""INSERT INTO LINKS(parent_id, child_id, date, source) VALUES (?, ?, ?, ?) """, (parent_id, child_id, link_date, source))
        self.commit()

    def insert_link_urls(self, parent_url: str, child_url: str, link_date: str, source: str=None):
        parent_url_exist = self.url_exist(parent_url)
        child_url_exist = self.url_exist(child_url)
        if not parent_url_exist:
            self.insert_url(parent_url)
        if not child_url_exist:
            self.insert_url(child_url)

        child_id = self.get_url_id(child_url)
        parent_id = self.get_url_id(parent_url)
        if not self.link_exist(child_id, parent_id):
            self.insert_link_id(parent_id=parent_id, child_id=child_id, link_date=link_date, source=source)
        self.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_tree(self, main_url: str) -> List[Tuple[str, str]]:
        """
        Function which return edges in form of [from_url, to_url] of subtree, where root of the tree is main url.
        :param main_url: the root of the tree
        :return: List of edges in form of [from_url, to_url]
        """
        main_id = self.get_url_id(main_url)  # id of this url in DB
        parent_id_queue = [main_id]  # list od ids to be opened
        visited_parents = [main_id]  # list od ids which already visited
        edges = []  # edges of the subtree
        for parent_id in parent_id_queue:

            visited_parents.append(parent_id)
            # getting all childrens which start from the parent_id
            # returns in the form of List[Tuples]
            children_ids = self.c.execute("""SELECT child_id FROM LINKS WHERE parent_id=(?);""", (parent_id,)).fetchall()
            parent_url = self.get_url_by_id(parent_id)[0][0]
            for child_tuple in children_ids:
                child_id = child_tuple[0]
                # if the child was already expend, dont add it to the queue
                if child_id not in visited_parents and child_id not in parent_id_queue:
                    parent_id_queue.append(child_id)
                child_url = self.get_url_by_id(child_id)[0][0]
                edges.append((parent_url, child_url))
        return edges

    def update_date_published(self, url:str, date_of_publication: str):
        self.c.execute("""UPDATE URLS SET date_published = ?  WHERE url = ?""", (date_of_publication, url))
        self.commit()

    def update_date_of_query(self, url:str, date_of_query: str):
        self.c.execute("""UPDATE URLS SET date_of_query = ?  WHERE url = ?""", (date_of_query, url))
        self.commit()

    def get_date_of_query_url(self, url:str) -> str:
        dates = self.c.execute("""SELECT date_of_query FROM URLS WHERE url=?""", (url, )).fetchall()

        if len(dates) > 0:
            return dates[0][0]
        else:
            return None

    def get_date_of_link(self, parent_url:str, child_url:str) -> str:
        child_id = self.get_url_key(child_url)
        parent_id = self.get_url_key(parent_url)
        dates = self.c.execute("""SELECT date FROM LINKS WHERE parent_id=? and child_id=?""", (parent_id,child_id )).fetchall()
        if len(dates) > 0:
            return dates[0][0]

if __name__ == '__main__':
    db = DB("propaganda.db")

