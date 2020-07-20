# Computational Propaganda Detection Tool

A set of tools to work on computational propaganda detection

## Running scirpt

```python web-network-mapper.py -l LINK -n NUMBER_OF_ITERATIONS -p (include if it is propaganda)```

Example of propaganda

```python web-network-mapper.py -l https://euvsdisinfo.eu/report/despite-promises-to-the-contrary-nato-has-been-expanding-further-eastwards/ -p -n 30```


Build a graph

```python graph.py -l LINK```

Query the DB for the links to a particular URL

```DB/query_db.py -l LINK```

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

