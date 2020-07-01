
import sqlite3
import sqlalchemy

class DB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file )
        self.c = self.conn.cursor()

    def url_exist(self, url):
        url_exist = self.c.execute("""SELECT url_id FROM URLS WHERE url=(?);""", (url,))
        if len(url_exist.fetchall()) > 0:
            return True
        return False
    def link_exist(self, parent_id, child_id):
        url_exist = self.c.execute("""SELECT LINK_ID FROM LINKS WHERE parent_id=(?) and child_id=(?);""", (parent_id,child_id))
        if len(url_exist.fetchall()) > 0:
            return True

        return False

    def get_url_key(self, url):
        ids = self.c.execute("""SELECT URL_ID FROM URLS WHERE url=(?)""", (url, )).fetchall()
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
            self.c.execute(f"""INSERT INTO URLS(url, content, date_published, date_of_query, is_propaganda) VALUES 
            (?, ?, ?, ?, ?) """, (url, content, date_published, date_of_query, is_propaganda))
            self.commit()

    def insert_link_id(self, parent_id, child_id,  source=None):
        self.c.execute(f"""INSERT INTO LINKS(parent_id, child_id, source) VALUES 
                    (?, ?, ?) """, (parent_id, child_id,  source))
        self.commit()


    def insert_link_urls(self, parent_url, child_url, source):
        parent_url_exist = self.url_exist(parent_url)
        child_url_exist = self.url_exist(child_url)
        if not parent_url_exist:
            self.insert_url(parent_url)
        if not child_url_exist:
            self.insert_url(child_url)

        child_id = self.get_url_key(child_url)
        parent_id = self.get_url_key(parent_url)
        if not self.link_exist(child_id, parent_id):
            self.insert_link_id(child_id, parent_id, source)
        self.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    db = DB("propaganda.db")
    print(db.c.execute("""SELECT COUNT(URL) FROM URLS;""").fetchall())
    print(db.c.execute("""SELECT URL FROM URLS;""").fetchall())

    print(db.c.execute("""SELECT * FROM LINKS;""").fetchall())
    # #db.insert_url()
    #
    # print('INSERT INTO URLS(url) VALUES {}'.format(s.replace('"', '""')))
    #


