
import networkx as nx
from DB.propaganda_db import DB
import matplotlib.pyplot as plt


if __name__ == '__main__':
    db = DB("DB/propaganda_sebas.db")
    links = db.c.execute("""SELECT PARENT_ID, CHILD_ID from LINKS""").fetchall()
    G = nx.DiGraph()
    G.add_edges_from(links)
    nx.draw_spring(G)
    plt.savefig("graph_spring.png")