##################################################################################################
#
# data_preprocessing/02_data_cleaning_and_encoding/06_main.py
#
# pulls together all the preprocessing steps and returns a final dataframe
#
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import KNNImputer, SimpleImputer, IterativeImputer
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split, cross_val_score
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from CHAID import Tree
from shapely.geometry import Point  #Polygon
import geopandas

import inspect
import gc

from data_cleaning import *
from cleaning_categorical_data import *
from chaid import *
from encoding_categorical import *
from EPC_numeric_data import *


DATA_PATH = 'data/raw/'
PLOT_PATH = 'plots/'
OUTPUT_PATH = 'data/processed/'

CONFIG= {'counties':['Birmingham','Wolverhampton','Coventry','Dudley','Sandwell',
						'Solihull','Walsall','Cannock Chase','North Warwickshire',
						'Nuneaton and Bedworth','Redditch','Rugby','Shropshire',
						'Stratford-on-Avon','Tamworth','Telford and Wrekin','Warwick',
						'Warrington'],
		'random_int': 123,
		'parameters_to_drop':['num_households_fuel_poverty',
								'environment-impact-current','co2-emissions-current'],
		'percent_missing_threshold': 90,
		'test_size': 0.3,
		'imputing_columns': ['floor-height', 'mainheat-energy-eff', 'windows-env-eff', 
								'lighting-energy-eff', 'heating-cost-current', 'hot-water-cost-current', 
								'number-heated-rooms', 'number-open-fireplaces', 'glazed-area', 
								'inspection-date', 'roof-energy-eff', 'total-floor-area', 'number-habitable-rooms', 
								'hot-water-env-eff', 'mainheatc-energy-eff', 'lighting-env-eff', 'windows-energy-eff', 
								'roof-env-eff', 'walls-energy-eff', 'photo-supply', 'mainheat-env-eff', 
								'multi-glaze-proportion', 'lodgement-datetime', 'walls-env-eff', 
								'energy-consumption-current', 'lighting-cost-current', 'extension-count', 
								'mainheatc-env-eff', 'wind-turbine-count', 'hot-water-energy-eff', 'low-energy-lighting',
								 'num_meter', 'total_consumption', 'mean_counsumption', 'median_consumption', 
								 'prop_households_fuel_poor', 'LATITUDE', 'LONGITUDE', 'percentage-low-energy-lighting']
		}

# setting random seed for reporducibility. SK learn uses numpy random seed.
np.random.seed(CONFIG['random_int'])

def main(config):

	print('Loading intiial merged CSV....')
	df = pd.read_csv('data/processed/data_1012650.csv')

	# # print(df)

	# initial data cleaning. 
	print('Cleaning data....')
	data_cleaning = DataCleaning(df, config['counties'], DATA_PATH, PLOT_PATH)
	clean_df = DataCleaning.process(data_cleaning)
	clean_df.to_csv(OUTPUT_PATH+'data_cleaning.csv', index=False)


	# specifically cleaning the categorical data
	print('Categorical Cleaning Data....')
	categorical_cleaning = CleaningCategoricalData(clean_df)
	categorical_df = CleaningCategoricalData.process(categorical_cleaning)
	categorical_df.to_csv(OUTPUT_PATH+'cleaning_categorical_data.csv', index=False)


	# doing chaid grouping of the categorical data columns
	print('CHAID cleaning....')
	chaid_cleaning = CHAIDGrouping(categorical_df, OUTPUT_PATH)
	chaid_df = CHAIDGrouping.process(chaid_cleaning)
	chaid_df.to_csv(OUTPUT_PATH+'chaid_data.csv', index=False)

	# numerically and one-hot encoding the categorical variables
	print('Encoding Data....')
	encoded_cleaning = EncodingCategorical(chaid_df, PLOT_PATH)
	encoded_df = EncodingCategorical.process(encoded_cleaning)
	encoded_df.to_csv(OUTPUT_PATH+'encoded_categorical.csv', index=False)

	# numerically cleaning and imputing 
	print('Numerical cleaning the data....')
	numeric_cleaning = CleaningNumericData(encoded_df, percent_missing_threshold=config['percent_missing_threshold'], 
													parameters_to_drop=config['parameters_to_drop'], imputing_columns=config['imputing_columns'],
													test_size=config['test_size'], random_int=config['random_int'])
	numeric_df = CleaningNumericData.process(numeric_cleaning)
	numeric_df.to_csv(OUTPUT_PATH+'cleaned_epc_data.csv', index=False)




if __name__ == '__main__':

	main(CONFIG)

	print('It ran. Good job!')




