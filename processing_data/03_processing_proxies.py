
import geopandas as gpd
import pandas as pd
import numpy as np
import glob
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
import os
import time
import geopandas.tools
from shapely.geometry import Point
from shapely import wkt
import rtree
import matplotlib.pyplot as plt
from typing import Optional, Dict
from collections import defaultdict


RAW_DATA_PATH = 'data/raw/'



def merge_os_files(building_path, addressbase_path, topology_path):
    """
    Merge all AddressBase Premium, OS Master Map Topology and OS Master Map Building Height Attribute

    Input
    addressbase_path(str): Path to AddressBase tile
    topology_path(str): Path to Topology tile
    building_path(str): Path to building height csv

    Output
    merged_gdf(GeoDataFrame): Merged dataframe with building polygons
    """
    print("Merging files...")

    start = time.time()
    
    add_df = gpd.read_file(addressbase_path, layer='BasicLandPropertyUnit', driver='GML')
    top_df = gpd.read_file(topology_path, layer='TopographicArea', driver='GML')
    build_df = pd.read_csv(
                building_path, 
                header=None, 
                names=['fid','OS_TOPO_TOID_VERSION','BHA_ProcessDate','TileRef', 'AbsHMin', 'AbsH2','AbsHMax','RelH2','RelHMax','BHA_Conf']
                )

    add_df = add_df[['uprn','postcode', 'geometry', 'buildingNumber', 'thoroughfare', 'parentUPRN']]
    top_df = top_df[['fid', 'geometry', 'calculatedAreaValue']]
    build_df = build_df[['fid','RelHMax', 'AbsHMin', 'AbsHMax']]
    
    add_df = add_df.set_crs('epsg:4258', allow_override=True)
    add_df = add_df.to_crs('epsg:27700')
    
    top_df = top_df.merge(build_df, on='fid')
    merged_df = gpd.sjoin(add_df, top_df, how="left")

    merged_df = merged_df[merged_df['index_right'].notna()]
    merged_df['geometry'] = merged_df['index_right'].apply(lambda col: top_df['geometry'][col])
    merged_df.drop(columns=['index_right'], inplace=True)

    end = time.time()
    print(f"Completed merging data in {end-start}s")
    
    return merged_df


# In[17]:


def loading_other(add_files):  
    """
    Load all fuel poverty and mapping data.

    Returns
    pcd_lsoa_msoa_df(DataFrame): Mapping data for postcodes in the West Midlands
    fuel_poverty_avg(float): average fuel poverty rating used to fill missing data 
    energy_consump_df(DataFrame): Energy consumption data for the West Midlands
    fuel_poverty_df(DataFrame): Fuel poverty data in the West Midlands

    """
    # Post code to LSOA to MSOA converting data
    # Retrieved from https://geoportal.statistics.gov.uk/datasets/ons-uprn-directory-august-2022/about
    
    PCD_LSOA_MSOA_PATH = RAW_DATA_PATH+"ONSUD_AUG_2022_WM.csv"
    pcd_lsoa_msoa_df = pd.read_csv(PCD_LSOA_MSOA_PATH, low_memory=False, encoding='latin-1')

    # Filter for local authorities in WMCA
    WMCA_code = ['E08000025', 'E08000031', 'E08000026', 'E08000027', 'E08000028', 'E08000029', 'E08000030', 
                    'E07000192', 'E07000218', 'E07000219', 'E07000236', 'E07000220', 'E06000051', 'E07000221', 
                    'E07000199', 'E06000020', 'E07000222']
    pcd_lsoa_msoa_df = pcd_lsoa_msoa_df[pcd_lsoa_msoa_df['LAD21CD'].isin(WMCA_code)]

    # Rename and select columns to keep
    keep_col = ['UPRN', 'PCDS', 'lsoa11cd', 'msoa11cd', 'LAD21CD', 'PCON19CD']
    col_names = ['uprn', 'postcode', 'lsoa_code', 'msoa_code', 'local-authority', 'constituency']
    pcd_lsoa_msoa_df = pcd_lsoa_msoa_df[keep_col]
    pcd_lsoa_msoa_df = pcd_lsoa_msoa_df.rename(columns=dict(zip(keep_col,col_names)))

    # Load fuel poverty data
    # Retrieved from https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2022 
    FUEL_POVERTY_PATH = RAW_DATA_PATH+"sub-regional-fuel-poverty-2022-tables.xlsx"
    fuel_poverty_df = pd.read_excel(FUEL_POVERTY_PATH, sheet_name="Table 3", header=2)
    fuel_poverty_df.drop(columns=["LSOA Name", "LA Code", "LA Name", "Region"], inplace=True)
    fuel_poverty_df.columns = ["lsoa_code", "num_households", "num_households_fuel_poverty", "prop_households_fuel_poor"]

    # Remove bottom text rows
    crop_idx = np.where(fuel_poverty_df.isna().sum(axis=1) == len(fuel_poverty_df.columns))[0][0]
    fuel_poverty_df = fuel_poverty_df[:crop_idx-1]

    fuel_poverty_avg = fuel_poverty_df.mean(axis=0) # impute with national average

    # Load energy consumption data
    ENERGY_CONSUMP_PATH = RAW_DATA_PATH+"LSOA_domestic_elec_2010-20.xlsx"
    energy_consump_df = pd.read_excel(ENERGY_CONSUMP_PATH, sheet_name="2020", header=4)
    energy_consump_df.columns = [
        'local-authority', 'la', 'msoa_code', 'msoa', 'lsoa_code', 'lsoa', 'num_meter', 
        'total_consumption', 'mean_counsumption', 'median_consumption'
        ]
    energy_consump_df = energy_consump_df[['local-authority','msoa_code','lsoa_code', 
                                           'total_consumption', 'mean_counsumption', 'median_consumption']]
    energy_consump_df = energy_consump_df[energy_consump_df['local-authority'].isin(WMCA_code)]
    
    return pcd_lsoa_msoa_df, fuel_poverty_avg, energy_consump_df, fuel_poverty_df



