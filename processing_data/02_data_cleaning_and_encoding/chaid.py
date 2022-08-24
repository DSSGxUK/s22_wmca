import pandas as pd
import pickle
import numpy as np
from CHAID import Tree

class CHAIDGrouping():
	def __init__(self, df, OUTPUT_PATH):
		self.df = df
		self.cat_var = ['mainheatcont-description', 'walls-description', 'hotwater-description', 
						'floor-description', 'windows-description', 
						'roof-description', 'secondheat-description', 'main-fuel', 'transaction-type',
						'energy-tariff']
		self.chaid_dict = {}
		self.OUTPUT_PATH = OUTPUT_PATH

	def chaid(self):
		"""
		Run the CHAID algorithm.
		Set the inputs and outputs.
		The inputs are given as a dictionary along with the type.
		The output must be of string type.
		"""
		for var in self.cat_var:
			#I have assumed all features are nominal, we can change the features dictionary to include the ordinal type
			features = {var:'nominal'}
			label = 'current-energy-efficiency'
			#Create the Tree
			self.chaid_dict[var] = {}
			tree = Tree.from_pandas_df(self.df, i_variables = features, d_variable = label, alpha_merge = 0.0)
			#Loop through all the nodes and enter into a dictionary
			print('\n\n\nVariable: %s' % var)
			print('p-value: %f' % tree.tree_store[0].split.p)
			print('Chi2: %f' % tree.tree_store[0].split.score)
			for i in range(1, len(tree.tree_store)):
				count = tree.tree_store[i].members[0] + tree.tree_store[i].members[1]
				if count != 0:
					rate = tree.tree_store[i].members[1] / count
					print('\nNode %i:\n\tCount = %i\tRate = %f' % (i,count,rate))
					print('\t%s' % tree.tree_store[i].choices)
				self.chaid_dict[var]['node' + str(i)] = tree.tree_store[i].choices

		with open(self.OUTPUT_PATH+'chaid_dict.pkl', 'wb') as handle:
			pickle.dump(self.chaid_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

	def group_values(self):
		"""Replace values using this naive method to group levels together. Will process more next iteration."""
		self.cat_var.remove('transaction-type')	# Grouping doesn't make sense + small enough

		for var in self.cat_var:
			var_dict = {}
			for k, v in self.chaid_dict[var].items():
				var_dict.update(dict.fromkeys(v, k))
				self.df[var].replace(var_dict, inplace=True)

		floor_level_dict = dict.fromkeys(['1','2','3','4'],'low floors')
		floor_level_dict.update(dict.fromkeys(['-1', 'Ground']))
		floor_level_dict.update(dict.fromkeys(['mid floor','5','6','7','8','9','10','11'],'mid floors'))
		floor_level_dict.update(dict.fromkeys(['top floor','12','13','14','15','16','17','18','19','20',
											'21 or above', '20+'],'upper floors'))
		self.df['floor-level'].replace(floor_level_dict, inplace=True)

		glazed_dict = dict.fromkeys(['double glazing installed before 2002','double glazing, unknown install date'],'old double glazing')
		glazed_dict.update(dict.fromkeys(['triple, known data','triple glazing'],'triple glazing'))
		glazed_dict.update(dict.fromkeys(['secondary glazing','not defined','single glazing'],'old glazing'))
		glazed_dict.update(dict.fromkeys(['double, known data','double glazing installed during or after 2002'],'double glazing'))
		self.df['glazed-type'].replace(floor_level_dict, inplace=True)

	def process(self):

		self.chaid()
		self.group_values()

		return self.df

def main(df, OUTPUT_PATH):
	grouping = CHAIDGrouping(df, OUTPUT_PATH)
	grouping.chaid()
	grouping.group_values()

if __name__ == "__main__":
	main()



