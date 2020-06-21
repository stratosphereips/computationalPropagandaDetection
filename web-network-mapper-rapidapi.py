#!/usr/bin/env python

import sys
import json
import requests
from datetime import datetime


RAPIDAPI_HOST = "google-search3.p.rapidapi.com"
RAPIDAPI_URL = "https://google-search3.p.rapidapi.com/api/v1/search"
f = open('rapidapi-api.txt')
RAPIDAPI_KEY = f.readline()[:-1]
f.close()


def trigger_api(search_leyword):
    payload = "{  \"q\":\"" + search_leyword + "\",  \"max_results\":  10}"
    headers = {
          'x-rapidapi-host': RAPIDAPI_HOST,
          'x-rapidapi-key': RAPIDAPI_KEY,
          'content-type': "application/json",
          'accept': "application/json"
        }

    response = requests.request("POST", RAPIDAPI_URL, data=payload,
                                headers=headers)

    if(200 == response.status_code):
        return json.loads(response.text)
    else:
        return None


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

        # Show results
        show_results(data)
    except Exception as e:
        print(f"Error in main(): {e}")
