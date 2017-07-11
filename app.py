from flask import Flask, render_template, request, redirect
import pandas as pd
import sys
import generate_new_recipe
import os
import numpy as np
import re
import sys


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'app_data')

app = Flask(__name__,static_url_path=STATIC_ROOT)

basefile = os.path.dirname(os.path.realpath(__file__))
filename = basefile+'/app_data/rot_parse_output.cleanednyt_parse_output.cleaned'
#filename = basefile + '/app_data/nyt_parsed2.cleaned'
#networkfilename =basefile+'/app_data/overlap_network.csv.normed'
Nnew = 5
df_ing,df_ing2,df_meta,G = generate_new_recipe.load_data([filename]) #[filename,basefile+'/app_data/te_parse_output']
#cats,counts = np.unique(df_meta[df_meta['recipeCategory']!='']['recipeCategory'],return_counts=True)
df_meta = df_meta[~df_meta.index.duplicated(keep="first")]
cats = pd.read_csv(basefile+'/app_data/nytimes_cat_select.csv')
cats = list(cats[cats.columns[1]])
cats = ['_'.join(c.split()) for c in cats]
ings = pd.read_csv(basefile+'/app_data/common_ing.csv')
ings_id = ['_'.join(i.split()) for i in ings['ing']]

ing_pass = zip(ings['ing'],ings_id)
#print cats
ings_id=None
ings=None

def get_recipe(selected_cat,ing_list):

	#request was a POST
		succeeded,ix,base,extra_something,instructions,meta_ix=generate_new_recipe.generate_recipe(df_ing,df_ing2,G,df_meta,selected_cat,ing_list,Nnew)
		if succeeded:
			table1 = pd.DataFrame(base)
			table1.columns = ['Base Recipe']

			table2 = pd.DataFrame(extra_something)
			table2.columns = ['Additional Ingredients']
			

			header =df_meta.loc[meta_ix,'recipeName']
			print header
			header = header.replace('u0','\u0').encode('ascii')

		else:
			header,table1,table2='','',''
		return succeeded,ix,header,table1,table2,instructions

def string_cleaning(string):
	string = string.replace('u0','\u0')
	string = string.replace('\u003cp\u003e','')
	string = string.replace('\u003','')
	string = string.replace("','","")
	string = string.replace("c/pe'","")
	string = string.replace('/p','')
	string = string.lstrip(',')
	string = string.lstrip("', '")

	return string.decode('utf-8')

@app.route('/index',methods=['GET','POST'])
def index():
    

	if request.method == 'GET':
		selected_cat=''
		return render_template('index.html',\
			cats=[(cat,'selected') if cat==selected_cat else (cat,'') for cat in cats]\
			,ings=ing_pass,header2='',header='')

	else:
		

		selected_cat=request.form.get("Category")
		
		print selected_cat
		print not selected_cat
		if not selected_cat:
			selected_cat='any'

		ingredient_list = request.form.getlist("ingredients")
		#print ingredient_list
		
		if len(ingredient_list)!=0:
			ingredient_list = [' '.join(i.replace(',','').lower().split('_')) for i in ingredient_list]

		print ingredient_list

		succeeded,ix,header,table1,table2,instructions=get_recipe(selected_cat,ingredient_list)
		if succeeded:
			dir_prefix = 'Follow the directions here to make the base dish adding in one or more ingredients from the second table (amounts are guidlines only).'
			return render_template('index.html', tables=[re.sub(r'(u\d)',r'\\\1',table1.to_html(classes="table table-striped")),\
				re.sub(r'(u\d)',r'\\\1',table2.replace('u0','\u0').to_html(classes="table table-striped"))],header=header,link=ix.strip('"').lstrip('"'),\
				cats=[(cat,'selected') if cat==selected_cat else (cat,'') for cat in cats],\
				directions=[dir_prefix]+[string_cleaning(s)\
				for s in instructions.split('.')],\
				ings=ing_pass,\
				header2 = 'Directions')

		else:
			return render_template('index.html',cats=[(cat,'selected') if cat==selected_cat else (cat,'') for cat in cats] \
				,ings=ing_pass,error=True)

## api logic 
'''
@app.route('/api/v1.0/gen_recipe', methods=['POST'])
def get_recipe_api():
    if not request.json:# or not 'title' in request.json:
        abort(400)
    
    ix,header,table1,table2=get_recipe(cats)

    outdict = {'base link':ix.strip('"').lstrip('"'),'header':header,'base recipie':list(table1['Base Recipe']),'additional ingredients':list(table2['Additional Ingredients'])}
    
    return jsonify(outdict), 201
'''

if __name__ == '__main__':

  app.run(debug=True)
