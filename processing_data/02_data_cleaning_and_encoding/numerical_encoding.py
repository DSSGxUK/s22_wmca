##################################################################################################
#
# data_preprocessing/02_data_cleaning_and_encoding/05_numerical_encoding.py
#
# Script to examine the numeric EPC data, remove columns with large amounts of
# missing data, and impute others. Will test several imputation methods and 
# test them using a random forrest classifier.
#
##################################################################################################


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import json
import pickle
import requests
from scipy.stats import pearsonr
from tqdm import tqdm
import scipy.stats as stats
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.feature_selection import SelectFromModel
from sklearn.metrics import accuracy_score

import inspect
import gc


# setting random seed for reporducibility. SK learn uses numpy random seed.
random_int = 123
np.random.seed(random_int)


class CleaningNumericData():

	def __init__(self, df=None, percent_missing_threshold=None, 
					parameters_to_drop=None, imputing_columns=None, test_size=0.3, random_int=None):

		self.df = df
		self.percent_missing_threshold = percent_missing_threshold
		self.parameters_to_drop = parameters_to_drop
		self.imputing_columns = imputing_columns
		self.test_size = test_size
		self.random_int = random_int


	def dropping_unnecessary_numeric_columns_and_rows(self):
		'''Dropping columns with more than percent_missing_threshold missing 
			data, as well as some that are deemed uneccesary by EDA.

			INPUTS:
				df: pandas df that has gone through catagorical processing
				percent_missing_threshold (int or float): percent that will be used to eliminate 
											columns. Columns in df containing more than this value 
											in missing data will be dropped.
				other_params_to_drop (str or list of str): other df columns that should be dropped based on 
										other anaylsis besides missing data percentage.

			RETURNS: 
				df: pandas dataframe with appropriate columns dropped.'''

		print('dropping unnecessary numeric columns and rows....')

		self.df = self.df[self.df['current-energy-rating'].notna()] # dropping columns where there is no EPC rating
		self.target = self.df['current-energy-rating']

		percent_missing = self.df.isnull().sum() * 100 / len(self.df)
		for feat, missing in zip(percent_missing.index, percent_missing):
			if missing >= self.percent_missing_threshold:
				self.parameters_to_drop.append(feat)
		
		self.parameters_to_drop.append('current-energy-rating')
		
		self.df.drop(self.parameters_to_drop, inplace=True, axis=1)

		if self.imputing_columns == None:
			self.imputing_columns = self.df.select_dtypes(exclude=['object']).columns.tolist()


	def splitting_into_numeric_and_categorical(self):
		print('splitting into train and test....')

		# segmenting the columns that we don't want to impute
		self.cat = self.df.drop(self.imputing_columns, axis=1)
		self.cat['current-energy-rating'] = self.target

		# getting the columns we want to impute
		self.numeric = self.df[self.imputing_columns]

	
	def iterative_imputing(self):
		'''Performs a train-test split and then iteritivly imputes the missing data in the df. Uses
			the training dataset to fit the imputer and then transforms the traina dn test sets to
			not introduce bias into the testing set. The sets are then concatinated together and
			exported as one dataframe. 

			INPUTS:
				df (pd.df): pandas dataframe containing all data needing imputing.
				iterative_imputing_columns (str, or list of str): list of columns for which the imputing will be performed. Must be numeri columns.
				target (pd.Series): target variable for the model.
				random_state (int): random state to use for reproducibility.
				test_size (float between 0 and 1): fraction of the dataframe that will be split for testing.

			RETURNS:
				df (pd.df): combined dataframe containing the imputed data.
		'''
		self.splitting_into_numeric_and_categorical()

		print('iterative imputing....')
		imp = IterativeImputer(verbose=1, random_state=self.random_int)		# initalizing the imputer
		imp.fit(self.numeric)													# fitting the imputer on the dataframe
		self.numeric = imp.transform(self.numeric)									# transforming the df on the fit imputer

		# turning it into a dataframe
		numeric = pd.DataFrame(self.numeric, columns=self.imputing_columns)

		# putting the imputed columns back together with teh non-imputed columns
		self.df = pd.concat([self.cat, numeric], axis=1, ignore_index=False)


	def process(self):

		self.dropping_unnecessary_numeric_columns_and_rows()
		self.iterative_imputing()

		return self.df  


def main(percent_missing_threshold=None, parameters_to_drop=None, imputing_columns=None, test_size=0.3):
	'''main function tying together all other functions

		INPUTS:
			df (pandas df): dataframe of the data that has gone through catagorical cleaning, 
							CHIAD analysis and catagorical encoding. Will be None if this script 
							is being run in isolation and will then load a preprocessed csv file.
			csv_path (str): path to the preprocessed csv file if there is no DF being loaded.
			percent_missing_threshold (int or float): value used to drop columns missing a certin percentage of missing data.
			parameter_to_drop (str or list of str): parameters to drop from the df due to EDA.
			test_size (float between 0 and 1): fraction of the dataframe that will be split for testing.

		RETURNS:
			imputed_df: dataframe containing the fully processed data. Sequentially seperated into train 
						and test. Bottom (test_size %) is testing data. 
	'''

	print('Loading CSV....')
	df = pd.read_csv('../../data/processed/encoding_categorical.csv')
	if parameters_to_drop == None:
		parameters_to_drop = ['num_households_fuel_poverty','num_households',
								'environment-impact-current','co2-emissions-current',
								'energy-consumption-current']


	numeric_method = numeric_processing(df=df, percent_missing_threshold=percent_missing_threshold, 
												parameters_to_drop=parameters_to_drop, imputing_columns=imputing_columns,
												test_size=test_size, random_int=random_int)

	processed_dataframe = numeric_processing.process(numeric_method)




if __name__ == '__main__':

	main(percent_missing_threshold=90, parameters_to_drop=None, imputing_columns=None, test_size=0.3)

	print('It ran! Good job.')




