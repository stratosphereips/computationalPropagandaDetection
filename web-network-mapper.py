#!/usr/bin/env python
import os
from datetime import datetime
import requests
import traceback
from serpapi.google_search_results import GoogleSearchResults
import json
import networkx as nx
import argparse
from graph import build_a_graph
from urls import URLs
from utils import get_hash_for_url


# Read the serapi api key
f = open('serapi.key')
SERAPI_KEY = f.readline()
f.close()

def sanity_check(url):
    # Blacklist of pages to ignore
    blacklist = {'robots.txt', 'sitemap.xml'}

    if "sitemap" in url:
        return False
    #Remove general sites like https://www.poolecommunity.com/
    if len(url.split(".")[-1].split("/")[-1])>2:
        return False


    # Apply some black list of the pages we dont want, such as
    # sitemap.xml and robots.txt , because they only have links
    # The page is the text after the last /
    if url.split('/')[-1] in blacklist:
        return False

    if url.split(".")[-1] == ".xml":
        return False
    if "twitter" in url:
        if "status" not in url:
            return False
    if "4chan" in url:
        if "thread" not in url:
            return False

    return True




def trigger_api(search_leyword):
    """
    Access to the API of serapi

    The API can do
        Bing using BingSearchResults class
        Baidu using BaiduSearchResults class
        Yahoo using YahooSearchResults class
        Ebay using EbaySearchResults class
        Yandex using YandexSearchResults class
        GoogleScholar using GoogleScholarSearchResults class

    This api has as parameters
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
        # print(f' == Retriving results for {search_leyword}')
        params = {
                  "engine": "google",
                  "q": search_leyword,
                  "google_domain": "google.com",
                  "api_key": SERAPI_KEY
                }

        # Here we store all the results of all the search pages returned.
        # We concatenate in this variable
        all_results = []

        # Get first results
        client = GoogleSearchResults(params)
        results = client.get_dict()
        # Store this batch of results in the final list
        try:
            all_results.append(results['organic_results'])
            # Since the results came in batches of 10, get all the 'pages'
            # together before continuing
            amount_total_results = results['search_information']['total_results']
            # The amount of results starts with 1, ends with 10 if there are > 10
            amount_of_results_so_far = len(results['organic_results'])
            # print(f' == Total amount of results: {amount_total_results}')
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')
        except KeyError:
            # There are no 'organic_results' for this result
            amount_total_results = 0
            amount_of_results_so_far = 0

        # Threshold of maxium amount of results to retrieve. Now 100.
        # Some pages can have 100000's
        max_results = 100

        # While we have results to get, get them
        while (amount_of_results_so_far < amount_total_results) and \
              (amount_of_results_so_far < max_results):
            # print(' == Searching 10 more...')
            # New params
            params = {
                      "engine": "google",
                      "q": search_leyword,
                      "google_domain": "google.com",
                      "start": str(amount_of_results_so_far + 1),
                      "api_key": SERAPI_KEY
                    }
            client = GoogleSearchResults(params)
            new_results = client.get_dict()
            # Store this batch of results in the final list
            try:
                all_results.append(new_results['organic_results'])
            except KeyError:
                # We dont have results. It can happen because search engines
                # report an amount of results that has a lot of
                # repetitions. So you can only access a part
                # print(f'Error accessing organic results.
                # Results: {new_results}')
                break

            amount_of_results_so_far += len(new_results['organic_results'])
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')

        print(f'\tTotal amount of results retrieved: {amount_of_results_so_far}')
        # Store the results of the api for future comparison
        #modificator_time = str(datetime.) + '_'+ str(datetime.now().hour) + ':' + \
            #str(datetime.now().minute) + ':' + \
            #str(datetime.now().second)
        modificator_time = str(datetime.now()).replace(' ', '_')
        # write the results to a json file so we dont lose them
        if 'http' in search_leyword:
            # we are searching a domain
            for_file_name = search_leyword.split('/')[2]
        else:
            # if a title, just the first word
            for_file_name = search_leyword.split(' ')[0]
        file_name_jsons = 'results-' + for_file_name + '_' + \
            modificator_time + '.json'
        if args.verbosity > 1:
            print(f'Storing the results of api in {file_name_jsons}')
        if not os.path.exists("results"):
            os.makedirs("results")
        with open(os.path.join("results", file_name_jsons), 'w') as f:
            json.dump(results, f)

        return all_results

    except Exception as e:
        print('Error in trigger_api()')
        print(f'{e}')
        print(f'{type(e)}')
        print(traceback.format_exc())



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

    if 'http' in url:
        # We are searching a domain
        for_file_name = url.split('/')[2]
    else:
        # If a title, just the first word
        for_file_name = url.split(' ')[0]

    timemodifier = str(datetime.now().second)
    file = open('contents/' + for_file_name + '_' + timemodifier + '-content.html','w')
    file.write(content)
    file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to check is distribution pattern", type=str)
    parser.add_argument("-p", "--is_propaganda", help="If the URL is propaganda . If absent, is not propaganda.", action="store_true")
    parser.add_argument("-n", "--number_of_levels", help="How many 'ring' levels around the URL we are going to search", type=int)
    parser.add_argument("-c", "--dont_store_content", help="Do not store the content of pages to disk", action="store_true", default=False)
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    args = parser.parse_args()
    try:

        # Create the dot object to plot a graph
        G = nx.Graph()
        # G = nx.cubical_graph()
        # Labels for the nx graph
        labels = {}

        # Get the URLs object
        URLs = URLs('DB/propaganda.db', args.verbosity)

        URLs.add_url(args.link, int(args.is_propaganda))

        # Here we keep the list of URLs still to search
        # We store the level of the URL
        # The level is how far away it is from the original URL that we
        # started from. So the original URL has level 0, and all the
        # URLS linking to it have level 1, etc.
        # We need a list so we can loop through it whil is changing and we
        # need a dictionary to keep the levels. Is horrible to need both!
        # But I dont know how to do better

        # Keep only the urls
        urls_to_search = []
        urls_to_search.append(args.link)
        # Keep the urls and their levels
        urls_to_search_level = {}
        urls_to_search_level[args.link] = 0

        # Here we store all the pair of links as [link, link], so we can
        # build the graph later
        all_links = []

        # Links which failed sanity check
        failed_links = []

        for url in urls_to_search:

            # If we reached the amount of 'ring' levels around the URL
            # that we want, then stop
            # We compared agains the args.number_of_levels - 1 because we always ask and add the leaves
            # So if you want to see only the level 1, we only SEARCH until level 0 (origin URL)
            if urls_to_search_level[url] > args.number_of_levels - 1:
                break

            print('\n==========================================')
            print(f'URL search level {urls_to_search_level[url]}. Searching data for url: {url}')

            # Add this url
            URLs.add_url(url)

            # Get the content of the url and store it
            if not args.dont_store_content:
                content = downloadContent(url)
                URLs.store_content(url, content)

            # Get other links to this URL for the next round (children)
            data = trigger_api(url)

            # From all the jsons, get only the links to continue
            urls = []
            try:
                for page in data:
                    for result in page:
                        urls.append(result['link'])
            except KeyError:
                # There are no 'organic_results' in this result
                # just continue
                pass

            # Set the datetime for the url
            # For now it is a string like "Mar 25, 2020"
            try:
                result_date = result['date']
            except KeyError:
                # There is no date field in the results
                result_date = ''
            URLs.set_datetime(url, result_date)

            if args.verbosity > 1:
                print(f'\tThere are {len(urls)} urls still to search.')

            for child_url in urls:


                if sanity_check(child_url):
                    all_links.append([url, child_url])

                    # Add the children to the DB
                    URLs.set_child(url, child_url)

                    # Set the time we asked for the results
                    result_search_date = datetime.now()
                    URLs.set_search_datetime(url, result_search_date)

                    # Check that the children was not seen before in this call
                    if child_url in urls_to_search:
                        # We hav, so ignore
                        if args.verbosity > 2:
                            print(f'\tRepeated url: {child_url}')
                    else:
                        # The child should have the level of the parent + 1
                        urls_to_search_level[child_url] = urls_to_search_level[url] + 1
                        urls_to_search.append(child_url)
                        if args.verbosity > 1:
                            print(f'\tAdding the URL {child_url} with level {urls_to_search_level[child_url]}')
                else:
                    failed_links.append(child_url)

        print('Finished with all the graph of URLs. Total number of unique links are %d' % (len(all_links)))
        # print('Final list of urls')
        # URLs.show_urls()
        build_a_graph(all_links, args.link)
        if not os.path.exists("removed_urls"):
            os.makedirs("removed_urls")
        with open(os.path.join("removed_urls", get_hash_for_url(args.link)), "w") as f:
            f.write("\n".join(failed_links))

    except KeyboardInterrupt:
        # If ctrl-c is pressed, do the graph anyway
        build_a_graph(all_links, args.link)
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
