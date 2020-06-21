#!/usr/bin/env python

import sys
import json
from datetime import datetime
from googlesearch import search
import pickle

if __name__ == "__main__":
    try:
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
        f = open('results.freegoogle.txt', 'w')
        data = search(search_string, tld="com", num=200, stop=200, pause=2)
        for j in data:
            print(j)
            f.write(j + '\n')
        f.close()

    except Exception as e:
        print(f"Error in main(): {e}")