def map_add_info(gdf, energy_consump_df, pcd_lsoa_msoa_df, fuel_poverty_df, latlon, filename):
    """
    Add LSOA, MSOA and local authority code, and fuel poverty data.

    Input
    gdf(GeoDataFrame): Merged OS dataframe
    energy_consump_df: energy consumption dataframe
    pcd_lsoa_msoa_df: dataframe containing the geographic codes
    fuel_poverty_df: fuel poverty dataframe
    latlon: dataframe of latitude and longitude data
    filename(str): Name of saved output file

    Returns:
    gdf: GeoDataFrame containing merged data 
    """
    print("Adding info...")
    start = time.time()

    ROOT_DIR = 'data/processed/'
    OUTPUT_DIR = ROOT_DIR + 'output/'
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
#     gdf = pd.DataFrame(gdf)
    gdf.drop(columns=['fid'], inplace=True)
    gdf['postcode'] = gdf['postcode'].fillna(np.nan)
    latlon = latlon[['UPRN', 'LATITUDE', 'LONGITUDE']]
    latlon.UPRN = latlon.UPRN.astype('object')
    gdf = pd.merge(gdf, latlon, left_on="uprn", right_on="UPRN", how="left")
    gdf.drop(columns=["UPRN"], inplace=True)
    
    cols_to_grab = ['lsoa_code', 'msoa_code', 'local-authority', 'constituency']
    
    temp_df = pd.DataFrame()
    temp_df['postcode'] = pcd_lsoa_msoa_df['postcode']
    temp_df[cols_to_grab] = pcd_lsoa_msoa_df[cols_to_grab]
    temp_df = pcd_lsoa_msoa_df.groupby('postcode', as_index=False)[cols_to_grab].agg(pd.Series.mode)
        
    # Map LSOA, MSOA and LA to postcode
    for col in list(pcd_lsoa_msoa_df.columns)[1:]:
        mapping = dict(zip(pcd_lsoa_msoa_df['uprn'], pcd_lsoa_msoa_df[col]))
        if col in gdf.columns:
            gdf[col] = gdf[col].fillna(gdf['uprn'].map(mapping))
        else:
            gdf[col] = gdf['uprn'].map(mapping)
            gdf[col] = gdf[col].fillna(np.nan)
            gdf[col] = gdf[col].fillna(gdf['postcode'].map(dict(zip(temp_df['postcode'], temp_df[col]))))
    
        
    gdf = gdf[gdf['postcode'].isna()==False]

    # Merge with fuel poverty on LSOA code
    gdf = gdf.merge(fuel_poverty_df, on="lsoa_code", how="left")

    # Merge with energy consumption on LSOA code
    energy_consump_df = energy_consump_df[["lsoa_code",'total_consumption', 
                                           'mean_counsumption', 'median_consumption']]
    gdf = gdf.merge(energy_consump_df, on="lsoa_code", how="left")

    gdf = gdf.to_crs("epsg:4326")
    gdf.to_file(OUTPUT_DIR+'{0}.geojson'.format(filename), driver='GeoJSON')
    end = time.time()
    print(f"Completed adding info in {end-start}s")

    return gdf


