##############################################################################
#
#
#	network_capacity/aggregating_points_into_shape_files.py
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

DATA_PATH = 'data/shp_files/'
OUTPUT_PATH = 'outputs/'
PLOT_PATH = 'plots/'

CONFIG = {
		'rel_features': ['uprn', 'LATITUDE', 'LONGITUDE', 'current-energy-rating', 'mainheat-description', 'total-floor-area']
							}

properties = pd.read_csv('outputs/additional_load_values.csv')

properties['geometry'] = properties.apply(lambda row: Point(row['LONGITUDE'], row['LATITUDE']), axis=1)

properties = gp.GeoDataFrame(properties, crs=4326, geometry='geometry')		# Convert to a GeoDataFrame

properties = properties.to_crs(epsg=31467)
columns_to_keep = properties.columns.tolist()

print('Dist Poly....')
# Load the countries polygons
distribution_polys = gp.GeoDataFrame.from_file(DATA_PATH+'wmca_distribution-area.shp')
distribution_polys = distribution_polys.to_crs(epsg=31467)
distribution_polys['dist_polygon'] = distribution_polys['geometry'].copy()
dist_properties = gp.tools.sjoin(properties, distribution_polys, how='left', predicate='within')
dist_df = dist_properties.groupby(dist_properties['dist_polygon'].to_wkt()).agg(additional_load=('additional_peak_load', np.sum)).reset_index()
dist_df.columns = ['geometry', 'additional_peak_load']
dist_df['geometry'] = gp.GeoSeries.from_wkt(dist_df['geometry'])
dist_df = gp.GeoDataFrame(dist_df, crs=4326, geometry='geometry')

fig = plt.figure()
dist_df.plot(column = 'additional_peak_load', legend=True, aspect='equal')
plt.savefig(PLOT_PATH+'dist_agg_peak.png')
dist_df.to_csv(OUTPUT_PATH+'dist_peak_agg.csv', index=False)

print('Primary Poly....')
primary_polys = gp.GeoDataFrame.from_file(DATA_PATH+'wmca_primary-area.shp')
primary_polys = primary_polys.to_crs(epsg=31467)
primary_polys['primary_polygon'] = primary_polys['geometry'].copy()
primary_properties = gp.tools.sjoin(properties, primary_polys, how='left', predicate='within')
primary_df = primary_properties.groupby(primary_properties['primary_polygon'].to_wkt()).agg(additional_peak_load=('additional_peak_load', np.sum)).reset_index()
primary_df.columns = ['geometry', 'additional_peak_load']
primary_df['geometry'] = gp.GeoSeries.from_wkt(primary_df['geometry'])
primary_df = gp.GeoDataFrame(primary_df, crs=4326, geometry='geometry')

fig = plt.figure(figsize=(60,55))
primary_df.plot(column = 'additional_peak_load', legend=True, aspect='equal')
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
plt.savefig(PLOT_PATH+'primary_agg_peak.png')
primary_df.to_csv(OUTPUT_PATH+'primary_peak_agg.csv', index=False)

print('GSP Poly....')
GSP_polys = gp.GeoDataFrame.from_file(DATA_PATH+'wmca_GSP.shp')
GSP_polys = GSP_polys.to_crs(epsg=31467)
GSP_polys['GSP_polygon'] = GSP_polys['geometry'].copy()
GSP_properties = gp.tools.sjoin(properties, GSP_polys, how='left', predicate='within')
GSP_df = GSP_properties.groupby(GSP_properties['GSP_polygon'].to_wkt()).agg(additional_load=('additional_load', np.sum)).reset_index()
GSP_df.columns = ['geometry', 'additional_load']
GSP_df['geometry'] = gp.GeoSeries.from_wkt(GSP_df['geometry'])
GSP_df = gp.GeoDataFrame(GSP_df, crs=4326, geometry='geometry')

fig = plt.figure()
GSP_df.plot(column = 'additional_load', legend=True, aspect='equal')
plt.savefig(PLOT_PATH+'GSP_agg_plt.png')
GSP_df.to_csv(OUTPUT_PATH+'GSP_peak_agg.csv', index=False)


print('BSP Poly....')
BSP_polys = gp.GeoDataFrame.from_file(DATA_PATH+'wmca_BSP.shp')
BSP_polys = BSP_polys.to_crs(epsg=31467)
BSP_polys['BSP_polygon'] = BSP_polys['geometry'].copy()
BSP_properties = gp.tools.sjoin(properties, BSP_polys, how='left', predicate='within')
BSP_df = BSP_properties.groupby(BSP_properties['BSP_polygon'].to_wkt()).agg(additional_load=('additional_load', np.sum)).reset_index()
BSP_df.columns = ['geometry', 'additional_load']
BSP_df['geometry'] = gp.GeoSeries.from_wkt(BSP_df['geometry'])
BSP_df = gp.GeoDataFrame(BSP_df, crs=4326, geometry='geometry')

fig = plt.figure()
BSP_df.plot(column = 'additional_load', legend=True, aspect='equal')
plt.savefig(PLOT_PATH+'BSP_agg_plt.png')
BSP_df.to_csv(OUTPUT_PATH+'BSP_peak_agg.csv', index=False)


print('WMCA Poly....')
WMCA_polys = gp.GeoDataFrame.from_file(DATA_PATH+'wmca.shp')
print('To CRS....')
WMCA_polys = WMCA_polys.to_crs(epsg=31467)
print('Copying geometry column....')
WMCA_polys['WMCA_polygon'] = WMCA_polys['geometry'].copy()
print('Joining....')
WMCA_properties = gp.tools.sjoin(properties, WMCA_polys, how='left', predicate='within')
print('Grouping by....')
# WMCA_df = WMCA_properties.groupby(WMCA_properties['WMCA_polygon'].to_wkt()).agg(additional_load=('additional_load', np.sum)).reset_index()
load = []
for poly in WMCA_properties['WMCA_polygon'].unique():
	temp = WMCA_properties[WMCA_properties['WMCA_polygon']==poly]
	load.append(temp['additional_load'].sum())
WMCA_df = pd.DataFrame({'geometry': WMCA_properties['WMCA_polygon'].unique(), 'additional_load':load})
print('Turning to GeoSeries....')
# WMCA_df['geometry'] = gp.GeoSeries.from_wkt(WMCA_df['geometry'])
print('To GeoDataframe....')
WMCA_df = gp.GeoDataFrame(WMCA_df, crs=4326, geometry='geometry')

print('Plotting....')

fig = plt.figure()
WMCA_df.plot(column = 'additional_load', legend=True, aspect='equal')
plt.savefig(PLOT_PATH+'WMCA_agg_plt.png')
WMCA_df.to_csv(OUTPUT_PATH+'WMCA_peak_agg.csv', index=False)



properties.to_csv(OUTPUT_PATH+'properties_with_polygons.csv', index=False)

print('Done!')

