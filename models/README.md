# Training Models and Getting Predictions
    
Running this set of scripts will take the proceessed data created in the data_preprocessing files and runs it through both a Similarity Quantification model and a Random Forest model. The results are then combined and the calculation for the additional load on the electricity network is perfromed. 

## Scripts

`combining_and_seperating_epc.py`: takes in the processed EPC data and merges it with the proxy data. This is done so that the EPC data required for                training will have the appropriate proxy columns. 

`similarity_quantification_model.py`: makes predictions by comparing the floor footprint of homes.

`multiclass_randomforest.py`: trains a multiclass classification Random Forest model to predict the EPC ratings and the heating type. Also trains a Random Forest Regression model to predict the current-energy-efficiency, a continuious value that maps to the EPC ratings. Requires arg parsing if run outside the `main.py` file.

`combining_SQ_and_RandomForest_models.py`: compares the predictions made by the Similarity Quantification and Random Forest models and chooses which to keep based on a variety of parameters.

`combining_results_for_output.py`: combines all of the predictions and performs the calculation to determine the additional load placed on the electricity network from homes replacing non-electric heating sources with electric heat pumps.

`main.py`: runs all above scripts in the appropriate order, storing each of their outputs and feeding them to the next function.


## Data Requirements

The `data/processed/` folder must contain:
	- `merged_and_encoded_dataframe.csv` output by the `processing_proxies.py` script in the `data_preprocessing` folder.
	- `processed_EPC_data.csv` output from the `data_preprocessing/main.py` file

The `data/raw/` folder must contain:
	- 'demanddata_2017.csv' downloaded from [nationalgridESO - Historic Demand Data](https://data.nationalgrideso.com/demand/historic-demand-data).

Additionally, it is HIGHLY RECCOMMENDED that this code is run in a virtual environment created using either the `requirements.txt` or `env.yml` files in the main directory. Scripts may not function properly, or at all, if not run in this environment.


## Changing the Parameters

There are some hard-coded varaible in place in these scripts that you may want to edit. Particularly the 'input_features' or 'features_to_keep' in the CONFIG dictonary at the top of several of the files in this folder. If the target area is changed from the West Midlands in the United Kingdom, where this was intially created to examine, these inputs will have to be changed to the appropriate names for the region being examined. 


## Running the Scripts
`main.py` should be run from the main directory as all paths are reletive to that directory. If you wish to change the file paths, edit the 
```python
DATA_PATH = 'data/processed/'
OUTPUT_PATH = 'outputs/'
```
at the beginning of each file. Outputs are saved to `outputs/` and models are saved to `models/'. Sub-directories are used for differentiating between epc results and heating type (mainheat) results where appropriate.



```bash
data   
├── raw                                                 # Pulled EPC data
│   ├── building_height	        
│   ├── landbaseprem	            
│   ├── topology	                  
│   ├── ONSUD_AUG_2022_WM.csv    
│   ├── LSOA_domestic_elect_2010-20.xlsx
│   └── sub-regional-fuel-poverty-2022-tables.xlsx
├── processed                                           # Processed EPC data
└── output                                              # Final outputs	
	├── epc
	├── mainheat	                                              # Saved plots from notebooks
models
├── main.py
├── combining_data_and_seperating_epc.py
├── similarity_quantification_model.py
├── multiclass_randomforest.py
├── combining_SQ_and_Randomforest_models.py
├── combining_results_for_output.py
└── models
    ├── epc
    └── mainheat
```


