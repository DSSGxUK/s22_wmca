######################################################################################
#
#	model/combining_data_and_seperating_epc.py
#	
#	File that takes in the processed data from the merging of the OS map/fuel_poverty/
# 	energy_consumption data and merges it with the EPC database. This is done so
# 	the EPC data can get the OS map data it requires for training.
#	
#
######################################################################################


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import pickle
import argparse
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier


DATA_PATH = 'data/processed/'		# path to the data from the project directory
OUTPUT_PATH = 'outputs/'
'''CONFIG dict storing global information. 
	random_int: integer setting the random seed for reproducibility.
'''
CONFIG = {
		'random_int': 123
		}

# setting random seed for reporducibility. SK learn uses numpy random seed.
np.random.seed(CONFIG['random_int'])


def loading_proxies():
	'''Function to load and combine the seperate proxy files into
		one dataframe. 

		RETURNS:
			tiles_df (pd.dataframe): df containing the data for all the homes in the target area (west midlands)'''

	tiles_df = pd.read_csv(DATA_PATH+'merged_and_encoded_proxies.csv')
	return tiles_df


def loading_epc():
	'''Function for loading the EPC data.

		RETURNS:
			epc_df (pd.dataframe): df containing the epc data'''

	epc_df = pd.read_csv(DATA_PATH+'cleaned_epc_data.csv')

	return epc_df


def merging_epc_and_proxies(epc_df, tiles_df):
	'''Merging the EPC data with all of the data from the target area (west midlands).
		The data is then seperated into two dataframes. One for the homes that are in 
		the epc database and one for those without. This is done because there is a
		difference between the variables in the EPC database, and those available for 
		all of the homes in the West Midlands. Combining and then seperating them in 
		this way allows for the matching of the epc ratings with the varaibles that
		are not available in the epc database.

		INPUTS: 
			epc_df (pd.Dataframe): df of the epc data
			tiles_df (pd.dataframe): df of the proxy data from all the homes in the WM

		RETURNS:
			proxies (pd.dataframe): df of all the homes without an EPC rating
			epc (pd.dataframe): df of all of the homes with an epc rating'''

	combined = tiles_df.merge(epc_df, on='uprn', how='left', suffixes=(None, '_epc'))		# merging the two dfs on the Unique Property Reference Number (UPRN)

	proxies = combined[combined['current-energy-rating'].isnull()].reset_index(drop=True) 	# homes not in the EPC database will not have a EPC rating. Use this to seperate
	epc = combined[combined['current-energy-rating'].notna()].reset_index(drop=True)		# homes in the database will have a rating

	# creating a column that indicates whether the eventaul results will be predicted or are a ground truth.
	epc['predicted'] = 0
	proxies['predicted'] = 1

	return proxies, epc		



def main():
	'''Main function for preparing and seperating the epc and proxy data.

		RETURNS:
			proxies (pd.dataframe): df of all the homes without an EPC rating
			epc (pd.dataframe): df of all of the homes with an epc rating'''

	tiles_df = loading_proxies()

	epc_df = loading_epc()

	proxies, epc = merging_epc_and_proxies(epc_df, tiles_df)

	# saving the data frames 
	proxies.to_csv(DATA_PATH+'homes_with_proxies.csv', index=False)
	epc.to_csv(DATA_PATH+'homes_with_epc_ratings.csv', index=False)

	return proxies, epc




if __name__ == '__main__':

	proxies, epc = main()		# calling the main function

	print('It ran. Good job!')

