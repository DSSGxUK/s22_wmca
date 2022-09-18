# DSSGx-UK 2022 Identifying Residential Areas in the West Midlands that are Most Suitable for Retrofitting

Welcome to the repository for the Data Science for Social Good UK 2022 project with the **West Midlands Combined Authority** & **PureLeapfrog**.

The objective of this project was to identify residential homes and areas in the West Midlands that are situatable for retrofitting interventions (e.g. installing solar panels or heat pumps) to improve their energy efficiency.

The team developed three models, listed below with links to sub-directories with further details:

  1. Predicting Energy Performance Certificate (EPC) ratings of 60% of homes in the West Midlands - [procesing_data](https://github.com/DSSGxUK/s22_wmca/tree/main/processing_data) and [models](https://github.com/DSSGxUK/s22_wmca/tree/main/models)
  2. Identifying solar-panel ready areas - [link](https://github.com/DSSGxUK/s22_wmca/tree/main/solar_pv)
  3. Determining the implications of switching homes to electric heating on the electrical network - [link](https://github.com/DSSGxUK/s22_wmca/tree/main/network_capacity)

Using the outputs of the models, as well as the other data available, we deployed a Streamlit app for visualising and presenting the insights. A screenshot of the app is shown below and a demo can be found at this [link](https://asthanameghna-wmca-app-main-5xxw2q.streamlitapp.com/).

![alt text](https://github.com/DSSGxUK/s22_wmca/blob/main/images/streamlit_screenshot.jpg)

There is a separate repository which explains the process for building the dashboard, which can be accessed [here](https://github.com/DSSGxUK/s22_wmca_app).

This README takes the reader through an overview of the project and how to replicate it, including how to set up the virtual environment and the process of running the scripts. It also contains brief descriptions of each folder's objective for users who only wish to replicate a particular part of the project. Further details on how to run each model can be found in the READMEs within each of the sub directories. These provide more detailed descriptions of the folder contents and the required files for running the scripts.

Other key resources to consult include:
  - Technical documentation - [link](https://github.com/DSSGxUK/s22_wmca/tree/main/technical_docs)
  - Project poster - [link](https://github.com/DSSGxUK/s22_wmca/blob/main/images/DSSG%20Poster%20Presentation%20WMCA.pdf)

### Presentation Video

To Be Added

### Partners

[West Midlands Combined Authority](https://www.wmca.org.uk/) represents eighteen local authorities and three Local Enterprise Partnerships and seeks to make the West Midlands a better place to live through growth, regeneration, and better infrastructure. WMCA are aiming for a 36% reduction in carbon emissions across local transport, homes, and businesses by 2026 and hope to achieve 100% carbon neutrality by 2041.

[PureLeapfrog](https://www.pureleapfrog.org/) is a charity that aims to enable positive social, environmental, and financial impact for communities, in particular those in deprivation by enabling their participation in and benefit from, an energy system in transition to lower carbon intensity.

### Challenge

With limited resources and stretched budgets, to achieve their net-zero ambitions WMCA and PureLeapfrog recognised the need to think outside the box. They approached DSSG UK and proposed a data-driven approach to identify residential areas that would benefit the most from retrofitting interventions. By identifying these areas, the authority will be able to target resources (such as grants) and incentivize homeowners to upgrade their properties and become more energy efficient.

However, doing this identification posed several challenges, namely that:
  - Energy Performance Certificate (EPC) ratings and are only available for 40% of the 1.2 million homes in the West Midlands. 
  - It is unclear how to assess the expected improvement of certain interventions, and which are likely to benefit the most (e.g. which homes are likely to produce the most clean-energy output by installing solar panels)
  - It is not clear what the implications of switching homes to solar panels and electric heat pumps would be on the electrical network.
    
### Data

A range of different data sources were used for the different models, which are explained in detail in the READMEs within the sub-directories. Some of these datasets were publicly available such as the EPC data. Others were licensed such as Ordnance Survey Maps data. Most local authorities should have access to the datasets required already.

### Methods

Toi achieve the objective of identifying residential areas that are most suitable for retrofitting, three models were built. This section briefly explains each model and how it was developed. Further information is available in the technical documentation.

1.	Predicting EPC ratings of the remaining 60% of houses in the West Midlands.
    - Merged EPC, Ordnance Survey Master Maps, fuel poverty and electricity consumption data and trained several machine learning models.
    - Each model was trained to predict the EPC rating and heating type of houses using data available for all homes (i.e. floor area, height, address).
    - Selected the best model on F-1 and accuracy scores and by assessing performance on lower rated houses.
    - A similarity quantification (SQ) model was developed to make predictions based on how similar a house is to another house that already has an EPC rating. The SQ model was combined with the machine learning models to improve accuracy.

2.	Identifying solar panel-ready areas / estimating potential solar PV output
    - Segmented house rooves for areas with a DSM layer using Digital Surface Model (DSM) data and Ordnance Survey Maps.
    - Estimated shading on roofs from other buildings, creating a pseudo-DSM where necessary.
    - Calculated estimated solar PV output using the formula from the Microgeneration Certification Scheme (MCS).

3.	Estimating the implications of switching to electric heating on the electrical network in terms of additional network load
    - Using the EPC predictions, national electricity consumption and regional network capacity data, we calculated the maximum additional load on the electrical network for homes switching to electric heating.
    - Derived individual home energy usage from national energy statistics and estimated heating costs.

### Further Work

We encourage other councils in the UK to adopt and improve on the open-source pipeline and visualisation tools we have developed, to guide evidence-based policy-making and urban planning. 

There are several ways the tool can be used, for example:
    - To identify areas with houses that should be targeted for retrofitting.
    - The solar PV output estimations can guide policies for potential funding or subsidies to different areas.
    - Energy capacity calculations can inform which areas might cause electrical grid issues during planning.

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
│   ├── additional_load_calc.py	                        # Calculates total additional load and additional peak laod for each home
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
└── technical_docs                                      # All technical documentation for project
    
```

## Brief Folder Description

`processing_data`: Folder that pulls the publiclly available data from multiple sources (requires API key). Cleans, encodes and imputes the data. Prepares the proxy data (not public), and combines it with the publically available data for training/testing of the models. Should be run 						before any other scripts in other folders unless user has pre-prepared data. For further details see [Preparing EPC Data](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/01B_Preparing_EPC_Data.pdf) and [Getting Proxies](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/01A_Getting_Proxies.pdf).

`solar_pv`: estimates the solar photovoltaic output for homes in the target area. Calculates the shadows that fall over a building's roof, combines that with the roof area, average sunlight exposure of the roof, and roof orientation and uses that to estimate the kWh per year that could be 				produced by a particular home. For further details see [Estimating Solar PV](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/04_EstimatingSolarPV.pdf)

`models`: takes the data prepared in the `processing_data` folder, trains a similarity quantification and random forest model, and produces predictions of 	the EPC ratings and the heating type for all the homes not in the EPC database. Performs the additional load calculations for the 						`network_capacity` process. For further details see [EPC and heat type predictions](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/02_EPC_heating_type_predictions.pdf)

`network_capacity`: aggregates the additional load that would be put on the network if homes were to switch from non-electric heating sources to electric heat-pumps. Displays the additoonal load as a function of the network polygons. Also calculates the load difference for the substations with available data. This is the gap between what the network can take as additional load, and how much would be produced by the additional heat pumps. A negetive value for the load differnece indicates the network/substation is in need of upgrades before the heating electrification could be completed. For further details see [Network Capacity](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/03_Network_Capacity.pdf)

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

Users should navigate to the [network_capacity](https://github.com/DSSGxUK/s22_wmca/tree/main/network_capacity) folder to run scripts in this section. That can be done by entering:

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

The solar pv process invloves using a mix of python scripts and jupyter notebooks. User should see the README in the [solar_pv](https://github.com/DSSGxUK/s22_wmca/tree/main/solar_pv) folder for instructions on running the solar_pv process. 

## Technical Documentation

The [technical_docs](https://github.com/DSSGxUK/s22_wmca/tree/main/technical_docs) contain all the technical methodology of the project. It explains the use, functionality, creation and architecture of the project. This will serve as a "How-to" guide for any user to know how the project works.

## Contributors

  - Li-Lian Ang – [GitHub](https://github.com/anglilian), [LinkedIn](https://www.linkedin.com/in/anglilian/)
  - Michael Coughlan – [GitHub](https://github.com/mikecoughlan), [LinkedIn](https://www.linkedin.com/in/mike-k-coughlan/)
  - Shriya C K Tarcar – [GitHub](https://github.com/shri3016), [LinkedIn](https://www.linkedin.com/search/results/all/?heroEntityKey=urn%3Ali%3Afsd_profile%3AACoAADMh2GgBFAcj2lb8uqM2iyu_dF9iiX62Spk&keywords=shriya%20c%20k%20tarcar&origin=RICH_QUERY_SUGGESTION&position=0&searchId=7c10cbb7-ab70-4c62-9ac5-fdf04d921079&sid=%40Oz)
  - Meghna Asthana – [GitHub](https://github.com/asthanameghna), [LinkedIn](https://www.linkedin.com/in/meghna-asthana-1452b097/)

In collaboration with: 
  - Project Manager: Satyam Bhagwanani – [GitHub](https://github.com/sat899), [LinkedIn](https://www.linkedin.com/in/satyam-bhagwanani-934a243a/)
  - Technical Mentor: Mihir Mehta – [GitHub](https://github.com/mihirpsu), [LinkedIn](https://www.linkedin.com/in/mihir79/)

