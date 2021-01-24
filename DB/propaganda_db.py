#!/usr/bin/env python
import sqlite3
from typing import List, Tuple
from datetime import datetime


class DB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()

    def url_exist(self, url):
        url_exist = self.c.execute("""SELECT url_id FROM URLS WHERE url=(?);""", (url,))
        data = url_exist.fetchall()
        if len(data) > 0:
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
            raise Exception("URL is not in DB")
        else:
            return ids[0][0]

    def update_url_title(self, url, title):
        self.c.execute("""UPDATE URLS SET title = ?  WHERE url = ?""", (title, url))
        self.commit()

    def update_url_content(self, url, content):
        self.c.execute("""UPDATE URLS SET content = ?  WHERE url = ?""", (content, url))
        self.commit()

    def insert_url(self, url, content=None, date_published=None, date_of_query=None, is_propaganda=None):
        url_exist = self.url_exist(url)

        if not url_exist:
            self.c.execute(
                """INSERT INTO URLS(url, content, date_published, date_of_query, is_propaganda) VALUES  (?, ?, ?, ?, ?) """,
                (url, content, date_published, date_of_query, is_propaganda),
            )
            self.commit()
        else:
            # assuming that the new date_of_query will be always newer which is already in DB, we will change it with the new date
            self.update_date_of_query(url, date_of_query)

    def insert_link_id(self, parent_id: int, child_id: int, link_date: str, source: str = None):
        self.c.execute("""INSERT INTO LINKS(parent_id, child_id, date, source) VALUES (?, ?, ?, ?) """, (parent_id, child_id, link_date, source))
        self.commit()

    def insert_link_urls(self, parent_url: str, child_url: str, link_date: str, source: str = None):
        parent_url_exist = self.url_exist(parent_url)
        child_url_exist = self.url_exist(child_url)
        if not parent_url_exist:
            self.insert_url(parent_url)
        if not child_url_exist:
            self.insert_url(child_url)

        child_id = self.get_url_id(child_url)
        parent_id = self.get_url_id(parent_url)
        if not self.link_exist(parent_id=parent_id, child_id=child_id):
            self.insert_link_id(parent_id=parent_id, child_id=child_id, link_date=link_date, source=source)
        else:
            # If the link types are different, insert
            old_link_type = self.get_type_of_link_by_ids(parent_id=parent_id, child_id=child_id)
            if source != old_link_type:
                self.insert_link_id(parent_id=parent_id, child_id=child_id, link_date=link_date, source=source)
            else:
                # If the link types are the same, check the date
                old_link_date = self.get_date_of_link_by_ids(parent_id=parent_id, child_id=child_id)  # getting date of existing link
                old_link_date_obj = datetime.strptime(old_link_date, "%Y-%m-%d %H:%M:%S.%f")
                # keeping the oldest link
                if link_date < old_link_date_obj:
                    self.update_date_of_link(parent_id=parent_id, child_id=child_id, date=link_date)
        self.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_tree(self, main_url: str) -> List[Tuple[str, str]]:
        """
        Function which return edges in form of [from_url, to_url] of subtree, where root of the tree is main url.
        :param main_url: the root of the tree
        :return: Dictionary of levels, each with a list of edges in form of [from_url, to_url]. Example: { [0]:[(url1, url2), (url1, url3)], [1]:[(url2, url4), (url2, url5)] }
        """
        main_id = self.get_url_id(main_url)  # id of this url in DB
        # visited_parents = [main_id]  # list of parent ids which already visited
        urls_to_retrieve_childs = [main_id]  # list of urls to retrieve childs
        edges = []  # edges of the subtree
        level = {}
        level[main_id] = 0

        for parent_id in urls_to_retrieve_childs:

            # visited_parents.append(parent_id)
            parent_url = self.get_url_by_id(parent_id)[0][0]

            # getting all childrens which start from the parent_id
            children_ids = self.c.execute("""SELECT child_id FROM LINKS WHERE parent_id=(?);""", (parent_id,)).fetchall()

            for child_tuple in children_ids:
                child_id = child_tuple[0]
                level[child_id] = level[parent_id] + 1
                # if the child was already expend, dont add it to the queue
                if child_id not in urls_to_retrieve_childs:
                    urls_to_retrieve_childs.append(child_id)
                child_url = self.get_url_by_id(child_id)[0][0]
                edges.append((level[child_id], parent_url, child_url))
        return edges

    def update_date_published(self, url: str, date_of_publication: str):
        self.c.execute("""UPDATE URLS SET date_published = ?  WHERE url = ?""", (date_of_publication, url))
        self.commit()

    def update_date_of_query(self, url: str, date_of_query: str):
        self.c.execute("""UPDATE URLS SET date_of_query = ?  WHERE url = ?""", (date_of_query, url))
        self.commit()

    def update_date_of_link(self, parent_id: int, child_id: int, date: str):
        self.c.execute("""UPDATE LINKS SET date = ?  WHERE parent_id = ? and child_id = ?""", (date, parent_id, child_id))
        self.commit()

    def __get_date_url(self, url: str, type_of_date: str) -> str:
        dates = self.c.execute(f"""SELECT {type_of_date} FROM URLS WHERE url=?""", (url,)).fetchall()
        if len(dates) > 0:
            return dates[0][0]
        else:
            return None

    def get_date_of_query_url(self, url: str) -> str:
        return self.__get_date_url(url, "date_of_query")

    def get_date_published_url(self, url: str) -> str:
        return self.__get_date_url(url, "date_published")

    def get_date_of_link_by_ids(self, parent_id: int, child_id: int) -> str:
        dates = self.c.execute("""SELECT date FROM LINKS WHERE parent_id=? and child_id=?""", (parent_id, child_id)).fetchall()
        if len(dates) > 0:
            return dates[0][0]
        return None

    def get_type_of_link_by_ids(self, parent_id: int, child_id: int) -> str:
        link_type = self.c.execute("""SELECT source FROM LINKS WHERE parent_id=? and child_id=?""", (parent_id, child_id)).fetchall()
        if len(link_type) > 0:
            return link_type[0][0]

    def get_date_of_link(self, parent_url: str, child_url: str) -> str:
        child_id = self.get_url_id(child_url)
        parent_id = self.get_url_id(parent_url)
        return self.get_date_of_link_by_ids(parent_id=parent_id, child_id=child_id)


if __name__ == "__main__":
    db = DB("propaganda.db")
