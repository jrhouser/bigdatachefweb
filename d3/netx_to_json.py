import pandas as pd
import sys
import networkx as nx
import numpy as np
import json
import heapq

def update(n,node,q,node_list):

	if n not in node:
			node[n]=q
			node_list.append({"name":n})
			q=q+1
	return q,node,node_list


def network_sub(filename,seed,seednode):
	G=nx.read_gpickle(filename)

	nodes = G.nodes()
	master_nodes = list(nodes)
	
	


	node_reference = {}
	node_list=[]
	connection_list=[]
	
	q=0

	nodes = G[seednode].keys()

	n = seednode

	tmpl = []
	for m in nodes:
		
		heapq.heappush(tmpl,(G[n][m]['weight'],n,m))
		if len(tmpl)>seed:
			heapq.heappop(tmpl)

	tmpl2=[]
	for w,n,m in tmpl:

		q,node_reference,node_list=update(n,node_reference,q,node_list)
		q,node_reference,node_list=update(m,node_reference,q,node_list)
		connection_list.append((n,m))

		for l in G[m].keys():
			heapq.heappush(tmpl2,(G[m][l]['weight'],m,l))
			if len(tmpl2)>seed:
				heapq.heappop(tmpl2)
	
	tmpl1=None
	for w,n,m in tmpl2:

		q,node_reference,node_list=update(n,node_reference,q,node_list)
		q,node_reference,node_list=update(m,node_reference,q,node_list)
		connection_list.append((n,m))
	tmpl2 = None


	connection_list=list(set(connection_list))


	connection_out=[]
	for n,m in connection_list:
		connection_out.append({"source":node_reference[n],"target":node_reference[m]})

	## write files
	with open('net_nodes.json', 'w') as outfile:
		json.dump(node_list, outfile)

	with open('net_connections.json', 'w') as outfile:
		json.dump(connection_out, outfile)

if __name__=="__main__":


	filename = sys.argv[1]

	if len(sys.argv)<4:
		seed = 8 #number of nodes to seed demonstration network with
		seednode = 'avocado'
	else:
		seed = int(sys.argv[2])
		seednode = sys.argv[3]

	network_sub(filename,seed,seednode)




