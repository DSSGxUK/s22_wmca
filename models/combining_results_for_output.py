######################################################################################
#
#   model/combining_results_for_output.py
#   
#   File for cominging all of the results from the differnt mdoels. Uses the epc 
#   rating, floor footprint, and heatings source to calculate the additional load 
#   the property would put onto the electrical network if it were to switch to
#   electric heat pumps for heating. Many assumptions were made in this calculation
#   which will not be discussed in detail here. Please see documentation for further
#   information on the calculations.
#   
#
######################################################################################

import pandas as pd
import numpy as np


'''CONFIG dict storing global information. 
	random_int: integer setting the reandom seed for reproducibility.
	features_to_keep: features to keep for the final output. Don't have to correspond to 'input_features'.
'''

DATA_PATH = 'data/processed/'
OUTPUT_PATH = 'outputs/'

CONFIG = {
		'random_int': 123,
		'features_to_keep':['uprn', 'postcode', 'calculatedAreaValue', 'RelHMax', 'LATITUDE', 'LONGITUDE', 'lsoa_code',
							'msoa_code', 'prop_households_fuel_poor', 'total_consumption', 'mean_counsumption', 
						  	'median_consumption', 'constituency', 'current-energy-rating',
						   'current-energy-efficiency', 'SQ_current-energy-rating', 'SQ_confidence', 
						   'RF_current-energy-rating', 'RF_confidence', 'confidence', 'confidence_within_one_rating',
						   'mainheat-description', 'additional_load', 'additional_peak_load', 'predicted']}


def area_under_the_curve(df):
	''' Function for calculating the area under the curve using a 
		Reimann sum.

		INPUTS:
			df (pd.DataFrame): dataframe containing the energy demand for the 
				UK with half hour time resoultion. 
		
		RETURNS:
			SUM (float): the calculated area under the curve defined by the time and MW value
	'''

	x = [n for n in range(len(df))] 		# creating an integer x value. Dataframe index is datetime so this makes the calculation easier.
	y = df['ND'].tolist()					# putting all the energy datapoints into a list
	SUM = 0 								# initializing the SUM amount
	for i in range(1, len(x)):				# looping through each point to manually do the calculation
		delta_x = x[i] - x[i - 1]						# change in the x value. Should just be unit value 
		tri_area = (delta_x * abs((y[i] - y[i-1]))/2) 	# calculates the area of the triagle formed by the slope of the line
		rec_area =  delta_x * min([y[i], y[i-1]])		# calculates the area of therectange below the trinagualar area
		total_area = tri_area + rec_area				# calculates teh total area
		SUM = SUM + total_area							# adds the area of this trapezoid to the total sum
	
	return SUM


def calculating_peak_ratio():

	'''Calculating the peak ratio using the UK total energy demand. Will be used
		to multiple the total energy added to the network when a home switches to a 
		heat pump for its heat source from a non-electric heat source.

		RETURNS:
			ratio (float): ratio between the peak of the power used and the total power used in the year
	'''

	df_2017 = pd.read_csv('data/raw/demanddata_2017.csv') 	# pulling the national data from 2017 because it contains the highest peak in the past 5 years

	df_2017['ND'] = df_2017['ND']*2 				# data is at half hour resoultion, multiplying by 2 converts from MW to MWh
	SUM = area_under_the_curve(df_2017)				# calculating the area under the curve
	ratio = df_2017['ND'].max()/SUM					# getting the ratio between the max (peak) value and the total power

	return ratio


def estimating_power_load_by_EPC(EPC_df, areas, avg_heating_power=15000):

	'''	Function for grouping the heating cost and stratifying it by EPC rating, 'calculatedAreaValue', and mainheat-description.
		Creates a column for the heating energy usage for homes stratified on these above params.
		15,000 kWh is the assumed heating energy usage for UK homes by the uk gov 
		(https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/853753/QEP_Q3_2019.pdf)

		INPUT:
			EPC_df (pd.DataFrame): df of EPC homes which have the heating cost, known EPC ratings, known floor area and mainheat-descriptions.
			areas (list of str): list of names for the binned floor areas.

		RETURNS:
			costs (pd.dataframe): dataframe of energy usage stratified over 'current-energy-rating', 'calculatedAreaValue', 'mainheat-description'

	'''
	print('Estimating power load by EPC....')

	# defining the bins on the quantiles
	bins = [EPC_df['calculatedAreaValue'].min(), EPC_df['calculatedAreaValue'].quantile(0.25), EPC_df['calculatedAreaValue'].quantile(0.5), 
			EPC_df['calculatedAreaValue'].quantile(0.75), EPC_df['calculatedAreaValue'].max()]
	
	EPC_df['calculatedAreaValue'] = pd.cut(EPC_df['calculatedAreaValue'], bins=bins, labels=areas) 			# cutting the values in the area column into bins

	# Grouping the dataframe on the three factors
	costs = EPC_df.groupby(['current-energy-rating', 'calculatedAreaValue', 'mainheat-description']).mean()[['energy-consumption-current', 'heating-cost-current']]
	costs['cost-ratio'] = costs['heating-cost-current']/EPC_df['heating-cost-current'].mean()		# calculating the ratio between the heating cost in each startified column and the mean of all the heating costs
	costs['heating-energy-usage'] = round(costs['cost-ratio']*avg_heating_power,0) 					# multiplying the ratio by the average power used for heating in the UK


	return costs



