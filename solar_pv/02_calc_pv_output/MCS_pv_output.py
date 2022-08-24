import pandas as pd
import geopandas as gpd
from glob import glob
import os
import numpy as np

def get_kk_factor(db, irradiance_df):
    """
    Map kk factor from MCS irradiance dataset based on aspect and slope

    Input
    db(DataFrame): Roof segment information
    irradiance_df(DataFrame): 2x2 matrix of kk factor from aspect and slope

    Output
    kk_factor(list): List of mapped kk factor

    """
    kk_factor = []
    for idx, row in db.iterrows():
        aspect = abs(row['aspect_mean'] - np.pi) * 180 / np.pi
        if 0 <=aspect <= 176 and 0 <= row['slope_mean'] < 90:
            aspect = 5 * round(aspect/5) # round to nearest 5
            slope = round(row['slope_mean'])
            if 0<slope<=10:
                kk_factor.append(irradiance_df.max().max())
            else:
                kk_factor.append(int(irradiance_df[aspect][slope]))
        else:
            kk_factor.append(0)

    return kk_factor

def main():
    # Get irradiance data for mapping
    IRRADIANCE_PATH = "..\\..\\data\\external\\Irradiance-Datasets.xlsx"
    irradiance_df = pd.read_excel(IRRADIANCE_PATH, sheet_name="Zone 6 - Birmingham", header=0)
    irradiance_df.columns = irradiance_df.loc[0].convert_dtypes()
    irradiance_df = irradiance_df.drop(0, axis=0)
    irradiance_df = irradiance_df.set_index('Slope')
    irradiance_df.index = irradiance_df.index.astype(int)
    irradiance_df = irradiance_df.iloc[: , 1:]

    # Loop through roof segments in tiles
    FOLDER_DIR = '..\\01_calc_shadow\\output\\roof_segments_unfiltered\\'
    filesInFolder = glob(FOLDER_DIR + '*.geojson')
    print(filesInFolder)

    OUTPUT_DIR = '\\output\\'
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    df = pd.DataFrame()
    for path in filesInFolder:
        db = pd.DataFrame(gpd.read_file(path, driver="GeoJSON"))
        db = db.dropna() # roof segments without slope or aspect value

        # Calculate pv output of each roof segment based on MCS equation
        db['installed_capacity'] = db['AREA'] * 2.5
        db['kk_factor'] = get_kk_factor(db, irradiance_df)
        db['pv_output'] = db['shading_mean'] * db['kk_factor'] * db['installed_capacity']

        # Group all roof segments to building
        db = db.groupby('uprn').agg(
            {
                'slope_mean':np.average,
                'aspect_mean':np.average,
                'shading_mean':np.average, 
                'height_mean': np.average,
                'pv_output': 'sum', 
                'AREA':'sum',
                'parentUPRN': pd.Series.mode,
                'thoroughfare': pd.Series.mode,
                'postcode': pd.Series.mode,
                'buildingNumber': pd.Series.mode
            })

        df = pd.concat([df, db])
    
    df.to_csv(f"{OUTPUT_DIR}MCS_pv_output.csv")

if __name__ == "__main__":
    main()