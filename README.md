# DSSGx-UK 2022 West Midlands Combined Authority/Pure Leapfrog Project

Welcome to the repository for the Data Science for Social Good - UK 2022 WMCA/Pure Leapfrog project. This repository consists of four main sections covering the three main outcomes of the project and the data preprocessing. Detailed descriptions can be found in each of the sub directories. These will provide more detailed descriptsions of the folder contents and the required files for running the scripts in the folder. 

This main README file will take the user through setting up the virtual environment, and the process of running the scripts to replicate the project in it's entiretly. It will also contain breif descriptsions of each folder's objective for users who which to only replicate a particular part of the project. 

## Folder structure
```bash
s22_wmca
├── data
│   ├── raw                                             # Data downloaded from other sources
│   │   ├── building_height	                          
│   │   ├── landbaseprem	            
│   │   ├── topology	                  
│   │   ├── ONSUD_AUG_2022_WM.csv    
│   │   ├── LSOA_domestic_elect_2010-20.xlsx
│   │   └── sub-regional-fuel-poverty-2022-tables.xlsx   
│   ├── processed                                       # Processed EPC data
│   └── output                                          # Final outputs	
├── processing_data
│   ├── 01_merge_EPC_energy_consumption.py              # Pulling and merging external files   
│   ├── 02_data_preprocessing
│   │   ├── data_cleaning.py                            # Initial cleaning
│   │   ├── cleaning_categorical_data.py                # Making categories uniform
│   │   ├── CHAID.py                                    # Grouping categories
│   │   ├── encoding_categorical.py                     # Encoding categorical variables
│   │   ├── numerical_encoding.py                       # Encoding and imputing numerical variables
│   │   └── main.py	                                    # Calls all functions in proper sequence
│   ├── 03_get_proxies.py	
│   └── plots                                           # Saved plots from this sub-directory
├── models
│   ├── combining_data_and_seperating_epc.py            # Attaches proxies to EPC data
│   ├── similarity_quantification_model.py	            # Runs similarity quantification model
│   ├── multiclass_randomforest.py			            # Runs multiclass random forest and regression RF
│   ├── combining_SQ_and_RandomForest_models.py	        # Combines SQ and RF models based on a set of criteria
│   ├── combining_results_for_output.py		            # Combines all results and calculates additional load
│   └── trained_models								    # Folder for storing trained random forest models
│       ├── epc
│       └── mainheat
├── network_capacity
│   ├── aggregating_points_into_shape_files.py	        # Calculates total additional load for different station levels
│   ├── comparing_station_headroom.py			        # Compares total additional loads to substation demand headrooms
│   ├── data
│   │   ├── raw
│   │   └── shp_files                                   # Stores shp files
│   ├── plots
│   └── outputs
├── solar pv
│   ├── 00_compare_grid   
│   │   ├── compare_grid.ipynb	            
│   │   ├── DSM_grid.txt	                            # DSM tiles received from Defra
│   │   ├── osmapFileName.txt	                        # Ordinance Survey data for West Midlands
│   │   ├── os_mapping.pkl	                            # Dictionary to map building footprint files and DSM data
│   │   └── missing_tiles.txt                           # Areas in West Midlands not covered by DSM
│   ├── 01_calc_shadow              
│   │   ├── temp	                                    # Auto-created to store temp files
│   │   ├── output	                                    # Auto-created to store outputs
│   │   │   ├── roof_segments	    
│   │   │   ├── roof_segments_unfiltered
│   │   │   └── no_DSM
│   │   ├── shading_with_DSM.py	                        # Roof segmentation & shading
│   │   ├── shading_without_DSM.py	                    # Pseudo-DSM & shading
│   │   └── launch.bat	                                # Runs OSGeo Shell
│   ├── 02_calc_pv_output                               # PV output estimates
│   │   ├── output                                      # Stores csv outputs
│   │   ├── MCS_output.py	
│   │   └── pvlib_output.py
│   └── 03_test_pv_output					
│       └── pv_test_set.ipynb  
├── technical_docs                                      # All technical documentation for project
    
```

## Brief Folder Description

`processing_data`: Folder that pulls the publiclly available data from multiple sources (requires API key). Cleans, encodes and imputes the data. Prepares the proxy data (not public), and combines it with the publically available data for training/testing of the models. Should be run 						before any other scripts in other folders unless user has pre-prepared data. 

`solar_pv`: estimates the solar photovoltaic output for homes in the target area. Calculates the shadows that fall over a building's roof, combines that with the roof area, average sunlight exposure of the roof, and roof orientation and uses that to estimate the kWh per year that could be 					produced by a particular home. 

`models`: takes the data prepared in the `processing_data` folder, trains a similarity quantification and random forest model, and produces predictions of 	the EPC ratings and the heating type for all the homes not in the EPC database. Performs the additional load calculations for the 						`network_capacity` process. 

`network_capacity`: aggregates the additional load that would be put on the network if homes were to switch from non-electric heating sources to electric heat-pumps. Displays the additoonal load as a function of the network polygons. Also calculates the load difference for the substations with available data. This is the gap between what the network can take as additional load, and how much would be produced by the additional heat pumps. A negetive value for the load differnece indicates the network/substation is in need of upgrades before the heating electrification could be completed. 

## Replicating the Project

If your goal is replicating all parts of the project for your given area follow these instructions. 

