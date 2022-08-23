##############################################################################
#
#
#	network_capacity/comparing_station_headroom.py
#
#	Taking the data from each individual property and putting assigning
# 	them a distribution level, primary, bulk supply, and grid supply point 
# 	polygon for further analysis. Uses GeoPandas.
#
#
##############################################################################


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import pickle
from tqdm import tqdm
import geopandas as gp
import geopandas.tools
from shapely.geometry import Point
from shapely import wkt

import inspect
import gc

DATA_PATH = 'data/processed/'
PLOT_PATH = 'plots/'

CONFIG = {
		'rel_features': ['uprn', 'LATITUDE', 'LONGITUDE', 'current-energy-rating', 'mainheat-description', 'total-floor-area'],
		'station_cols_to_keep': ['Network Reference ID', 'Parent Network Reference ID', 'Substation Name', 'Asset Type', 'Latitude', 'Longitude', 
									'Demand Headroom (MVA)', 'Upstream Demand Headroom', 'geometry']
							}

properties = pd.read_csv('outputs/additional_load_values.csv')
stations = pd.read_csv('data/WPD-Network-Capacity-Map-27-07-2022.csv')

properties['geometry'] = properties.apply(lambda row: Point(row['LONGITUDE'], row['LATITUDE']), axis=1)
stations['geometry'] = stations.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)

properties = gp.GeoDataFrame(properties, crs=4326, geometry='geometry')		# Convert to a GeoDataFrame
stations = gp.GeoDataFrame(stations, crs=4326, geometry='geometry')		# Convert to a GeoDataFrame

# properties.crs = {"init": "epsg:4326"}
properties = properties.to_crs(epsg=31467)
stations = stations.to_crs(epsg=31467)

columns_to_keep = properties.columns.tolist()
stations = stations[CONFIG['station_cols_to_keep']]
# stations.set_index('Network Reference ID', inplace=True)

df3 = gp.GeoDataFrame()
df2 = gp.GeoDataFrame.from_file('data/wmca_WPD/wmca_primary.shx')

df3['Network Reference ID'] = df2['Network_Re']
df3['Parent Network Reference ID'] = df2['Parent_Net']
df3['Substation Name'] = df2['Substation']
df3['Asset Type'] = df2['Asset_Type']
df3['Latitude'] = df2['Latitude']
df3['Longitude'] = df2['Longitude']
df3['Demand Headroom (MVA)'] = df2['Demand_Hea']
df3['Upstream Demand Headroom'] = np.nan
df3['geometry'] = df3.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
df3 = gp.GeoDataFrame(df3, crs=4326, geometry='geometry')		# Convert to a GeoDataFrame
df3 = df3.to_crs(epsg=31467)
df_IDS = df3['Network Reference ID'].unique().tolist()
station_IDS = stations['Network Reference ID'].unique().tolist()

df3 = df3[df3['Network Reference ID']==315304]
df3.reset_index(inplace=True, drop=True)

stations = pd.concat([stations, df3], axis=0)
stations = stations[stations['Asset Type']=='Primary']
stations.reset_index(drop=True, inplace=True)

primary_polys = gp.GeoDataFrame.from_file('data/wmca_WPD/wmca_primary-area.shp')

primary_polys = primary_polys.to_crs(epsg=31467)
primary_polys['primary_polygon'] = primary_polys['geometry'].copy()
primary_properties = gp.tools.sjoin(properties, primary_polys, how='left', predicate='within')
primary_df = primary_properties.groupby(primary_properties['primary_polygon'].to_wkt()).agg(additional_peak_load=('additional_peak_load', np.sum)).reset_index()
primary_df.columns = ['geometry', 'additional_peak_load']
primary_df['geometry'] = gp.GeoSeries.from_wkt(primary_df['geometry'])
primary_df = gp.GeoDataFrame(primary_df, crs=31467, geometry='geometry')
primary_df['station_number'] = [i for i in range(len(primary_df))]

primary_df['primary_polygon_geometry'] = primary_df['geometry'].copy()

primary_stations = gp.tools.sjoin(stations, primary_df, how='right', predicate='within')

primary_stations = primary_stations.dropna(subset=['primary_polygon_geometry']).reset_index(drop=True)
primary_stations['additional_peak_load (MWh)'] = primary_stations['additional_peak_load']/1000 			# converting from kWh to MWh
primary_stations['load_difference'] = primary_stations['Demand Headroom (MVA)'] - primary_stations['additional_peak_load (MWh)']
primary_polygons = primary_stations.groupby(primary_stations['primary_polygon_geometry'].to_wkt()).agg(load_difference=('load_difference', np.sum)).reset_index()

primary_polygons.columns = ['primary_polygon_geometry', 'load_difference']
primary_polygons['geometry'] = gp.GeoSeries.from_wkt(primary_polygons['primary_polygon_geometry'])
primary_polygons = gp.GeoDataFrame(primary_polygons, crs=31467, geometry='geometry')
primary_polygons = primary_stations.copy()


fig = plt.figure(figsize=(60,55))
primary_polygons.plot(column = 'load_difference', legend=True, aspect = 'equal')
plt.savefig('plots/network_capacity/primary_load_test_ver2.png')

# print(primary_polygons.columns)


print(primary_stations[['Network Reference ID', 'additional_peak_load (MWh)', 'load_difference', 'Demand Headroom (MVA)']])

primary_stations.to_csv('outputs/network_capacity/primary_poly_peak_load.csv', index=False)

















