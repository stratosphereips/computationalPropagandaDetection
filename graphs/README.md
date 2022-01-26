## DOMAIN-CENTERED-GRAPH
color_scheme of nodes
red: level 0 url
blue: level 1 url
green: level 2 url

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
