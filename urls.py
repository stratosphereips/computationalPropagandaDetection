from DB.propaganda_db import DB


class URLs:
    def __init__(self, file_db, verbosity):
        self.urls = {}
        self.db = DB(file_db)
        self.verbosity = verbosity

    def set_child(self, parent: str, child: str):
        if self.verbosity > 2:
            print(f"\tNew children in object: > {child}")
        self.urls[parent]["children"] = child
        self.db.insert_link_urls(parent_url=parent, child_url=child, source="G")

    def store_content(self, url: str, content: str):
        if self.verbosity > 2:
            print(f"\tNew content stored for url: {url}")
        self.urls[url]["content"] = content
        self.db.update_url_content(url, content)

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

    def set_datetime(self, url, datetime):
        """
        Set the datetime when the result was published
        """
        self.urls[url] = {"publication_date": datetime}

    def set_search_datetime(self, url, result_search_date):
        """
        Set the datetime when we searched for this
        """
        self.urls[url] = {"search_date": result_search_date}
