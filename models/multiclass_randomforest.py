######################################################################################
#
#	model/multiclass_randomforest.py
#	
#	File for running a random forest model. Gives the option for the target variable
#	to be either the EPC rating, in which cace the output will be multi-class, or
#	the electric/non-electric heating type, which will have a binary output. File 
#	saves the model and resulting predictions. Takes in the already seperated 
#	training and testing data. Run from the main project directory
#	
#
######################################################################################


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pickle
import argparse
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import gc


DATA_PATH = 'data/processed/'		# path to the data from the project directory
OUTPUT_PATH = 'outputs/'
MODEL_PATH = 'models/trained_models/'

'''CONFIG dict storing global information. 
	random_int: integer setting the reandom seed for reproducibility.
	input_features: list of features to be segmented from the larger training and testing datasets
					for input to the models.
'''
CONFIG = {
		'random_int': 123,
		'input_features':['postcode', 'calculatedAreaValue', 'RelHMax', 'LATITUDE', 'LONGITUDE', 'lsoa_code',
							'msoa_code', 'prop_households_fuel_poor', 'total_consumption', 'mean_counsumption', 
						  	'median_consumption', 'local-authority_E07000192',
							'local-authority_E08000025', 'local-authority_E08000027', 'local-authority_E08000028',
							'local-authority_E08000030', 'local-authority_E08000031', 'constituency']}


# setting random seed for reporducibility. SK learn uses numpy random seed.
np.random.seed(CONFIG['random_int'])

def loading_training_data(target, train_df=None):

	''' Function for loading the pre-seperated training data. The target var is then 
		seperated and everything not in the input_features list is dropped.

		INPUTS: 
		target (str): the target varaible. Either 'mainheat-description for elec/non-elec prediction, or 
						'current-energy-rating' for the epc rating.

		RETURNS:
		X_train (pd.DataFrame): dataframe ready to be put into the model for fitting.
		y_train (pd.Series): series containing the target variable for fitting the model.
		train_df (pd.DataFrame): original dataframe that will be used for producing final output.
	'''
	if train_df.empty:
		train_df = pd.read_csv(DATA_PATH+'homes_with_epc_ratings.csv')	# loading the training dataframe from saved file
	
	y_train = train_df[target]									# extracting the target varaible

	X_train = train_df[CONFIG['input_features']]				# dropping everything not in the 'input_features'

	return X_train, y_train, train_df


def loading_testing_data(test_df=None, file_path=None):

	''' Function for loading the pre-seperated testing data. Everything not in 
		the input_features list is dropped.

		INPUTS:
			file_path (str): path to the testing data. Default given if None

		RETURNS:
		X_test (pd.DataFrame): dataframe ready to be put into the model for making the predictions.
		test_df (pd.DataFrame): original dataframe that will be used for producing final output.
	'''
	if test_df.empty:
		if file_path:
			test_df = pd.read_csv(file_path)	# loading the testing dataframe

		if file_path==None:
			test_df = pd.read_csv(DATA_PATH+'homes_with_proxies.csv')	# loading the testing dataframe


	X_test = test_df[CONFIG['input_features']]					# dropping everything not in the 'input_features'

	return X_test, test_df


def define_model(n_estimators=1000, criterion='entropy'):
	''' 
		Creating the model for training and predicting. See Scikit-Learn documentation
		for more details on the input parameters to the model.

		INPUTS: 
		n_estimators (int): num of trees that will be used in the forest.
		criterion (str): The function to measure the quality of a split.

		RETURNS:
		model: defined model for fitting
	'''

	model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion)
	
	return model


def fitting_and_predicting(X_train, X_test, y_train, predicting, to_fit, file_name):
	''' 
		Function that does the fitting of the defined model on the 
		training data, saves the fit model, and then makes a prediction 
		on the testing data.

		INPUTS: 
		X_train (pd.DataFrame): prepared training input data
		X_test (pd.DataFrame): prepared testing input data
		y_train (pd.Series): prepared target data for fitting
		predicting (str): either 'epc' or 'mainheat', used for file path for
							saving the fit model.
		to_fit (bool)
		file_name (str): name of the file for saving the model.

		RETURNS:
		y_pred (np.array): array of predicted values from the model.
	'''
	if to_fit:
		model = define_model()		# getting the model
		print('Fitting the classifier....')
		model.fit(X_train, y_train)		# fitting the model
		del X_train, y_train
		gc.collect()
		
		# saving the model
		print('Saving the model....')
		with open(MODEL_PATH+'{0}/{1}.h5'.format(predicting, file_name), 'wb') as m:
			pickle.dump(multiclass_model, m)
		

	if to_fit==False:
		with open(MODEL_PATH+'{0}/{1}.h5'.format(predicting, file_name), 'rb') as f:
			model = pickle.load(f)
	print('Predicting....')
	y_pred = model.predict_proba(X_test)		# predicting the output values
	
	del X_test
	gc.collect()


	return pd.DataFrame(y_pred), model



