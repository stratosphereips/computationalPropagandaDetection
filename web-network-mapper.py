#!/usr/bin/env python

import sys
from datetime import datetime
import time
import requests
from DB.propaganda_db import DB
import traceback
from serpapi.google_search_results import GoogleSearchResults
import json


f = open('serapi.key')
SERAPI_KEY = f.readline()[:-1]
f.close()


def trigger_api(search_leyword):
    """
    Bing using BingSearchResults class
    Baidu using BaiduSearchResults class
    Yahoo using YahooSearchResults class
    Ebay using EbaySearchResults class
    Yandex using YandexSearchResults class
    GoogleScholar using GoogleScholarSearchResults class

    """
    try:
        params = {
                  "engine": "google",
                  "q": search_leyword,
                  "google_domain": "google.com",
                  "api_key": SERAPI_KEY
                }
        client = GoogleSearchResults(params)
        results = client.get_dict()
        return results
    except Exception as e:
        print('Error in trigger_api()')
        print(f'{e}')
        print(f'{type(e)}')
        print(traceback.format_exc())


class URLs():
    def __init__(self, file_db):
        self.urls = {}
        self.db = DB(file_db)

    def set_child(self, parent: str, child: str):
        print(f'\tNew children in object: {parent} -> {child}')
        self.urls[parent]['children'] = child
        self.db.insert_link_urls(parent_url=parent, child_url=child, source="G")

    def store_content(self, parent: str, content: str):
        print(f'\tNew content in url: {parent}')
        self.urls[parent]['content'] = content
        self.db.update_url_content(parent, content)

    def show_urls(self):
        """ Show all the urls in store """
        for url in self.urls:
            print(f'\tURL: {url}')

    def add_url(self, url):
        """ Add only a parent
        so we can store other things before having a child
        Also if case of a url without children!
        """
        self.urls[url] = {}
        self.db.insert_url(url=url)


def downloadContent(url):
    """
    Downlod the content of the web page
    """
    try:
        content = requests.get(url).text
    except requests.exceptions.ConnectionError:
        print('Error in getting content')
    except Exception as e:
        print('Error getting the content of the web.')
        print(f'{e}')
        print(f'{type(e)}')
    name_file = url.split('/')[2]
    timemodifier = str(datetime.now().second)
    file = open(name_file + '_' + timemodifier + '-content.html', 'w')
    file.write(content)
    file.close()


if __name__ == "__main__":
    try:
        # Receive the first URL to search
        search_string = ' '.join(sys.argv[1:])

        # Here we keep the list of URLs still to search
        urls_to_search = []

        # Store the first url
        urls_to_search.append(search_string)

        # Get the URLs object
        URLs = URLs("DB/propaganda.db")
        iteration = 0
        # Get everything
        for url in urls_to_search:
            print(f'Searching data for url: {url}')
            URLs.add_url(url)
            # Keep track of the iteration level
            iteration += 1
            # Get the content of the url and store it
            content = downloadContent(url)
            URLs.store_content(url, content)
            # Get the date when this url was created
            # Get other links to this URL for the next round (children)
            data = trigger_api(url)
            urls = []
            for result in data['organic_results']:
                urls.append(result['link'])

            for children_url in urls:
                # Add the children to the DB
                URLs.set_child(url, children_url)
                # Check that the children was not seen before in this call
                try:
                    _ = urls_to_search.index(children_url)
                    # We hav, so ignore
                    print(f'Repeated url: {children_url}')
                except ValueError:
                    # The url was not in the list. Append
                    urls_to_search.append(children_url)
                except Exception as e:
                    print(f"Error type {type(e)}")
                    print(f"Error {e}")
            print(f'Urls after searching for th {iteration} URL: {urls_to_search}')

        print('Finished with all the graph of URLs')
        print('Final list of urls')
        URLs.show_urls()
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
