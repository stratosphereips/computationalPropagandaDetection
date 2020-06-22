#!/usr/bin/env python3.6

import sys
from datetime import datetime
from googlesearch import search
import time
import requests


class URLs():
    def __init__(self):
        pass

    def children(self, parent: str, children: str):
        print(f'\tNew children in object: {parent} -> {children}')

    def store_content(self, parent: str, content: str):
        print(f'\tNew content in url: {parent}')


def get_data_google(url):
    """
    Function to get data from google
    """
    googledata = search(url, tld="com", num=200, stop=200, pause=2)
    return googledata


if __name__ == "__main__":
    try:
        # Receive the first URL to search
        search_string = ' '.join(sys.argv[1:])

        """
        search(query, tld='com', lang='en', num=10, start=0, stop=None, pause=2.0)
        query : query string that we want to search for.
        tld : tld stands for top level domain which means we want to search our result on google.com or google.in or some other domain.
        lang : lang stands for language.
        num : Number of results we want.
        start : First result to retrieve.
        stop : Last result to retrieve. Use None to keep searching forever.
        pause : Lapse to wait between HTTP requests. Lapse too short may cause Google to block your IP. Keeping significant lapse will make your program slow but its safe and better option.
        Return : Generator (iterator) that yields found URLs. If the stop parameter is None the iterator will loop forever.
        """

        # Here we keep the list of URLs still to search
        urls_to_search = []
        
        # Store the first url
        urls_to_search.append(search_string)

        # Get the URLs object
        URLs = URLs()
        # Get everything
        for url in urls_to_search:
            # Get the content of the url and store it
            content = requests.get(url).text
            URLs.store_content(url, content)
            # Get the date when this url was created
            # not sure how yet
            # Get other links to this URL for the next round (children)
            print(f'Searching for data for url: {url}')
            googledata = get_data_google(url)
            for children_url in googledata:
                # Add the children to the DB
                URLs.children(url, children_url)
                # Check that the children was not seen before in this call
                try:
                    if urls_to_search.index(children_url) < 0:
                        # We dont have it, so append it
                        urls_to_search.append(children_url)
                except ValueError:
                    pass
            # Dont overload google
            time.sleep(4)

    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