def calculating_additional_load(df, EPC_df, COP=1):

	'''calculates the additional load put on the network by switching a property to 
		an electric heating source. For homes currently using an electric heating source, the 
		value will be 0. This assumes a Coefficient of Performance (COP) of 1 for the 
		added heat pump.  

		INPUTS:
			df (pd.dataframe): df containing data for all the homes in the area of interest
			EPC_df (pd.dataframe): df containing data from the EPC database for all homes in area of interest
			COP (int or float): coefficient of performance. Measure of heat pump efficiency

		RETURNS:
			df['additional_load'] (pd.series): containing the additional total yearly load for each property
			df['additional_peak_load'] (pd.series): containing the calculated additional peak load for each property
		'''

	print('Calculating peak ratio....')
	ratio = calculating_peak_ratio()		# getting the peak load ratio

	areas = ['<25_percentile', '25-50_percentile', '50-75_percentile', '>75_percentile']		# defining the names of the bins for grouping the floor area

	costs_df = estimating_power_load_by_EPC(EPC_df, areas)				# getting the stratified values for calculating the total additional load

	costs_df['heating-energy-usage'] = costs_df['heating-energy-usage']/COP 		# dividing the total power usage by the COP. More efficient heat pumps will use less energy

	# defining the bins on the quantiles
	bins = [df['calculatedAreaValue'].min(), df['calculatedAreaValue'].quantile(0.25), df['calculatedAreaValue'].quantile(0.5), 
			df['calculatedAreaValue'].quantile(0.75), df['calculatedAreaValue'].max()]

	df['calculatedAreaValue'] = pd.cut(df['calculatedAreaValue'], bins=bins, labels=areas) 		# cutting the values in the area column into bins

	print('Calculating additional load....')

	ratings = ['A', 'B', 'C', 'D', 'E', 'F', 'G'] 		# listing the different EPC ratings

	conditions, additional_loads = [], []

	for area in areas: 		# looping through the definied areas

		# describing conditions that will be used for assigning the additional power load for each type of house
		conditions = conditions + [(df['mainheat-description'] == 0) & (df['calculatedAreaValue'] == area) & (df['current-energy-rating'] == rating) for rating in ratings]

		# assigning a value for additional power to each above condition
		additional_loads = additional_loads+ [costs_df.loc[rating,area,1]['heating-energy-usage'] for rating in ratings]


	df['additional_load'] = np.select(conditions, additional_loads, default=0) 		# assigning the additional yearly load value based on the conditions, and assigns homes already with electric heating a value of 0.
	df['additional_peak_load'] = df['additional_load']*ratio 						# calculating the additional peak load using the ratio calculated earlier

	return df['additional_load'], df['additional_peak_load']



def main(full_dataset=None, epc_df=None):

	'''Main function pulling together all the functions.

		INPUTS:
			full_dataset (pd.DataFrame): dataset containing all of the predictions for the EPC ratings
						and heating types.
			epc_df (pd.DataFrame): initial EPC data. Used for calculations of the additional load
					on the network.

		RETURNS:
			full_dataset (pd.DataFrame): final dataframe with all of the predictions and calculations.
	'''

	if full_dataset.empty:
		full_dataset = pd.read_csv(OUTPUT_PATH+'combined_epc_ratings.csv') 			# loading the full dataset

	if epc_df.empty:
		epc_df = pd.read_csv(DATA_PATH+'cleaned_epc_data.csv') 			# loading the EPC dataset

	total_load, peak_load = calculating_additional_load(full_dataset, epc_df)

	# adding the values to the the full dataset
	full_dataset['additional_load'] = total_load 
	full_dataset['additional_peak_load'] = peak_load

	# full_dataset = full_dataset[CONFIG['features_to_keep']] 	# stripping the full dataset to the essential columns

	print('Final ratings')
	print(full_dataset['current-energy-rating'].unique())

	full_dataset = full_dataset[CONFIG['features_to_keep']] 					# keeping only the realevent features

	full_dataset.to_csv(OUTPUT_PATH+'full_dataset_outputs.csv', index=False)		# saving the dataset

	return full_dataset


if __name__ == '__main__':

	full_dataset = main(pd.DataFrame(), pd.DataFrame())      # calling the main function

	print('It ran. Good job!')

