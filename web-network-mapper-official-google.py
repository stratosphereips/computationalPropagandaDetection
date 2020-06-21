#!/usr/bin/env python

import sys
import json
from datetime import datetime
import pickle
from googleapiclient.discovery import build 


def show_results(data: dict):
    """ Show the results received from the search"""
    results = data
    try:
        for result in results:
            print(f"Title: {result['title']}")
            print(f"\tLink: {result['link']}")
            print(f"\tDescription: {result['description']}")
    except Exception as e:
        print('Error in show_results().')
        print(f'Error: {e}')


def google_query(query, api_key, cse_id, **kwargs):
    query_service = build("customsearch",
                          "v1",
                          developerKey=api_key
                          )
    # This is a complex API, we can for example
    # linkSite, string, Specifies that all search results should contain a link to a particular URL.
    # num, Valid values are integers between 1 and 10, inclusive.
    # start

    query_results = query_service.cse().list(q=query,    # Query
                                             cx=cse_id,  # CSE ID
                                             **kwargs
                                             ).execute()
    return query_results['items']


if __name__ == "__main__":
    try:
        # Load private api keys
        f = open('api-google.txt')
        # First line is the google api key
        api_key = f.readline()[:-1]
        # Second line is the custom search engine api key
        cse_id = f.readline()[:-1]

        # Get the search string from the parameters
        search_string = ' '.join(sys.argv[1:])

        my_results_list = []

        print('First batch of results')
        my_results = google_query(search_string,
                                  api_key,
                                  cse_id,
                                  num=10,
                                  )
        print(type(my_results))
        for result in my_results:
            my_results_list.append(result)
            print('---------------')
            print(result)

        with open('google-results.pickle', 'wb') as handle:
            pickle.dump(my_results_list, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # Show results
        #show_results(data)
    except Exception as e:
        print(f"Error in main(): {e}")



