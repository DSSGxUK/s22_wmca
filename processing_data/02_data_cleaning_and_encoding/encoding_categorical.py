import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
import inspect
# from itertools import ifilter

class EncodingCategorical():
	def __init__(self, df, PLOT_PATH):
		self.df = df
		self.PLOT_PATH = PLOT_PATH

	def encode_datetime(self):
		# Convert to ordinal for regression
		self.df['inspection-date'] = self.df['inspection-date'].astype('datetime64[ns]').map(dt.datetime.toordinal)
		self.df['lodgement-datetime'] = self.df['lodgement-datetime'].astype('datetime64[ns]').map(dt.datetime.toordinal)
		self.df['original-postcode'] = self.df['postcode'].copy()
		self.df['original-local-authority'] = self.df['local-authority'].copy()
		self.df['original-constituency'] = self.df['constituency'].copy()
		self.df['original-msoa_code'] = self.df['msoa_code'].copy()
		self.df['original-lsoa_code'] = self.df['lsoa_code'].copy()


	def encode_categorical(self):
		self.cat_var = self.df.select_dtypes(include= ['object']).columns.tolist()

		print(self.cat_var)
		# High missing values 
		self.df.drop(columns=['floor-level'], inplace=True)
		self.cat_var.remove('floor-level')
		self.cat_var.remove('original-constituency')
		self.cat_var.remove('original-local-authority')
		self.cat_var.remove('original-postcode')
		self.cat_var.remove('original-msoa_code')
		self.cat_var.remove('original-lsoa_code')

		# not these
		self.cat_var.remove("current-energy-rating")
		self.cat_var.remove('address')

		# Change categorical variable to numbers
		ranked_var = [col for col in self.cat_var if '-eff' in col]
		if 'current-energy-efficiency' in ranked_var:
			ranked_var.remove('current-energy-efficiency')
		rank = ['Very Poor', 'Poor', 'Average', 'Good', 'Very Good', np.nan]

		for var in ranked_var:
			self.df[var] = self.df[var].apply(lambda x: rank.index(x))
			self.df[var].replace(len(rank)-1, np.nan, inplace=True)

		glazed_rank = ['Much Less Than Typical', 'Less Than Typical', 'Normal', 
						'More Than Typical', 'Much More Than Typical', np.nan]
		self.df['glazed-area'] = self.df['glazed-area'].apply(lambda x: glazed_rank.index(x))
		self.df['glazed-area'].replace(len(glazed_rank)-1, np.nan, inplace=True)

		# Define non-ordinal categories
		self.ordinal_var = ranked_var + ['construction-age-band', 'glazed-area']
		print('Ordinal Var: '+str(self.ordinal_var))
		print('Len ordinal var: '+str(len(self.ordinal_var)))
		non_ordinal_var = [col for col in self.cat_var if col not in self.ordinal_var]

		print('Non-Ordinal Var: '+str(non_ordinal_var))
		print('Len non-ordinal var: '+str(len(non_ordinal_var)))
		# non_ordinal_var.remove('mainheat-description')

		# Visualising cardinality to prevent code breaking
		cardinality = self.df[non_ordinal_var].nunique()
		
		# fig = plt.figure(figsize=(20,10))
		# plt.bar(cardinality)
		# plt.set_xlabel('Variable')
		# plt.set_ylabel('Number of unique values')
		# plt.savefig(self.PLOT_PATH, 'cardinality_hist.png')
		
		input('Check cardinality to continue. Edit nunique limit as necessary.')

		self.encode_non_ordinal(non_ordinal_var)

	def encode_non_ordinal(self, non_ordinal_var, nunique_limit=18):
		# One hot encode non-ordinal variables

		for var in non_ordinal_var:
			if len(self.df[var].unique()) < nunique_limit:
				mask = self.df[var].isna()
				one_hot_encoded = pd.get_dummies(self.df[var])
				one_hot_encoded = one_hot_encoded.add_prefix(str(var+'_'))
				self.df = pd.concat([self.df, one_hot_encoded], axis=1)
				self.df.drop(var, inplace=True, axis=1)
				# self.df[var] = one_hot_encoded.to_numpy().tolist()
				# print(self.df[var])
				# self.df[var][mask] = np.nan
				# print(self.df[var][mask])
			# High cardinality will break code
			elif self.df[var].isna().sum() == 0:
				label_encoder = LabelEncoder()
				self.df[var] = label_encoder.fit_transform(self.df[var])
			else:
				categories = list(self.df[var].unique())
				self.df[var] = self.df[var].apply(lambda x: categories.index(x))
				self.df[var].replace(len(categories)-1, np.nan, inplace=True)

		return self.df

	def process(self):

		self.encode_datetime()
		self.encode_categorical()

		print(self.df.columns.tolist())

		return self.df

def main(df, PLOT_PATH):
	cleaning = EncodingCategorical(df, PLOT_PATH)
	attrs = (getattr(cleaning, name) for name in dir(cleaning))
	# methods = ifilter(inspect.ismethod, attrs)
	# for method in methods:
	# 	method()

if __name__ == "__main__":
	main()