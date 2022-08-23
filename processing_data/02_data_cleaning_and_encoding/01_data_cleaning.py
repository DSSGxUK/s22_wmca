import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point	#Polygon
import geopandas
import inspect
# from itertools import ifilter

class DataCleaning():
	def __init__(self, df, counties, DATA_PATH, PLOT_PATH):
		self.df = df
		self.pred = 'current-energy-rating'
		self.DATA_PATH = DATA_PATH
		self.PLOT_PATH = PLOT_PATH
		self.counties = counties # WMCA + Warrington houses only
	
	def filter_geography(self):
		""" Filter coordinates for those in region of interest """

		house_gdf = geopandas.GeoDataFrame(
			self.df[['uprn', 'LATITUDE', 'LONGITUDE']],
			geometry=geopandas.points_from_xy(self.df.LONGITUDE, self.df.LATITUDE),
			crs='epsg:4326')

		# filter shapefiles
		uk_shp = geopandas.read_file(self.DATA_PATH +'LAD_DEC_2021_GB_BFC.shp')
		westmidlands_shp = uk_shp[uk_shp.LAD21NM.isin(self.counties)] 
		# convert to lat/lng
		westmidlands_shp = westmidlands_shp.to_crs('epsg:4326') 
		# combine shapefiles 
		westmidlands_shp_boundary = westmidlands_shp.dissolve()

		# Filter for houses within boundary
		houseInWestMidlands = geopandas.tools.sjoin(house_gdf,westmidlands_shp_boundary, how='right')

		# # Check that all houses are within region of interest 
		# fig, ax = plt.subplots(figsize=(7,7))
		# westmidlands_shp_boundary.plot(
		# 	ax=ax, facecolor='Grey', edgecolor='k',alpha=1,linewidth=1,cmap="cividis"
		# 	)
		# # Reduce points to prevent crashing
		# plot_points = houseInWestMidlands.drop_duplicates(subset='geometry',inplace=True)
		# plot_points.plot(ax=ax, color='red', markersize=2, alpha=0.2)
		# ax.set_xlabel('Longitude', fontsize=10)
		# ax.set_ylabel('Latitude', fontsize='medium')
		# fig.savefig(self.PLOT_PATH+'houses_in_region_of_interest.png')

		# # Map of West Midlands
		# westmidlands_shp.plot(facecolor='Grey', edgecolor='k',alpha=1,linewidth=1,cmap="cividis")
		# fig.savefig(self.PLOT_PATH+'region_of_interest_boundary.png')

		# input("Check that the region of interest is correct and that all houses are within the region.")

		# Filter out houses outside the region of interest
		self.df = self.df[self.df.uprn.isin(houseInWestMidlands.uprn)]


	def clean_dependent_variable(self):
		""" Sanity check on dependent variable (EPC rating) """

		# Energy efficiency ratings should only go up to 100
		self.df = self.df[self.df['current-energy-efficiency'] <=100]
		print(f"Min: {self.df['current-energy-efficiency'].min()}")
		print(f"Max: {self.df['current-energy-efficiency'].max()}")

		print(self.df)
		print(self.df[self.pred].unique())

		plt.figure(figsize=(20,5))

		# Consider 0 ratings as band G
		self.df['current-energy-rating'][self.df['current-energy-efficiency']==0] = 'G'

		bands = ['G', 'F', 'E', 'D', 'C', 'B','A']

		for i, band in enumerate(bands):
			print(band)
			epc_bands = self.df[self.df[self.pred] == band]
			print(epc_bands)
			plt.subplot(241+i)
			bins = len(epc_bands['current-energy-efficiency'].unique())
			print(bins)
			epc_bands['current-energy-efficiency'].hist(bins=bins)
			plt.xlabel(band,fontsize=16, weight='bold')

		plt.tight_layout()
		plt.savefig(self.PLOT_PATH+'epc_rating_band_distribution.png')

		input('Check that the distributions look logical.')

	def drop_duplicates(self):

		"""

		For values which do not change often over time such as `built-form` (detached, terraced etc), it's safe to use the data from previous certificates where available to fill the missing values in more recent certificates. Keep the most recent certificate and drop the duplicates.

		"""
		# Impute missing values
		epc_grouped = self.df.groupby(['uprn'], as_index=False)['inspection-date'].count()
		epc_grouped_2plus = epc_grouped[epc_grouped['inspection-date'] > 1]
		epc_2plus = self.df.merge(epc_grouped_2plus[['uprn']], on = 'uprn', how = 'inner')

		# note this takes a while
		fill_columns = ['built-form', 'floor-level','number-habitable-rooms','floor-description',
				'roof-description','heat-loss-corridor','walls-description','floor-height',
				'mains-gas-flag']

		print('Columns being filled...')
		for c in fill_columns:
		 	print(c)
		 	epc_2plus[c] = epc_2plus.groupby(['uprn'], sort=False)[c].apply(lambda x: x.ffill())

		epc_grouped_1 = epc_grouped[epc_grouped['inspection-date'] == 1]
		epc_1 = self.df.merge(epc_grouped_1[['uprn']], on='uprn', how='inner')

		# merging filled data for buildings with more than one certificate with data for buildings with only one certificate
		epc_filled = pd.concat([epc_1,epc_2plus])

		# checking length of filled data (should be the same)
		print(f"Missing rows: {len(self.df) - len(epc_filled)}")
		print(f"Property without UPRN: {len(self.df[self.df.uprn.isna()])}")

		# remove rows without UPRN, doesn't exist and cannot find data
		self.df = self.df[self.df.uprn.isna()==False]

		# Keep the most recent UPRN record. Remove duplicates.
		df_sorted = self.df.sort_values('inspection-date')
		self.df = df_sorted.drop_duplicates('uprn', keep='last')
		print(f"Number of duplicates dropped: {len(df_sorted)-len(self.df)}")
		

	def standardise_missing_labels(self):
		"""Replace 'NO DATA!', 'not defined' and 'not recored' with null."""

		self.df = self.df.replace(['NO DATA!','NODATA!'],np.nan)
		self.df = self.df.replace(['not recorded','not defined','unknown','Unknown','Not defined','Not recorded'],np.nan)
		self.df = self.df.replace(['N/A','n/a'],np.nan)
		self.df = self.df.replace(['INVALID!'],np.nan)

	def missing_values_column(self):
		"""Drop columns which have too many missing or are irrelevant."""
		
		percent_missing = self.df.isnull().sum() * 100 / len(self.df)

		print(percent_missing.sort_values(ascending=False)[:30])

		self.df = self.df.drop([
				# Remove variables with too many missing variables
				'sheating-env-eff', 'sheating-energy-eff', 'flat-storey-count', 
				'floor-env-eff', 'floor-energy-eff', 'unheated-corridor-length', 
				'county', 'heat-loss-corridor', 'flat-top-storey', 
				# Remove unnecessary variables
				'msoa', 'lsoa', 'building-reference-number', 'local-authority-label', 
				'posttown', 'heating-cost-potential', 'hot-water-cost-potential',
				'energy-consumption-potential', 'potential-energy-efficiency',
				'co2-emissions-potential', 'lighting-cost-potential',
				'potential-energy-rating', 'environment-impact-potential',
				'constituency-label', 'lmk-key',
				# Remove derived variables
				'co2-emiss-curr-per-floor-area',
				# Remove variables with high % missing and similar variables
				'low-energy-fixed-light-count', 'fixed-lighting-outlets-count'
				],
				axis=1)

	def impute_photo_supply(self):
		"""Impute missing values for photo-supply from solar-water-heating-flag"""

		if 'photo-supply' in self.df.columns and 'solar-water-heating-flag' in self.df.columns:
			print(f"Original missing value: {self.df['photo-supply'].isna().sum()}")
			self.df['photo-supply-binary'] = np.where(self.df['photo-supply']>0.0, True, False)
			self.df['photo-supply-binary'].mask(self.df['photo-supply'].isna(),np.nan,inplace=True)
			self.df['solar-water-heating-flag'] = self.df['solar-water-heating-flag'].replace({'Y': True, 'N': False})
			self.df['photo-supply-binary'].fillna(self.df['solar-water-heating-flag'], inplace=True)
			print(f"After missing value: {self.df['photo-supply-binary'].isna().sum()}")

	def missing_values_row(self):
		"""Remove rows with too many missing values."""

		percent_missing_rows = self.df.isnull().sum(axis=1)/len(self.df.columns)

		plt.figure(figsize=(20,5))
		missing_plt = percent_missing_rows.hist()
		missing_plt.set_xlabel('Percent missing')
		missing_plt.set_ylabel('Number of rows')
		plt.savefig(self.PLOT_PATH+'missing_row_distribution.png')

		input("Check if there are any rows that should be removed.")

	def datetime_sanity_check(self):
		"""Sanity check values for datetime, should be in logical period."""

		# Convert to datetime object
		self.df['inspection-date'] = self.df['inspection-date'].astype('datetime64')
		self.df['lodgement-datetime'] = self.df['lodgement-datetime'].astype('datetime64')

		## remove similar column
		self.df.drop(columns=['lodgement-date'], inplace=True)

		# All valid years
		print(self.df['inspection-date'].dt.year.value_counts(normalize=True).sort_index())

		# All valid years
		print(self.df['lodgement-datetime'].dt.year.value_counts(normalize=True).sort_index())

		# Convert to datetime object
		self.df['inspection-date'] = self.df['inspection-date'].dt.year.astype('int')
		self.df['lodgement-datetime'] = self.df['lodgement-datetime'].dt.year.astype('int')

		input("Check that dates are in the logical range.")

	def clip_numeric(self):
		"""Clip values in numeric columns that are too high."""

		num_var = self.df.select_dtypes(include= 'number').columns.tolist()

		# Not these variables
		num_var.remove('uprn')
		num_var.remove('LATITUDE')
		num_var.remove('LONGITUDE')
		num_var.remove('current-energy-efficiency')

		# Subplots are organized in a Rows x Cols Grid
		tot_subplots = len(num_var)
		cols = 7

		# Compute Rows required
		rows = tot_subplots // cols 
		rows += tot_subplots % cols
		
		pos = range(1,tot_subplots + 1) # Create a Position index

		fig = plt.figure(figsize=(20,10))

		for k, var in enumerate(num_var):
		 	# add every single subplot to the figure with a for loop
		 	ax = fig.add_subplot(rows,cols,pos[k])
		 	ax.boxplot(self.df[var].dropna())	
		 	ax.set_xlabel(var,fontsize=8, weight='bold') 

		fig.tight_layout()
		plt.savefig(self.PLOT_PATH+'numerical_var_boxplot.png')

		# Clip these var
		clip_var = ['low-energy-lighting', 'total-floor-area', 'number-open-fireplaces',
			'number-heated-rooms', 'number-habitable-rooms', 'lighting-cost-current', 
			'energy-consumption-current', 'floor-height', 'num_meter']
		
		# clip only the lower bound of these vars
		lower_clip_var = ['heating-cost-current', 'hot-water-cost-current', 'lighting-cost-current',
							'wind-turbine-count']

		print(f"Variables to be clipped: {clip_var}")
		input("Check that these variables should be clipped at the upper 99% percentile.")

		# Clips the variables of the EPC data with the upper bound of the 99% 
		# confidence interval for variables with many outliers variance (no lower clip)
		audit_num = self.df[clip_var].describe(percentiles = [0.01,0.25,0.5,0.75,0.9,0.95,0.99])

		# clipping just the lower bound of certain columns
		for var in lower_clip_var:
		 	self.df[var].clip(lower=0.0, upper=self.df[var].max(),inplace=True)

		# Subplots are organized in a Rows x Cols Grid
		tot_subplots = len(clip_var)
		cols = 7

		# Compute Rows required
		rows = tot_subplots // cols 
		rows += tot_subplots % cols

		pos = range(1,tot_subplots + 1)	 # Create a Position index

		fig = plt.figure(figsize=(20,10))

		for k, var in enumerate(clip_var):
		 	ax = fig.add_subplot(rows,cols,pos[k])
		 	self.df[var].clip(lower=-9999.0, upper=audit_num[var]['99%'], inplace=True)
		 	ax.boxplot(self.df[var].dropna())
		 	ax.set_xlabel(var,fontsize=8, weight='bold')

		fig.tight_layout()
		plt.savefig(self.PLOT_PATH+'clipped_numerical_var_boxplot.png')

		input("Completed: Numerical variables clipped.")

	def process(self):

		self.filter_geography()
		self.clean_dependent_variable()
		self.drop_duplicates()
		self.standardise_missing_labels()
		self.missing_values_column()
		self.impute_photo_supply()
		self.missing_values_row()
		self.datetime_sanity_check()
		self.clip_numeric()

		return self.df

def main(df, counties, DATA_PATH, PLOT_PATH):
	cleaning = DataCleaning(df, counties, DATA_PATH, PLOT_PATH)
	attrs = (getattr(cleaning, name) for name in dir(cleaning))
	methods = ifilter(inspect.ismethod, attrs)
	for method in methods:
		method()

if __name__ == "__main__":
	main()








