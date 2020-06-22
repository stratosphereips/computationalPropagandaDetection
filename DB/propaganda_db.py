
import sqlite3

class DB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn =  sqlite3.connect(self.db_file )
        self.c = self.conn.cursor()

    def url_exist(self, url):
        return self.c.execute(f'''SELECT EXISTS(SELECT 1 FROM URLS WHERE url={url});''')

    def get_url_key(self, url):
        return self.c.execute(f'''SELECT ID FROM URLS WHERE url={url};''')


    def insert_url(self, url, content=None, date_published=None, date_of_query=None):
        url_exist = self.url_exist(url)
        if not url_exist:
            self.c.execute(f"""INSERT INTO URLS(url, content, date_published, date_of_query) VALUES 
            ({url}, {content}, {date_published}, {date_of_query}) """)
            self.commit()

    def insert_link_id(self,parent_id,child_id,  source=None):
        self.c.execute(f"""INSERT INTO LINKS(parent_id, child_id, source) VALUES 
                    ({parent_id}, {child_id}, {source}) """)
        self.commit()



    def insert_link_urls(self, parent_url, child_url, source):
        parent_url_exist = self.url_exist(parent_url)
        child_url_exist = self.url_exist(child_url)
        if parent_url_exist:
            self.insert_url(parent_url)
        if child_url_exist:
            self.insert_url(child_url)

        child_url_key = self.get_url_key(child_url)
        parent_url_key = self.get_url_key(parent_url)
        self.insert_link_id(parent_url_key, child_url_key, source)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()