# In[14]:


def encode_var(gdf, energy_consump_df, encode, fuel_poverty_avg, fuel_poverty_df, filename):
    """
    Encode non-numeric variables for model training and fill numeric na with mean. Exported as csv.

    Input
    gdf(GeoDataFrame): Merged dataframe
    energy_consump_df: energy consumption dataframe
    encode: dict containing the mapping key-value pairs
    fuel_povery_avg: national average fuel poverty used to fill missing values
    fuel_poverty_df: fuel poverty dataframe
    filename(str): Name of output file

    Returns:
    df: encoded dataframe

    """
    print("Encoding variables...")
    ROOT_DIR = 'data/processed/'
    OUTPUT_DIR = ROOT_DIR + 'encoded_proxy/'
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    df = pd.DataFrame(gdf.drop(columns=['geometry', 'buildingNumber', 'thoroughfare', 'parentUPRN']))

    fuel_poverty_col = ["num_households", "num_households_fuel_poverty", "prop_households_fuel_poor"]
    for col in fuel_poverty_col:
        df[col] = df[col].fillna(fuel_poverty_avg[col])

    energy_consump_col = ['total_consumption', 'mean_counsumption', 'median_consumption']
    hierarchy = ["msoa_code", "local-authority"]

    for col in energy_consump_col:
        for grouped_var in hierarchy:
            if df[col].isna().sum() > 0:
                grouped_df = energy_consump_df.groupby(grouped_var).mean()
                mapping = dict(zip(energy_consump_df[grouped_var], grouped_df[col]))
                idx = df[df[col].isna() == True].index
                df.loc[idx, col] = df.loc[idx, grouped_var].map(mapping)

        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(energy_consump_df[col].mean())

    one_hot_col = ['local-authority']
    label_encode_col = ['postcode', 'lsoa_code', 'msoa_code', 'constituency']

    for col in one_hot_col:
        one_hot_encoded = pd.get_dummies(df[col], prefix=col)
        df = pd.concat([df, one_hot_encoded], axis=1)
        df.drop(columns=[col], inplace=True)

    for col in label_encode_col:
        mapping = encode[col]
        df[col] = df[col].map(mapping)


    df.to_csv(OUTPUT_DIR+'{0}.csv'.format(filename), index=False)

    print("Completed encoding variables.")
    return df


def main():
    """
    Assign all homes in AddressBasePremium to its building footprint from OSMap Topography and building 
    height from OSMap Building Height Attribute. Building shapefiles saved in 'output' as .gml
    """
    address_dir = RAW_DATA_DIR +'landbaseprem/'
    building_height_dir = RAW_DATA_DIR+'building_height/'
    topology_dir = RAW_DATA_DIR+'topology/'
    latlon = RAW_DATA_DIR+'osopenuprn_202205.csv'
    latlon = pd.read_csv(latlon)
    
    building_height_files = glob.glob(building_height_dir+'*.csv')
    address_files = glob.glob(address_dir+"*.gml")
    topology_files = glob.glob(topology_dir+"*.gml")

    final_output_df = pd.DataFrame()
    pcd_lsoa_msoa_df, fuel_poverty_avg, energy_consump_df, fuel_poverty_df = loading_other(address_files)

    for build, address, top in zip(building_height_files, address_files, topology_files):
        merged_df = merge_os_files(build, address, top)
        filename = Path(address).stem
        df = map_add_info(merged_df, energy_consump_df, pcd_lsoa_msoa_df, fuel_poverty_df, latlon, filename)
        final_output_df = pd.concat([final_output_df, df], axis=0)
        
    print('Loading postcode encoding stuff....')
    map_df = final_output_df[['postcode', 'lsoa_code', 'msoa_code', 'constituency']]
    
    # Create dictionary for one hot encoding
    encode = {}
    for lvl in ['postcode', 'lsoa_code', 'msoa_code', 'constituency']:
        unq_var = map_df[lvl].unique()
        encode[lvl] = dict(zip(unq_var, np.arange(len(unq_var))))
    encode_var(final_output_df, energy_consump_df, encode, fuel_poverty_avg, fuel_poverty_df, 'merged_and_encoded_proxies')




if __name__ == '__main__':

    main()

    print('It ran. Good job.')





