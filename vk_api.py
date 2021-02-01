import vk
from datetime import datetime
import sqlite3

f = open("vk.key")
VK_KEY = f.readline()
f.close()


class VKDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def add_values(self, values):
        (url, post_id, user_id, from_id, date, text, comments_count, likes_count, reposts_count, views_count, is_private) = values
        if not self.url_exist(url):
            self.c.execute(
                """INSERT INTO SEARCH_VK(url, post_id, user_id,from_id, date, text,comments_count, likes_count, \
                reposts_count, views_count, is_private ) \
                VALUES  (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                (url, post_id, user_id, from_id, date, text, comments_count, likes_count, reposts_count, views_count, is_private),
            )
            self.commit()

    def close(self):
        self.conn.close()

    def url_exist(self, url):
        url_exist = self.c.execute("""SELECT url FROM SEARCH_VK WHERE url=(?);""", (url,))
        if len(url_exist.fetchall()) > 0:
            return True
        return False


def get_number_of_intereaction(report, name_of_interaction):
    return report[name_of_interaction]["count"]


def get_vk_data(
    searched_phrase, db_path="DB/vk.db",
):
    session = vk.Session(access_token=VK_KEY)

    api = vk.API(session)
    reports = api.newsfeed.search(q=searched_phrase, v="5.126")
    vkdb = VKDB(db_path)
    vk_info = []

    for report in reports["items"]:
        user_id = report["owner_id"]
        from_id = report["from_id"]
        is_private = 1
        if user_id < 0:
            is_private = 0
        post_id = report["id"]
        date = datetime.utcfromtimestamp(report["date"]).strftime("%Y-%m-%d %H:%M:%S")
        text = report["text"]
        comments_count = get_number_of_intereaction(report, "comments")
        likes_count = get_number_of_intereaction(report, "likes")
        reposts_count = get_number_of_intereaction(report, "reposts")
        views_count = get_number_of_intereaction(report, "views")
        url = f"https://vk.com/id{user_id}?w=wall{user_id}_{post_id}"
        values = (url, post_id, user_id, from_id, date, text, comments_count, likes_count, reposts_count, views_count, is_private)
        vkdb.add_values(values)
        vk_info.append({"link": url, "text": text, "published_date": date})

    vkdb.close()
    return vk_info


info = get_vk_data("https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html")
print(info)