## Creating the environment

To begin it is highly reccomended a virtual environment is used to run these scripts. We cannot guarantee the scripts will run as intended if not run in an environment. To create the environment you can either use the `requirements.txt` file or the `env.yml` files. To use the `requirements.txt` file use 

```bash
pip install virtualenv
``` 
in the command line to install the virtual environment package, then run:
```bash
virtualenv venv
``` 
to initilize the environment (here called venv). Then to activate the environment run:
```bash
source venv/bin/activate
``` 
The requirements.txt file can be installed in the environment by running:
```bash
pip install -r requirements.txt
``` 

Alternitivly, if the user has Anaconda installed on their maching, a Conda environment can be created using the `env.yml`. To do this, simply run:
```bash
conda env create -f env.yml
``` 
This will create an environment called 'project_env'. Activation of this environemnt is done by running:
```bash
conda activate project_env
``` 

## Running the processing_data files

Once the environment has been created and activated the scripts in the `processing_data` file can be run. Files in this section should be run from the main directory. The file `processing_data/01_merge_EPC_energy_consumption.py` should be run first. To run:
```bash
python3 processing_data/01_merge_EPC_energy_consumption.py
```
This file pulls and merges the publically avaliable data. This is designed for the West Midlands geographic area. If another area is desired, the `WMCA_councils.txt` file should be modified to reflect the area of interest. Pulling the EPC data requires an API key. These are available for free with registration [here](https://epc.opendatacommunities.org/#register). The API key can be saved in an external file (reccommended) or manually input into the file (not recommended for security reasons). `01_merge_EPC_energy_consumption.py` will ouput the pulled and merged EOC data and save it as `data/processed/pre_clean_merged_epc_data.csv`. This will be used when running the cleaning and encoding file. This file can take time to run which will scale with the number of local authorities that are being pulled.

After `processing_data/01_merge_EPC_energy_consumption.py` has completed, the next file to run will be `processing_data/02_data_cleaning_and_encoding/main.py` which sequentially runs all of the other files in this folder. To run:

```bash
python3 processing_data/02_data_cleaning_and_encoding/main.py
```
The README file in the folder expalins in more detail each of the files. In short, these files clean, encode, and impute the merged data so it is ready for training a machine learning model. This file will output `data/processed/cleaned_epc_data.csv` as the final file, though it will output files after each class is called to be used for comparison and checkpointing. 

Following the cleaning and encoding of the data, the final data processing file to run is `processing_data/03_processing_proxies.py` which takes the OS map data and combines it with the cleaned and encoded EPC data to include the proxy data for training and deploying the model. To run:
```bash
python3 processing_data/03_processing_proxies.py
```
This file will output several files. One processed file for each of the input geographic tiles in the target area to be saved as `data/output/*.geojson`, and a final combined csv file for input into the modeling folder, saved as `data/processed/encoded_proxies/merged_and_encoded_proxies.csv`.


## Training the Models and Making Predictions

Scripts in this section should be run from the main directory. After the data has been preprocessed it can be input to the modeling pipeline. Running the modeling pipeline as a whole can be done by running:

```bash
python3 models/06_main.py
```
The individual files can be run if desired. The main file will output a combined csv file which contains the predicted and real EPC data. This file will contain the ratings (A-G and 0-100), the predicted heating type (0 for non-electric or 1 for electric), a level of confidence for the predictions, a level of confidence for the EPC ratings being withing one rating of teh predicted value, and the calculated additional load the home will put on the electrical network if it converts from a non-electical heating source to an electrical one. This value will be used in the network_capactiy files. The models will be saved in the `models/models/` folder. The user could consider changing the hyperparameters used in the RandomForest model. Due to computational constraints, the model used in our project only had 200 n_estimators. Performance could be improved by increasing the n_estimators to 1000 or more if user has the capacity. 


## Network Capacity

Users should navigate to the network_capacity folder to run scripts in this section. That can be done by entering:

``` bash
cd network_capacity
```
In the terminal window.
There are three files in the network_capacity folder. See documentation in the folder for more detailed information on these files. The `additional_load_calc.py` file does not have to be run if model results came from the `models/06_main.py` file, as this performs the additional load calculation. However, if the user has a file containing just the EPC ratings, heating types, and floor footprint area for a property, the additional load calculation should be done on that file before advances to the other files in the network_capacity folder. The other two files can be run individually after the calculations has been done. The `aggregating_points_into_shape_files.py` file aggregates the additional peak loads into the shape files for the different electrical network levels. It outputs plots and csv files for the aggregated values. Plots will be output to the `network_capacity/plots/` folder, and csv files to the `network_capacity/outputs/` file. To run:

```bash
python3 aggregating_points_into_shape_files.py
```
after navigating to the network_capacity folder. 

The `comparing_station_headroom.py` file compares the aggregated values for the primary station level with the demand headroom for the electrical substations that have data avaliable. It outputs plots and csv files with the load difference. Plots will be output to the `network_capacity/plots/` folder, and csv files to the `network_capacity/outputs/` file. Negetive load difference indicates that the increased load from converting to heatpumps exceeded the current capacity of the station. To run:
```bash
python3 comparing_station_headroom.py
```



## Solar_PV

The solar pv process invloves using a mix of python scripts and jupyter notebooks. User should see the README in the solar_pv folder for instructions on running the solar_pv process. 


