In this folder there are some special graphs created by notebooks. Every folder contains notebook that created the graphs.

Meaning of colors: Unless specified otherwise, colors refer to level of url, red for level 0, blue for level 1, green for level 2.

## URLS of single tool query publish date difference in edge length
Graphs here are simple: Every url in a database is single node, color coreesponds to level. Edge (a->b) means a is referenced by b. Edge length encodes the absolute day difference when the urls were published.

## DATES and when two articles referencing each other were published
Every node here coresponds to a date. There are two kinds of edges. Gray (a->b) stands for a is the date just before b). Blue (a->b) means something published at a is referenced by b. There is also a two level variant, both levels represent the same timeline. Referencing edges are than easier to view.

## DOMAINS Which domains reference each other in single Tool query
For every url its domain is extracted and showed as a node. Since multiple urls might be contained in one node, color refers to the lowest url level. Sizze of the node show how many times the domain is in the database. If there is a link (a links b) in the database, there is an between domain a and domain b. Width of the edge increases if there are more links between the two domains.

## DOMAINS distribution of single propaganda in all non_propaganda
The graph nodes and edges are the same as in Web centered. Here however we combine more databases - all non-propaganda databases and one propaganda database. Purely non-propaganda domains are green, purely propaganda domains are red, if one domain is both non-propaganda and propaganda, the node is orange.

## DOMAINS with SNA features for all dataset
Again the same concept as in Web centered. Size of a node shows different Social Network Analysis centrality.

## URLS graph with timeline
Different versions of graphs where timeline is shown. Readme in the folder.