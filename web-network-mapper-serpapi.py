#!/usr/bin/env python

import sys
import json
from datetime import datetime
from serpapi.google_search_results import GoogleSearchResults
import traceback


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


def show_results(data: dict):
    """ Show the results received from the search"""
    results = data['results']
    # The structure is, for each entry:
    #     {
    #  "title": "Don't Test Me - XXXTENTACION - LETRAS.MUS.BR",
    #  "link": "https://www.letras.mus.br/xxxtentacion/dont-test-me/",
    #  "description": "XXXTENTACION - Don't Test Me (Letra e mght, dead on ..."
    #     },
    try:
        for result in results:
            print(f"Title: {result['title']}")
            print(f"\tLink: {result['link']}")
            print(f"\tDescription: {result['description']}")
    except Exception as e:
        print('Error in show_results().')
        print(f'Error: {e}')


if __name__ == "__main__":
    search_string = ' '.join(sys.argv[1:])

    """
    This Python package is meant to scrape and parse Google, Google Scholar, Bing, Baidu, Yandex, Yahoo, Ebay results using SerpApi. The following services are provided:
    """


    try:
        print(f'Getting the data from the API for query: {search_string}')
        data = trigger_api(search_string)

        # Read a json to simulate data
        # with open('results.json') as json_file:
        #    data = json.load(json_file)

        # Save json to disk
        modificator_time = str(datetime.now().hour) + ':' + str(datetime.now().minute) + ':' + str(datetime.now().second)

        # Write the results to a json file so we dont lose them
        with open('results-' + modificator_time + '.json', 'w') as f:
            json.dump(data, f)
            print('Json written to file')

        print(data)
        # Show results
        #show_results(data)
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
