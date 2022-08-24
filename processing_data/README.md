# Pull Data

## Getting EPC data
EPC ratings were introduced in stages from 2007 and cover residential and non-residential buildings. A buildings will have an EPC rating if it has been built, sold or rented after 2008.  Following our scope, we are only looking at the EPC ratings for residential buildings.

We will use the EPC data to (1) determine which property features are most predictive of energy efficiency and (2) build a labelled dataset with the known EPC ratings and heating types. For more details see [here]().

### Installations
- [requests](https://pypi.org/project/requests/) to pull from API.
- (optional) [geopandas](https://geopandas.org/en/stable/getting_started/install.html) Python library to read geospatial data.
- [scikit-learn](https://scikit-learn.org/stable/) Python library for CHAID and encoding.

### Setup
1. Register for an account at [Energy Performance of Buildings Data: England and Wales](https://epc.opendatacommunities.org/) to get your API.
2. Replace `AUTH_TOKEN` with your API key.
3. Replace local authority codes or postcodes to the region of interest if it is not the West Midlands.
4. Run `01_get_epc.py` from the folder.
5. Run `main.py` from `02_data_preprocessing` from the folder.

## Getting proxies
The following creates the data required to predict EPC ratings, estimate solar PV output and determine heat pump capacity. The final output from the process outlined in this document will be a series of .geojson files while another set of files will be encoded and saved as .csv for model training. For more details see [here]().

### Data
1. [OS MasterMap Topography Layer](https://www.ordnancesurvey.co.uk/business-government/products/mastermap-topography): building footprints (format: `5882272-{tilename}.gml`)
2. [OS MasterMap Building Height Attribute](https://www.ordnancesurvey.co.uk/business-government/products/mastermap-building): heights of each building (format: `{tilename}.csv`)
3. [AddressBase Premium](https://www.ordnancesurvey.co.uk/business-government/products/addressbase-premium): address data for each house (format: `{tilename}.gml`)
4. [ONS UPRN Directory](https://geoportal.statistics.gov.uk/datasets/ons-uprn-directory-august-2022/about) (August 2022 West Midlands)
5. [Sub-regional fuel poverty data 2022](https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2022)
6. [Lower and Middle Super Output Areas electricity consumption](https://www.gov.uk/government/statistics/lower-and-middle-super-output-areas-electricity-consumption)

### Installation
- [geopandas](https://geopandas.org/en/stable/getting_started/install.html) Python library to read geospatial data
- [openpyxl](https://openpyxl.readthedocs.io/en/stable/) Python library to read Excel worksheets

### Setup
1. Set `ROOT_DIR` in `getting_proxies.py` to the main folder with all the OS Master Map data.
2. The folder with the topology files don’t have an extension so add .gml to them, using
```python
for path in glob.glob(TOPOLOGY_DIR+’*’):
  os.rename(path, path + ".gml")
```
2. Replace `WMCA_code` if you are working with another region.
3. Run the Python script from within its folder.

## Folder structure
```bash
data
├── external                                            # Data downloaded from other sources
│   ├── building_height	        
│   ├── landbaseprem	            
│   ├── topology	                  
│   ├── ONSUD_AUG_2022_WM.csv    
│   ├── LSOA_domestic_elect_2010-20.xlsx
│   └── sub-regional-fuel-poverty-2022-tables.xlsx   
├── raw                                                 # Pulled EPC data
├── processed                                           # Processed EPC data
└── output                                              # Final outputs	
pull_data
├── 01_get_EPC.py	                  
├── 02_data_preprocessing
│   ├── 01_data_cleaning.py
│   ├── 02_cleaning_categorical_data.py
│   ├── 03_CHAID.py
│   └── 04_encoding_categorical.py	    
├── 03_get_proxies.py	
├── notebooks	
└── plots	                                              # Saved plots from notebooks
    
```

## References
The method used here was largely inspired by [Using machine learning to predict energy efficiency (February 2020) by Sonia Williams](https://datasciencecampus.ons.gov.uk/projects/using-machine-learning-to-predict-energy-efficiency/).
