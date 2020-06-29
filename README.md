# Computational Propaganda Detection Tool

A set of tools to work on computational propaganda detection


## Useful Info
- https://towardsdatascience.com/current-google-search-packages-using-python-3-7-a-simple-tutorial-3606e459e0d4


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
If the ending page of the URL is one of these, we ignore it
- robots.txt
- sitemap.xml


# Packages you need
- brew install graphviz
