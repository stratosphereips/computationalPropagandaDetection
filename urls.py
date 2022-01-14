from DB.propaganda_db import DB


class URLs:
    def __init__(self, file_db, verbosity):
        self.urls = {}
        self.db = DB(file_db)
        self.verbosity = verbosity

    def set_child(self, parent: str, child: str, link_date: str, link_type: str, similarity: float, clear_content: str):
        """
        Add a relationship, 'link', between a parent URL and a
        child URL.
        Input:
        - parent URL
        - child URL
        - link_date
        - link_type of link. It can be 'link' meaning the link was search
          or it can be 'title' meaning the title was search

        Returns True if successful, False if not
        """
        if link_type not in ["link", "title"]:
            return False
        # if self.verbosity > 3:
        #     print(f"\t\tNew children in object: > {child}")
        self.urls[parent]["children"] = child
        self.db.insert_link_urls(parent_url=parent, child_url=child, link_date=link_date, source=link_type, similarity=similarity)
        return True

    def store_content(self, url: str, content: str):
        self.urls[url]["content"] = content
        self.db.update_url_content(url, content)

    def store_clear_content(self, url:str, clear_content: str):
        self.urls[url]["clear_content"] = clear_content
        self.db.update_url_clear_content(url, clear_content)



    def store_title(self, url: str, title: str):
        self.urls[url]["title"] = title
        self.db.update_url_title(url, title)

    def show_urls(self):
        """ Show all the urls in store """
        for url in self.urls:
            print(f"\tURL: {url}")

    def add_url(self, url, is_propaganda=None):
        """ Add only a parent
        so we can store other things before having a child
        Also if case of a url without children!
        """
        self.urls[url] = {}
        self.db.insert_url(url=url, is_propaganda=is_propaganda)

    def set_publication_datetime(self, url: str, datetime: str):
        """
        Set the datetime when the result was published
        """
        self.urls[url] = {"publication_date": datetime}
        self.db.update_date_published(url, datetime)

    def set_query_datetime(self, url: str, result_search_date: str):
        """
        Set the datetime when we searched for this
        """
        self.urls[url] = {"search_date": result_search_date}
        self.db.update_date_of_query(url, result_search_date)

    def url_exist(self, url):
        return self.db.url_exist(url)

    def get_content_by_url(self, url):
        return self.db.get_content_by_url(url)

    def get_clear_content_by_url(self, url):
        return self.db.get_clear_content_by_url(url)

    def get_title_by_url(self, url):
        return self.db.get_url_by_title(url)

    def get_publication_datetime(self, url: str):
        """
        Set the datetime when the result was published
        """
        return self.db.get_date_published_url(url)
