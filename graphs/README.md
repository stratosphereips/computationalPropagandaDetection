All graphs in the experiments folder are created by jupyter notebooks in folder jupyter notebooks.

color_scheme is the same in all the graphs (with exception of TIMELINE_GRAPH)
red: level 0 url
blue: level 1 url
green: level 2 url

## DOMAIN-CENTERED-GRAPH
The final version, function graph.create_domain_centered,  generated automatically when using web-network-mapper 
Here the concept of a date and levels is dropped. Nodes represent a domain. If in our database is bbc.com multiple times 
(in multiple links, might be different urls: bbc.com/X, bbc.com/Y) the size of the node is increased. Colors correspond to the lowest level of the domain 
(if url0 in level0 is referenced by url1, but both urls are on the same domain, there is a self loop and the node has multiple levels)
Edge is when there is a link between domain1 and domain2, width is the number of such links in the entire search tree. 
Created by graph.create_domain_centered

## TIMELINE_CENTERED_GRAPH
The final version, function graph.create_timeline_centered, that is generated automatically when using web-network-mapper, this is created by graph.create_date_centered.
Gray nodes represent timeline with red mark on the original query date, green mark is the day of running the tool to distinguish future dates (future publishing dates are note possible, but we want to keep them), future dates are also darker and smaller. Yellow mark is *anything older than timeline window*.
All other visible nodes correspond to level 1 urls - all urls referencing level0 (original query) url. Color of the node means if the reference is by title (green) or url (red).
If there is an level2 url published on date *d* referencing level 1 url, there is an edge between level1 url and *d*, color of the edge again refers to the relation of the reference: green for title and red for link. It can happen that multiple level2 urls published on the same date reference the same level1 url, in that case corresponding edge is wider (and number on the edge) and if there are references by both url and title the color is purple. 
Published date of level1 url is visualized as a dashed edge. 
Node distance from the timeline is logarithm as number of times the url was referenced (#edges + any urls that we do not have published date of), the number is also seen by hovering mouse over a node

Small nodes near the timeline are level 1 edges with no level2 urls referencing them.
### expermented with:

#### dates_as_edge_length: 
If two urls are linked and both have dates, there is an edge scaled as the the absolute day difference between publications

####  basic_timeline
Level 0 url is not visible (every level 1 url is by definition connected to level 0), edges between level 1 and linked 
level 2 urls are hidden (but we can see the clusters), Gray nodes represent individual dates, each gray edge is when corresponding url was published.

#### level_timeline
similar concept as *basic_timeline*, however level 2 urls are hidden. If there is a level 2 url (published at day *d*) referencing a level 1 url, there is an edge (level 1 url, *d*)
Moreover there are two special dates visible, red: published date of level 0 (the original) url, yellow: *old date*, everything published before *old date* is linking to this date, the reason is that if there is one url published 20 years ago it moves the entire graph a lot to the right.
Small blue nodes correspond to level 1 urls where there is no level 2 url referencing them.

#### only_dates
Every node is a date. If there is an url1 published at *d1* and there is url2 published at *d2* that references the url1, there is an edge (*d1*, *d2*) 

#### two_level_only_dates
There are two timelines top and bottom, idea is the very same as in *only_dates*, however for visualizing the *d1* is in the upper timeline, *d2* is below

