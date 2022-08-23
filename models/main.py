##############################################################################
#
#
#	DSSG_WMCA/scripts/models/main.py
#
#	The full modeling pipeline. Starts by taking the fully processed EPC data
# 	and merging it with the proxy data to get the 'calculatedAreaValue' and
# 	'ResHMax' values, which are proxies for the total-floor-area and the 
# 	floor height. Then passes the data through the similarity quantification 
# 	model which will identify homes with the same floor area footprint as
# 	homes in the EPC database within the same target area (postcode, lsoa, etc.)
# 	and assigns the EPC rating to the similar home. The homes with similar
# 	homes with EPC ratings and those without are seperated. A Random Forest (RF) 
# 	model is run on both datasets. For the non-similar homes the RF results are 
# 	used as the EPC results for that home, for the similar homes set, the 
# 	RF and SQ results are compared and if they do not match, the confidence
# 	level of the RF is examined. If it exceeded 0.5 the RF value is used.
# 	If it does not, the SQ value is used. For all homes the RF model is used
# 	to predict the 'mainheat-description'. The results are then used to calculate
# 	the additional peak load on the electrical network if the homes without
# 	electric heating are converted to electric heating. A seperate file is
# 	used to aggregate those values and compare them to the currently network
# 	capacity.
# 	
#
#
##############################################################################


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import pickle
import requests
import argparse
from scipy.stats import pearsonr
from tqdm import tqdm
import scipy.stats as stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel

import inspect
import gc

import combining_data_and_seperating_epc as CASE
import similarity_quantification_model as SQM
import multiclass_randomforest as RFM
import combining_SQ_and_RandomForest_models as combining_models
import combining_results_for_output as combining_results


DATA_PATH = 'data/processed/'
PLOT_PATH = 'plots/'
OUTPUT_PATH = 'outputs/'

'''CONFIG dict storing global information. 
	random_int: integer setting the reandom seed for reproducibility.
'''

CONFIG = {
		'random_int': 123,
		'features_to_keep':['postcode', 'calculatedAreaValue', 'RelHMax', 'LATITUDE', 'LONGITUDE', 'lsoa_code',
							'msoa_code', 'prop_households_fuel_poor', 'total_consumption', 'mean_counsumption', 
						  	'median_consumption', 'local-authority_E07000192',
							'local-authority_E08000025', 'local-authority_E08000027', 'local-authority_E08000028',
							'local-authority_E08000030', 'local-authority_E08000031', 'constituency', 'current-energy-rating',
						   'current-energy-efficiency', 'SQ_current-energy-rating', 'SQ_confidence', 'RF_current-energy-rating',
						   'RF_confidence', 'confidence', 'confidence_within_one_rating', 'predicted', 'current-energy-rating_combo',
						   'mainheat-description', 'additional_load', 'additional_peak_load']}
							

# setting random seed for reporducibility. SK learn uses numpy random seed.
np.random.seed(CONFIG['random_int'])


def main():

	print('Combining and seperating the initial data....')
	proxies, epc = CASE.main()

	print('Similarity Quantification Model....')
	SQ_results = SQM.main(epc_df=epc, all_df=proxies)

	print('Training the EPC Random Forest Model....')
	RF_SQ_results = RFM.main(epc, SQ_results, target='current-energy-rating', predicting='epc', saved_file_name='epc_predictions_homes_with_sim', to_fit=True, file_path=None)

	# print('Predicting the EPC Random Forest Model and predicting on homes without similarities....')
	# no_sim = RFM.main(train_df=pd.DataFrame(), test_df=no_sim, target='current-energy-rating', predicting='epc', saved_file_name='epc_predictions_homes_without_sim', to_fit=False, file_path=None)

	print('Comparing and combining the SQ and RF models....')
	combined_df = combining_models.main(RF_SQ_results)

	print('Training the Mainheat Random Forest Model and predicting on homes with similarities....')
	combined_df = RFM.main(epc, combined_df, target='mainheat-description', predicting='mainheat', saved_file_name='mainheat_predictions_all_homes', to_fit=True, file_path=None)

	print('Combining the final results and calculating the additional loads....')
	full_dataset = combining_results.main(full_dataset=combined_df, epc_df=epc)

	print(full_dataset.isnull().sum())






if __name__ == '__main__':

	main()		# running the main script

	print('It ran. Good job!')





