def fitting_and_predicting_regression(X_train, X_test, y_train, predicting, to_fit, file_name, n_estimators=1000, criterion='squared_error'):
	''' 
		Function that does the fitting of the defined model on the 
		training data, saves the fit model, and then makes a prediction 
		on the testing data.

		INPUTS: 
		X_train (pd.DataFrame): prepared training input data
		X_test (pd.DataFrame): prepared testing input data
		y_train (pd.Series): prepared target data for fitting
		predicting (str): either 'epc' or 'mainheat', used for file path for
							saving the fit model.
		to_fit (bool)
		file_name (str): name of the file for saving the model.

		RETURNS:
		y_pred (np.array): array of predicted values from the model.
	'''
	
	if to_fit:
		model = RandomForestRegressor(n_estimators=n_estimators, criterion=criterion)
		print('fitting regressor....')
		model.fit(X_train, y_train)		# fitting the model

		# saving the model
		with open(MODEL_PATH+'{0}/{1}.h5'.format(predicting, file_name), 'wb') as r:
			pickle.dump(regression_model, r)
		
		

	if to_fit==False:
		with open(MODEL_PATH+'{0}/{1}.h5'.format(predicting, file_name), 'rb') as f:
			model = pickle.load(f)
	
	print('predicting regressor....')
	y_pred = model.predict(X_test)		# predicting the output values
	del X_test
	gc.collect()


	return pd.DataFrame(y_pred), model



def definitive_prediction_and_confidence(results):
	''' 
		Takes the positive node outputs from each of the models and combines them to
		make one defeinitive prediciton. Also calculates a confidence rating for each prediction.

		INPUTS: 
		results (pd.DataFrame): dataframe contianing the positive nodes for each models output.

		RETURNS:
		outputs (pd.DataFrame): df containing the final predicitons and confidence intervals.
	'''

	results.columns=['A','B','C','D','E','F','G']	# changing the name of the columns to correspond to the ratings
	results = results.div(results.sum(axis=1), axis=0)	# normalizing the rows using the sum of the rows
	results = results.to_numpy()		# turning the dataframe to a np.array for calculations

	outputs = pd.DataFrame()			# defnining a df for later use.

	to_map = {0:'A', 1:'B', 2:'C', 3:'D', 4:'E', 5:'F', 6:'G'}	# mapping dict for tranitioning the column position to EPC rating

	predicted = np.argmax(results, axis=1)							# getting the highest prediction in each row
	confidence = results[np.arange(results.shape[0]), predicted]	# Getting the percentile value from the highest predicted column

	# This block is looking at the confidence that the results are within one band either way for the epc ratings
	down_one = predicted - 1 								# changing the column position so it's one down from the result
	down_o = np.where(down_one < 0, 0, 1) 					# changing the -1 values to 0 and everything else to 1. Will use this to eliminate the out of bounds estimates
	down_one = np.where(down_one < 0, 0, down_one) 			# changing everything that's below 0 to 0. Used for indexing. Can't have nan values

	up_one = predicted + 1 									# changing the column position so it's one up from the result
	up_o = np.where(up_one > 6, 0, 1)						# changing the 7 values to 0 and everything else to 1. Will use this to eliminate the out of bounds estimates
	up_one = np.where(up_one > 6, 6, up_one)				# changing everything that's above 6 to 6. Used for indexing. Can't have nan values

	up = results[np.arange(results.shape[0]), up_one]		# extracting the values from the one up column
	up = up * up_o.T 										# multiplying by the identity column to eliminate the out of bounds values
	down = results[np.arange(results.shape[0]), down_one]	# extracting the values from the one down column
	down = down * down_o.T 									# multiplying by the identity column to eliminate the out of bounds values

	within_one = up + confidence + down 					# summing up the individual confidences for the value and the one band away

	outputs['RF_current-energy-rating'] = pd.Series(predicted).map(to_map) 	# mapping the column indicies to EPC ratings and saving the resulting array as a df column
	outputs['RF_confidence'] = confidence 										# saving the confidence
	outputs['confidence_within_one_rating'] = within_one 					# saving the within_one_confidence


	return outputs


