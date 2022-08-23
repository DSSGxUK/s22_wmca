######################################################################################
#
#	model/combining_SQ_and_RandomForest_models.py
#	
#	File for taking the random forest and similarity quantification models and
# 	combining their outputs. The Similarity quantification models will first be run
# 	and the results segregated into homes with a simialr home in the EPC database,
# 	and homes without. The random forest model will be run on both sets. For the 
# 	homes without a similar home, the random forest model will be taken as the 
# 	final result with the accompaning confidence levels. For the homes with a 
# 	similarity, the random forest and SQ model results will be compared. If they
# 	are the same, the result will remain and the confidence level from the 
# 	random forest will be used. If they differ, the confidence level from the random
# 	forest will be examined. If the confidence level is above 0.5, the random forest 
# 	prediction will be used. If it is below 0.5 the SQ model will be used. The SQ 
# 	will be able to provide a discrete level of confidence (low, mid, high), instead
# 	of the continuious level offered by the random forest model. It will not be able
# 	to offer the 'confidence-within-one' rating.
#	
#
######################################################################################


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pickle
import argparse
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

OUTPUT_PATH = 'outputs/'

def loading_data_from_files():
	'''function for loading  the seperate dataframes after predictions have been made.

		RETURNS:
			no_sim (pd.dataframe): df of the homes without a similar home in the EPC df
			sim (pd.dataframe): df of homes that have a similarity quantification prediction
	'''

	no_sim = pd.read_csv(OUTPUT_PATH+'epc/all_predictions_homes_without_sim.csv')
	sim = pd.read_csv(OUTPUT_PATH+'epc/all_predictions_homes_with_sim.csv')

	return no_sim, sim 


def comparing_results(df):
	'''Using a series of conditions to decide which prediction to take for each home.

		INPUTS:
			df (pd.dataframe): df of homes that have an SQ and RF prediction

		RETURNS:
			df (pd.dataframe): df with single prediction and confidence levels'''


	# describing conditions that will be used for assigning the additional power load for each type of house
	conditions = [(df['predicted']==0), (df['SQ_current-energy-rating'].isnull()),
					(df['SQ_current-energy-rating'] == df['RF_current-energy-rating']), 
					(df['SQ_current-energy-rating'] != df['RF_current-energy-rating']) & (df['RF_confidence']>=0.5),
					(df['SQ_current-energy-rating'] != df['RF_current-energy-rating']) & (df['RF_confidence']<0.5),
					(df['SQ_current-energy-rating'] != df['RF_current-energy-rating']) & (df['RF_confidence']<0.5) & (df['SQ_current-energy-rating'].isnull())]

	# assigning a value for additional power to each above condition
	ratings = [df['current-energy-rating'], df['RF_current-energy-rating'], df['RF_current-energy-rating'], 
				df['RF_current-energy-rating'], df['SQ_current-energy-rating'], df['RF_current-energy-rating']]

	# assigning a value for confidence level to each above condition
	confidence = [1, df['RF_confidence'], df['RF_confidence'], df['RF_confidence'], df['SQ_confidence'], df['RF_confidence']]

	# assigning a value for confidence that the prediction is within one value of the true value to each above condition
	within_one_conf = [np.nan, df['confidence_within_one_rating'], df['confidence_within_one_rating'], 
						df['confidence_within_one_rating'], np.nan, df['confidence_within_one_rating']] 


	df['current-energy-rating'] = np.select(conditions, ratings) 	# assigning the final prediction based on the conditions	
	df['confidence'] = np.select(conditions, confidence) 		# assigning the final confidence based on the conditions
	df['confidence_within_one_rating'] = np.select(conditions, within_one_conf) 	# assigning the final within_one_confidence based on the conditions
	df['predicted'].fillna(1, inplace=True) 	# predicted values for the predicted column can get dropped in the merging and show up as nan

	return df


def main(df):
	'''Main function for combining the similarity quantification and random forest
		models.

		RETURNS:
			df (pd.dataframe): combined modeled results
	'''

	if df.empty:

		df = loading_data_from_files()

	df = comparing_results(df)

	df.reset_index(inplace=True, drop=True)

	df.to_csv(OUTPUT_PATH+'combined_epc_ratings.csv', index=False)

	return df











