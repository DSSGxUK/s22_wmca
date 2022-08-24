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
from pandas_profiling import ProfileReport
import json
import pickle
import requests
from scipy.stats import pearsonr
from tqdm import tqdm
import scipy.stats as stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import KNNImputer, SimpleImputer, IterativeImputer
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split, cross_val_score
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


	def splitting_into_train_and_test(self):
		print('splitting into train and test....')

		# splitting the training and testing set
		self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.df, self.target, test_size=self.test_size, random_state=self.random_int, stratify=self.target)
		
		self.y_train.reset_index(inplace=True, drop=True)
		self.y_test.reset_index(inplace=True, drop=True)
		self.X_train.reset_index(inplace=True, drop=True)
		self.X_test.reset_index(inplace=True, drop=True)
		# segmenting the columns that we don't want to impute
		cat_train = self.X_train.drop(self.imputing_columns, axis=1)
		cat_test = self.X_test.drop(self.imputing_columns, axis=1)
		cat_train['current-energy-rating'] = self.y_train
		cat_test['current-energy-rating'] = self.y_test

		# putting the data back together so we can concatinate it with the imputed data
		self.catagorical = pd.concat([cat_train, cat_test], axis=0).reset_index(drop=True)

		# getting the columns we want to impute
		self.X_train = self.X_train[self.imputing_columns]
		self.X_test = self.X_test[self.imputing_columns]


	
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
		self.splitting_into_train_and_test()

		print('iterative imputing....')
		imp = IterativeImputer(verbose=1, random_state=self.random_int)		# initalizing the imputer
		imp.fit(self.X_train)													# fitting the imputer on the dataframe
		self.X_train = imp.transform(self.X_train)									# transforming the df on the fit imputer
		self.X_test = imp.transform(self.X_test)										# transforming the df on the fit imputer

		# putting the testing and training data back together for saving as a csv. 
		X = np.concatenate((self.X_train, self.X_test),axis=0)

		# turning it into a dataframe
		numeric = pd.DataFrame(X, columns=self.imputing_columns)

		# putting the imputed columns back together with teh non-imputed columns
		self.df = pd.concat([self.catagorical, numeric], axis=1, ignore_index=False)


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

		# imputing_columns = ['floor-height', 'mainheat-energy-eff', 
		# 			'glazed-type', 'mainheatcont-description', 'property-type', 'energy-tariff', 'mechanical-ventilation', 'postcode', 
		# 			'solar-water-heating-flag', 'constituency', 'number-heated-rooms', 'floor-description', 'local-authority', 
		# 			'built-form', 'number-open-fireplaces', 'windows-description', 'glazed-area', 'mains-gas-flag', 
		# 			'roof-energy-eff', 'total-floor-area', 'roof-description', 'number-habitable-rooms',  
		# 			'main-fuel', 'multi-glaze-proportion', 
		# 			'transaction-type', 'mainheat-description', 'extension-count', 'wind-turbine-count', 'tenure',  
		# 			'walls-description', 'hotwater-description', 'num_meter', 'total_consumption', 
		# 			'mean_counsumption', 'median_consumption', 'prop_households_fuel_poor', 'LATITUDE', 'LONGITUDE', 
		# 			'photo-supply-binary', 'secondheat-description', 'lighting-description']


	numeric_method = numeric_processing(df=df, percent_missing_threshold=percent_missing_threshold, 
												parameters_to_drop=parameters_to_drop, imputing_columns=imputing_columns,
												test_size=test_size, random_int=random_int)

	processed_dataframe = numeric_processing.process(numeric_method)

	# attrs = (getattr(processed_dataframe, name) for name in dir(processed_dataframe))
	# print(attrs)


	print(processed_dataframe)
	# print(processed_dataframe.isnull().sum())



if __name__ == '__main__':

	main(percent_missing_threshold=90, parameters_to_drop=None, imputing_columns=None, test_size=0.3)

	print('It ran! Good job.')



# The columns that were removed.
#
# ['windows-env-eff', 'lighting-energy-eff','hot-water-env-eff','mainheatc-energy-eff','lighting-env-eff','windows-energy-eff',
#  'roof-env-eff','walls-energy-eff', 'photo-supply','mainheat-env-eff','current-energy-rating','walls-env-eff', 'lighting-cost-current',
#  'mainheatc-env-eff', 'hot-water-energy-eff', 'low-energy-lighting','msoa_code', 'lsoa_code', 'percentage-low-energy-lighting']
#
#
# 'floor-thermal-transmittance', 'walls-thermal-transmittance', 'roof-thermal-transmittance', 
#



