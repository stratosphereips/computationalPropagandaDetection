#!/usr/bin/env python3.6

import sys
from datetime import datetime
from googlesearch import search
import time
import requests


class URLs():
    def __init__(self):
        self.urls = {}
        pass

    def children(self, parent: str, children: str):
        print(f'\tNew children in object: {parent} -> {children}')
        self.urls[parent]['children'] = children

    def store_content(self, parent: str, content: str):
        print(f'\tNew content in url: {parent}')
        self.urls[parent]['content'] = content

    def show_urls(self):
        """ Show all the urls in store """
        for url in self.urls:
            print(f'\tURL: {url}')

    def addParent(self, url):
        """ Add only a parent
        so we can store other things before having a child
        Also if case of a url without children!
        """
        self.urls[url] = {}


def get_data_google(url):
    """
    Function to get data from google

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

    googledata = search(url, tld="com", num=200, stop=200, pause=5)
    return googledata


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
        URLs = URLs()
        iteration = 0
        # Get everything
        for url in urls_to_search:
            print(f'Searching data for url: {url}')
            URLs.addParent(url)
            # Keep track of the iteration level
            iteration += 1
            # Get the content of the url and store it
            content = downloadContent(url)
            URLs.store_content(url, content)
            # Get the date when this url was created
            # not sure how yet
            # Get other links to this URL for the next round (children)
            googledata = get_data_google(url)
            # googledata = ['http://aaa.com','http://ccc.com','http://bbb.com','http://aaa.com']
            for children_url in googledata:
                # Add the children to the DB
                URLs.children(url, children_url)
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
            # Dont overload google
            time.sleep(60)

        print('Finished with all the graph of URLs')
        print('Final list of urls')
        URLs.show_urls()

    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
