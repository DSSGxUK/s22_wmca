######################################################################################
#
#   model/similarity_quantification_model.py
#   
#   File uses the similarity between the floor footprints of homes to map 
#   EPC ratings from known ratings to the unknown homes with the same floorprint.
#   This does not create a rating for all of the homes in the database, only those
#   that have the same footprint as anotehr already in the EPC database. The 
#   remaining homes are seperated 
#   
#
######################################################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from tqdm import tqdm
import inspect
import gc

DATA_PATH = '../data/processed/'		# data path
OUTPUT_PATH = 'outputs/'

'''CONFIG dict storing global information. 
	random_int: integer setting the reandom seed for reproducibility.
'''

CONFIG = {
		'random_int': 123}


def loading_epc_data():

	'''Function for loading the EPC data.

		RETURNS:
		epc_df (pd.DataFrame): dataframe contianing data from the 
				homes in the epc database.
	'''

	epc_df = pd.read_csv(DATA_PATH+'homes_with_epc_ratings.csv')

	return epc_df


def loading_all_homes_data():
	'''Function for loading the data from all homes in the West Midlands.

		RETURNS:
		epc_df (pd.DataFrame): dataframe contianing data from the 
				homes in the epc database.
	'''
	all_df = pd.read_csv(DATA_PATH+'homes_with_proxies.csv')

	return all_df


def similar_homes(all_df, epc_df, level='postcode', precision=2):

	'''Function comparing homes in the epc databsse to all homes. Homes with a floor footprint
		area withing a limit of precision to a home in the EPC database will be assumed to have 
		the same EPC rating. This will only apply to a subset of homes in the "All homes dataframe"
		so the remaining homes will be seperated so they can be put through a random forest model.

		INPUTS:
			all_df (pd.DataFrame): dataframe containing the home and proxy information for all homes in the 
					area of interest.
			epc_df (pd.DataFrame): dataframe that contains data from properties in the EPC database 
					in the area of interest.
			level (str): area in which comparisons of area will be made between homes. Searches will only
						be performed between homes in this area.
			precision (int): area calculation for comparing homes is rounded to this precision.

		RETURNS:
			results (pd.DataFrame): dataframe containing the homes that can obtain a rating through this method
	'''

																
	results = pd.DataFrame()						# initializing the data frame that will store the results
	for code in all_df[level].unique():			# looping through all unique values in the selected level. 
		EPC = epc_df[epc_df[level]==code]		# creating a subset EPC dataframe for the code being examined
		ALL = all_df[all_df[level]==code]			# creating a subset proxy dataframe for the code being examined
		if len(ALL)<5:
			continue

		EPC = EPC[['calculatedAreaValue', 'current-energy-rating', 'uprn']]		# segmenting out the required columns for the similarity matching
		EPC['area'] = round(EPC['calculatedAreaValue'], precision)			# calculating the area from the polygon and rounding to the degree of precision.  
		EPC['predicted'] = 0											# creating a new coulmn that indicates that this data is ground truth and not predicted
		EPC.reset_index(inplace=True, drop=True)    					

		temp_df = ALL.copy()											# creating a copy to preserve the larger dataframe inforamtion to attach after predictions 
		ALL = ALL[['uprn', 'calculatedAreaValue']]									# segmenting out required columns. Reducing columns improves the computational time for merging.
		ALL['area'] = round(ALL['calculatedAreaValue'],precision)				# calculating the area from the polygon and rounding to the degree of precision.  
		ALL.reset_index(inplace=True, drop=True)
		
		prediction = EPC.merge(ALL[['area', 'uprn']], on='area', how='right', suffixes=('_epc', None))	# merging the two dataframes on the area column. Preserves the homes in the ALL df that match an area in the EPC df
		prediction.dropna(inplace=True)									# removes all homes that do not have a match in the EPC
		pred, area, uprn, conf = [],[],[],[]							# initializing lists.
		for ID in prediction['uprn'].unique():							# looping through all the unique uprn values. One uprn could have multiple matches in the EPC df 
			frame = prediction[prediction['uprn']==ID]					# Creates a segmented dataframe for the unique uprn
			pred.append(frame['current-energy-rating'].mode()[0])		# taking the mode of the matching homes EPC rating
			area.append(frame['area'].mode()[0])						# Taking the mode of the area jsut for convienience 
			uprn.append(ID)												# grabbing the unique uprn for the property
			highest_mode = len(frame[frame['current-energy-rating']==frame['current-energy-rating'].mode()[0]]) 			# getting all the ratings that correspond to the highest rating
			perc = highest_mode/len(frame)		# getting the percentage of ratings that correspond to the most common rating
			
			''' This block assigns a confidence rating to the prediction based on the number of home with the same 
				area have the same rating, and how many homes have that area. Ratings drop one tier if there is
				only one home with the same area.
			'''

			if perc > 0.66:
				if highest_mode > 1:
					conf.append(0.8)
				else:
					conf.append(0.5)
			elif (perc>0.33) and (perc<=0.66):
				if highest_mode > 1:
					conf.append(0.5)
				else:
					conf.append(0.3)
			else:
				conf.append(0.3)

		dataframe = pd.DataFrame({'uprn':uprn, 'area':area, 'SQ_current-energy-rating':pred, 'SQ_confidence':conf})		# creating a dataframe for this code to store all of the matching homes
		dataframe = temp_df.merge(dataframe, on='uprn', how='left', suffixes=(None, '_pred'))		# mreging the predicted data with the other coulmns in the initial dataframe so we have all information associated with the uprn
		results = pd.concat([results,dataframe], axis=0)				# concatinating this with the larger results dataframe which stores the results for all areas
		results.reset_index(inplace=True, drop=True)					


	return results



def main(epc_df=None, all_df=None):
	'''Main function for preparing and seperating the epc and proxy data.

		RETURNS:
			results (pd.DataFrame): dataframe containing the homes that can obtain a rating through this method
	'''

	if epc_df.empty:
		epc_df = loading_epc_data()

	if all_df.empty:
		all_df = loading_all_homes_data()

	results = similar_homes(all_df, epc_df, level='postcode', precision=2)

	results.to_csv(OUTPUT_PATH+'SQ_results.csv', index=False)


	return results




if __name__ == '__main__':

	results = main(pd.DataFrame(), pd.DataFrame())		# calling the main function

	print('It ran. Good job!')
