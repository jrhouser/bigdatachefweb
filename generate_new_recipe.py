import pandas as pd
import numpy as np
import sys
import networkx as nx
import time
from collections import defaultdict
import copy

MAX_NEIGHBORS = 3 #only get top N connected neighbors when considering 
MAX_TRIES = 100
EXTRA_ING = 5

def load_data(filename):


	df_ing = pd.read_csv(filename[0],sep="$",error_bad_lines=False).set_index('link')

	df_ing = df_ing[['ingredient','og ingredient']]
	new_ix=[]
	for ix in df_ing.index:
		new_ix.append(ix.replace('"',''))
	df_ing.index=new_ix

	G = nx.read_gpickle(filename[0]+'.normed.network.abc.pk')#,delimiter='$')
	if len(filename)>1:
		print 'true'
		df_ing2 = pd.read_csv(filename[1],sep="$",error_bad_lines=False)
		df_ing2 = df_ing2[['link','og ingredient']]

	else:
		df_ing2 = []

	df_meta = pd.read_csv(filename[0]+'.meta_data.csv').set_index('link').fillna('')
	df_meta=df_meta[['recipeCategory','recipeInstructions','recipeName']]

	df_meta = df_meta[df_meta['recipeInstructions']!='']

	return df_ing,df_ing2,df_meta,G

def generate_recipe(df_ing,df_ing2,G,df_meta,cat,ing_list,Nnew):
	

	#### init and quality checks ####
	np.random.seed(int(time.time())) #seed random number generator

	df_meta = check_intersection(df_meta,df_ing) #double check that there are no missing recipes in df_ing. probably uncessary.
	
	df_ing['ingredient']=df_ing['ingredient'].str.lower() #probably uncessary at this point.

	cat = ' '.join(cat.split('_')) # replace underscore with spaces.

	##### --- #### 

	if cat!='any' and len(ing_list)==0:  
		# we are selecting based upon category so only keep recipes with that category.
		meta_current_ix = list(set(df_meta[df_meta['recipeCategory']==cat].index))
	else:
		meta_current_ix = list(set(df_meta.index))

	if len(ing_list)!=0:	
		meta_current_ix=recipe_candidates(G,ing_list,meta_current_ix,df_ing) 

		if meta_current_ix==False:
			return False,'','','','','' #error handling. couldn't find recipes that were in the neighboorhood of those ingredient combinations.


	extra_something = []
	while len(extra_something)==0:
		base,og_ing,instructions,core_ing,meta_ix,ix=pick_a_recipe(meta_current_ix,df_meta,df_ing,df_ing2)

		extra_something=get_new_ingredients(df_ing,df_ing2,G,df_meta,cat,ing_list,Nnew,meta_current_ix,core_ing)
	

	return True,ix,base,list(set(extra_something)),instructions,meta_ix



def recipe_candidates(G,ing_list,meta_current_ix,df_ing):
	

	candidate_ix=meta_current_ix
	neighbors = []
	weights = []
	
	# get list of neighbors for the ingredients.
	for i in ing_list:

		if i in G:
			neighbors.extend(G[i].keys())
			weights.extend(G[i].values())

	weights = [w['weight'] for w in weights]
	weights = np.array(weights)/sum(weights)
	# get a list of neighbors that are porportional to the weights.
	idx = np.random.choice(range(len(weights)),size=MAX_NEIGHBORS,p=weights)

	mask=[]
	
	for i in idx:
		n = neighbors[i]
		if len(mask)==0:
			mask=df_ing['ingredient']==n
		else:
			mask+=df_ing['ingredient']==n

	for i in ing_list:
		mask+=df_ing['ingredient']==i

	possible_ix = df_ing[mask].index
	candidate_ix = list(set(candidate_ix).intersection(set(possible_ix)))

	#couldn't find any recipes in the neighborhood of the ingredients selected.
	if len(candidate_ix)==0:
		return False

	return candidate_ix



def check_intersection(df_meta,df_ing):

	drop=[]
	for ix in df_meta.index:
		if ix not in df_ing.index:
			drop.append(ix)
	df_meta=df_meta.drop(drop)

	return df_meta

