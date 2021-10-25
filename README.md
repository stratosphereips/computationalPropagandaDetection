# Computational Propaganda Detection Tool

A set of tools to work on computational propaganda detection

## Running script

    python web-network-mapper.py -l LINK -n NUMBER_OF_ITERATIONS -p (include if it is propaganda)

Example of propaganda

    python web-network-mapper.py -l https://euvsdisinfo.eu/report/despite-promises-to-the-contrary-nato-has-been-expanding-further-eastwards/ -p -n 30


Build a graph

    python graph.py -l LINK

Query the DB for the links to a particular URL

    DB/query_db.py -l LINK

## How we get the info

- We use the serapi api.
- We download the results from one seed url
- For each result
	- We filter that is not in our blacklist
	- We download its content with curl
	- We store its datetime of search from the engine
	- We store its datetime of our search
	- We ask the links to this page and we loop.


## Blacklist
We apply some blacklisting of webpages based on some criteria in order to know which pages should be considered good links.

# Packages you need
- See requirements.txt

## Useful Info
- https://towardsdatascience.com/current-google-search-packages-using-python-3-7-a-simple-tutorial-3606e459e0d4

## Database structure

### Table LINKS
Table links has the following fields: 

- link_id:
- parent_id:
- child_id:
- date:
- source: Twitter, Facebook, Webpage (this is any generic webpage), VK, Reddit, etc.
- linktype:

## Extraction of Features

The features that we are extracting from each graph are:

1. Time histograms
    Generate the features based on time
    - For each level:
        - Calculate a histogram of how many links there are by:
            - In the next 48hs after the publication date of the main URL (2 days). 
                - Compute the histogram of urls published by minute
            - After more than 48hs of the publication, for the next 120hs (5 days), that is from > 2nd day to <= 7th day.
                - Compute the histogram of urls published by hour
            - After more than 168hs of the publication, for the next 23 days, that is from > 7th day to <= 30th
                - Compute the histogram of urls published by day

              ```Publication of    Up to                        More than 48hs
              main URL          48hs hs                      and up to 120hs
                    | By minute |         By hour             |                    By day
                    \/          \/                            \/
            Days: |--*--|-----|--*--|-----|-----|-----|-----|--*--|-----|-----|-----|-----|-----|-----|-----|-----|-----|
                     1     2     3     4     5     6     7     8     9    10    11    12    13    14    15    16   17...```

2. The number of urls published before the source

3. The total number of urls in each level 













