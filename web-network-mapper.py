#!/usr/bin/env python

import sys
from datetime import datetime
import requests
from DB.propaganda_db import DB
import traceback
from serpapi.google_search_results import GoogleSearchResults
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib._color_data as mcd

import argparse


# Read the serapi api key
f = open('serapi.key')
SERAPI_KEY = f.readline()[:-1]
f.close()


def build_a_graph(all_links, search_link):

    def filter_name(url):
        basename = url.split('/')[2]
        if "www" == basename[:3]:
            return basename[4:]
        return basename
    labels = {}
    levels = {search_link: 0}
    G = nx.DiGraph()
    G.add_edges_from(all_links)
    colors = ["black"]
    possible_colors = ["red", "green", "c", "m", "y"]

    for (from_link, to_link) in all_links:
        labels[from_link] = filter_name(from_link)
        labels[to_link] = filter_name(to_link)
        if to_link not in levels:
            levels[to_link] = levels[from_link] + 1
            colors.append(possible_colors[levels[to_link] % len(possible_colors)])
    print(levels)
    nx.draw(G, labels=labels, node_color=colors, with_labels=True)
    # nx.draw_spectral(G)
    # pos = nx.spring_layout(G)
    # nx.draw_networkx_labels(G, pos, labels, font_size=16)
    plt.show()

def trigger_api(search_leyword):
    """
    Bing using BingSearchResults class
    Baidu using BaiduSearchResults class
    Yahoo using YahooSearchResults class
    Ebay using EbaySearchResults class
    Yandex using YandexSearchResults class
    GoogleScholar using GoogleScholarSearchResults class

    This api has
    "position": 8,
    "title": "COVID-19 и Мишель Фуко (некоторые мысли вслух ...",
    "link": "https://www.geopolitica.ru/article/covid-19-i-mishel-fuko-nekotorye-mysli-vsluh",
    "displayed_link": "www.geopolitica.ru › article › covid-...",
    "thumbnail": null,
    "date": "Apr 5, 2020",
    "snippet": "... проект ID2020 (почитать о нем можно здесь - https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html).",
    "cached_page_link": "https://webcache.googleusercontent.com/search?q=cache:rrzBOTKH5BsJ:https://www.geopolitica.ru/article/covid-19-i-mishel-fuko-nekotorye-mysli-vsluh+&cd=8&hl=en&ct=clnk&gl=us"

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
        # Store the results of the api for future comparison
        modificator_time = str(datetime.now().hour) + ':' + str(datetime.now().minute) + ':' + str(datetime.now().second)
        # write the results to a json file so we dont lose them
        with open('results-' + modificator_time + '.json', 'w') as f:
            json.dump(results, f)
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
        #print(f'\tNew children in object: {parent} -> {child}')
        print(f'\tNew children in object: > {child}')
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
        self.urls[url] = {'publication_date': datetime}

    def set_search_datetime(self, url, result_search_date):
        """
        Set the datetime when we searched for this
        """
        self.urls[url] = {'search_date': result_search_date}



def downloadContent(url):
    """
    Downlod the content of the web page
    """
    try:
        content = requests.get(url).text
    except requests.exceptions.ConnectionError:
        print('Error in getting content')
        content = ''
    except Exception as e:
        print('Error getting the content of the web.')
        print(f'{e}')
        print(f'{type(e)}')
    name_file = url.split('/')[2]
    timemodifier = str(datetime.now().second)
    file = open('contents/' + name_file + '_' + timemodifier + '-content.html', 'w')
    file.write(content)
    file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l","--link", help = "link to build a graph", type=str)
    parser.add_argument("-p","--is_propaganda", help = "link to build a graph", action="store_true")

    args = parser.parse_args()
    try:
        # Create the dot object to plot a graph
        G = nx.Graph()
        # G = nx.cubical_graph()
        # Labels for the nx graph
        labels = {}

        # Blacklist of pages to ignore
        blacklist = {'robots.txt', 'sitemap.xml'}

        # Get the URLs object
        URLs = URLs("DB/propaganda.db")

        URLs.add_url(args.link, int(args.is_propaganda))

        # Here we keep the list of URLs still to search
        urls_to_search = [args.link]

        all_links = []

        for iteration, url in enumerate(urls_to_search):
            # For now, dont go in an infinite search for the Internet.
            if iteration == 3:
                break

            print('\n==========================================')
            print(f'Searching data for url: {url}')

            # Add this url
            URLs.add_url(url)

            # Get the content of the url and store it
            content = downloadContent(url)
            URLs.store_content(url, content)
            # Get the date when this url was created
            # Get other links to this URL for the next round (children)
            data = trigger_api(url)
            urls = []
            # From all the jsons, get only the links to continue
            try:
                for result in data['organic_results']:
                    urls.append(result['link'])
            except KeyError:
                # There are no organic_results
                pass

            for children_url in urls:

                # Apply some black list of the pages we dont want, such as
                # sitemap.xml and robots.txt , because they only have links
                # The page is the text after the last /
                if children_url.split('/')[-1] in blacklist:
                    continue
                all_links.append([url, children_url])

                # Add the children to the DB
                URLs.set_child(url, children_url)

                # Set the datetime for the url
                # For now it is a string like "Mar 25, 2020"
                result_date = ''
                try:
                    result_date = result['date']
                except KeyError:
                    # There is no date field in the results
                    result_date = ''
                URLs.set_datetime(url, result_date)

                # Set the time we asked for the results
                result_search_date = datetime.now()
                URLs.set_search_datetime(url, result_search_date)

                # Check that the children was not seen before in this call
                try:
                    _ = urls_to_search.index(children_url)
                    # We hav, so ignore
                    print(f'\tRepeated url: {children_url}')
                except ValueError:
                    # The url was not in the list. Append
                    urls_to_search.append(children_url)
                except Exception as e:
                    print(f"Error type {type(e)}")
                    print(f"Error {e}")
            print(f'\tUrls after searching for th {iteration} URL: {urls_to_search}')

        print('Finished with all the graph of URLs')
        print('Final list of urls')
        URLs.show_urls()
        build_a_graph(all_links, args.link)

    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())