def pick_a_recipe(meta_current_ix,df_meta,df_ing,df_ing2):
	
	k=0
	try_again = True
	while try_again and k<MAX_TRIES:
		k+=1
		try_again = False
		ix = np.random.choice(meta_current_ix) 
		instructions = df_meta.loc[ix,'recipeInstructions'] # get instructions
		meta_ix = ix
		ix=ix.replace('"','') #clean up string.
		core_ing = df_ing.loc[ix,'ingredient']


		if len(df_ing2)==0:
			og_ing = df_ing.loc[ix,'og ingredient']
		else:
			og_ing = df_ing2.loc[ix,'og ingredient']

		#print og_ing
		if  type(og_ing)==str:
			base = og_ing
		
		elif type(og_ing)=='float' :
			try_again = True
		else:
			try:
				base = og_ing.values
			except:
				try_again = True

	return base,og_ing,instructions,core_ing,meta_ix,ix

def get_new_ingredients(df_ing,df_ing2,G,df_meta,cat,ing_list,Nnew,meta_current_ix,core_ing):


	## main loop 
	new_igs=[]
	extra_something = []
	
	### pre populate the list of extra ingredients with any user supplied ingredients. ###
	if len(ing_list)!=0:

		extra_something_candidates = list(set(ing_list)-set(core_ing))

		extra_something = []
		for e in extra_something_candidates:
			candidate = np.random.choice(df_ing[df_ing['ingredient']==e]['og ingredient'].values)
			extra_something.append(candidate)

	j = 0
	
	### --- ###
	ing_seed_n = 3
	while len(extra_something)<EXTRA_ING and j<MAX_TRIES:
		j +=1
		print j

		
		### select a random ingredient from the base recipe ###
		if type(core_ing)==str:
			selected_core_ing = core_ing
		else:
			try:
				selected_core_ing = np.random.choice(list(core_ing),size=min([ing_seed_n,len(list(core_ing))]))
			except:
				break
		### --- ###
		#print selected_core_ing
		### crawl the network for new  ingredients ###
		selected_core_ing = list(selected_core_ing)
		for s in selected_core_ing:
			if s not in G:
				selected_core_ing.remove(s)
		

		if len(selected_core_ing)>0:

			B = []
			for s in selected_core_ing:
				#get current sub-graph
				if s in G:

					if type(s)==np.string_ and 'nan'!=s:

						if len(B)==0:
							B=G[s]
							print len(B)
						else:
							Bold = B.copy()
							B = G[s]
							keys_a = list(Bold.keys())
							B = dict((key,value) for key, value in B.iteritems() if key in keys_a)
							print len(B)

			if len(B)>0:
				#normalize selected weights to 1

				p_new_igs = np.array([float(B[k]['weight'])*1.0  for k in B.keys() if 'weight' in B[k]])
				p_new_igs = p_new_igs/float(sum(p_new_igs))
				#ig = np.random.choice(B.keys(),p=p_new_igs)


				ig ='asdfasd'
				trys=0
				failed = False
				while ig not in list(df_ing['ingredient']):
					ig = np.random.choice(B.keys(),p=p_new_igs)
					if trys>len(B.keys()):
						failed=True
						break

					trys+=1
				#if not failed:
				candidate = np.random.choice(df_ing[df_ing['ingredient']==ig]['og ingredient'].values)

				if not is_in_dish(candidate,core_ing):

					extra_something.append(candidate)
					new_igs.append(True)

			

	
	return list(set(extra_something))


def is_in_dish(candidate,core_ing):
	s1=candidate.split()
	overlapping=False
	# test for an ingredient that is already in the main dish.
	for c in core_ing:
		if type(c)==str:
			s2=c.split()

			L1=len(set(s1).intersection(set(s2)))
			L2=min([len(s1),len(s2)])
			if L2==0.0:
				L2=max([len(s1),len(s2)])
			if 1.0*L1/L2>0.6:
				overlapping=True

	return overlapping

'''
def failed_lookup():
			ig ='asdfasd'
			trys=0
			failed = False
			while ig not in list(df_ing['ingredient']):
				ig = np.random.choice(B.keys(),p=p_new_igs)
				if trys>len(B.keys()):
					failed=True
					break

				trys+=1
'''
			