def attaching_training_data_to_epc(train_df, test_df, outputs, y_pred_eff):
	''' 
		Attaches the results to the original dataframes so everything is together
		for the final output. Also attaches a new column indicating whether or not 
		the results for that row are ground truth (0), or predicted values (1).

		INPUTS: 
		train_df (pd.DataFrame): original training dataframe
		test_df (pd.DataFrame): original testing dataframe
		outputs (pd.DataFrame): model predictions. 

		RETURNS:
		df (pd.DataFrame): final combined dataframe
	'''

	test_df = pd.concat([test_df, outputs], ignore_index=False, axis=1)		# attaching the outputs to the testing dataframe
	test_df['current-energy-efficiency'] = y_pred_eff

	return test_df


def attaching_training_data_to_mainheat(train_df, test_df, y_pred):

	''' 
		Attaches the results to the original dataframes so everything is together
		for the final output. Also attaches a new column indicating whether or not 
		the results for that row are ground truth (0), or predicted values (1).

		INPUTS: 
		train_df (pd.DataFrame): original training dataframe
		test_df (pd.DataFrame): original testing dataframe
		target (str): the target varaible. Either 'mainheat-description for elec/non-elec prediction, or 
						'current-energy-rating' for the epc rating. Used for naming the column of saved
						results in the final dataframe.
		y_pred (np.array): model predictions. 

		RETURNS:
		df (pd.DataFrame): final combined dataframe
	'''
	test_df['mainheat-description'] = np.argmax(y_pred.to_numpy(), axis=1)		# assigning the model positive node to the test_df 

	train_df['predicted'] = 0 		# creating new column indicating whether the target column is gorund truth 
	test_df['predicted'] = 1 		# or prediced/synthetic data

	df = pd.concat([train_df, test_df], axis=0)		# putting the dataframes together to create one final dataframe

	return df


def main(train_df, test_df, target, predicting, saved_file_name, to_fit=True, file_path=None):

	''' 
		Main funtion pulling in all functions to prodcue a final output csv file containing predictions.

		INPUTS: 
		train_df (pd.Dataframe): dataframe containing the homes with EPC ratings for model training
		test_df (pd.Dataframe): dataframe containing the homes without EPC ratings for prediction
		target (str): the target varaible. Either 'mainheat-description for elec/non-elec prediction, or 
						'current-energy-rating' for the epc rating.
		predicting (str): simplified version of target, either 'epc', or 'mainheat'. Used for 
							defining the file path.
		saved_file_name (str): name of the file that will be saved as a results of the predictions.
		to_fit (bool): if True model will be fit and saved. If False, pre-trained model will be loaded
		file_path (str): path to the testing data. Defaul provided if None

	'''
	if (train_df.empty) and (to_fit==False):
		X_test, test_df = loading_testing_data(test_df=test_df, file_path=file_path)			# loading the pre-seperated testing data
		X_train, y_train = pd.DataFrame(), pd.Series()

	else:
		X_train, y_train, train_df = loading_training_data(target=target, train_df=train_df)		# loading the pre-seperated training data
		____, y_train_eff, ___ = loading_training_data(target='current-energy-efficiency', train_df=train_df)		# loading the pre-seperated training data
		X_test, test_df = loading_testing_data(test_df=test_df, file_path=file_path)			# loading the pre-seperated testing data
	
	y_pred, multiclass_model = fitting_and_predicting(X_train, X_test, y_train, predicting=predicting, to_fit=to_fit, file_name='multiclass_randomforest')	 # model training and predicting


	print('Got past the first block....')
	del y_train, multiclass_model
	gc.collect()

	if predicting == 'epc':

		y_pred_eff, regression_model = fitting_and_predicting_regression(X_train, X_test, y_train_eff, predicting=predicting, to_fit=to_fit, file_name='regression_randomforest')
		
		del X_train, X_test
		gc.collect()

		y_pred = definitive_prediction_and_confidence(y_pred) 		# getting the confidence intervals for the prediction

		output_df = attaching_training_data_to_epc(train_df, test_df, y_pred, y_pred_eff) 	# putting all of the dataframes together
		
		del y_train_eff
		gc.collect()
		

	else:

		output_df = attaching_training_data_to_mainheat(train_df, test_df, y_pred)		# creating the final output file


	output_df.to_csv(OUTPUT_PATH+'{0}/{1}.csv'.format(predicting, saved_file_name), index=False)	# saving the file.	
	
	


	return output_df


if __name__ == '__main__':

	# using arg parsing for if you were to run this file outside the main.py file.

	parser = argparse.ArgumentParser()
	parser.add_argument('target',
						action='store',
						choices=['epc', 'heat'],
						type=str,
						help='choose which target param to examine. Type epc for current-energy-rating, and heat for mainheat-description')

	
	args=parser.parse_args()

	if args.target == 'epc':
		target = 'current-energy-rating'
		predicting = 'epc'
	elif args.target == 'heat':
		target = 'mainheat-description'
		predicting = 'mainheat'


	output_df = main(target, predicting)		# calling the main function

	print('It ran. Good job!')


