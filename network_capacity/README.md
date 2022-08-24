# Network Capacity

As the world transitionas away from fossil fuels as a source of energy, one of the most often overlooked pieces of the puzzle is the electrical grid. Transitioning away from using gas and other non-electric heating sources to more efficient heat pumps, the electrical network will be put under increased strain. Here an attempt was made to calculate the additional peak strain in a particular area, and to compare it to the current demand headroom for the substations serving that area. 

Many assumptions were made here in doing these calculations. For a discussion of those assumptions and details about how the calculation was performed see the [technical documentation](https://github.com/DSSGxUK/s22_wmca/blob/main/technical_docs/03_Network_Capacity.pdf).

### Data
Requires the output from the EPC and heating type predictions, as well as either the total-floor-area or the floor-footprint-area. If running these files without having gone through the modeling process, begin with the `additional_load_calc.py` file. Will require:
  - The EPC rating for each home
  - The heating type in a binary format (0 for non-electric, 1 for electric heating) 
  - The total-floor-area or the floor-footprint-area (name this columns `calculatedAreaValue`)
  - `../data/processed/cleaned_epc_data.csv` 
  - `data/raw/demanddata2017.csv`
If running after processing the data through the `models` folder, skip to the `aggregating_points_into_shape_files.py` file to get just the total additional peak load for each area. Or the `comparing_station_headroom.py` file to get the comparison between teh additional peak load and the demand headroom for the primary station layer. These two files require the output from either the `models` folder, or the output from `additional_load_calc.py` file. In addition, the following files are required:
  - `data/shp_files/wmca_distribution-area.shp
  - `data/shp_files/wmca_primary-area.shp`
  - `data/shp_files/wmca_GSP.shp`
  - `data/shp_files/wmca_BSP.shp`
  - `data/shp_files/wmca.shp`
  - `data/raw/WPD-Network-Capacity-Map-27-07-2022.csv`
  - `data/shp_files/wmca_primary.shx`


### Network Capacity Folder Structure
```bash
network_capacity
├── additional_load_calc.py               # calculates the additional load
├── aggregate_points_into_shape_files.py  # aggregates the additional peak load within defined polygons             
├── comparing_station_headroom.py         # aggregates additional peak load and compares to substation headroom
├── data
│    ├── shp_files
│    └── raw
├── plots
└── outputs				
    
```
The station headroom difference cannot be calculated for all polygons. Many are missing stations and some stations do not have the necessary demand headroom data. Those will not appear in the final plots.
