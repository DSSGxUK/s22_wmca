# Estimating Solar PV Output
Solar PV output is determined by the amount of solar radiation a module receives, influenced by the weather (cloud cover, temperature, shade etc.), and the efficiency of the module. The [Microgeneration Certification Scheme Service](https://mcscertified.com/) (MCS) creates and maintains the standards for low-carbon products and installations used to produce electricity and heat from renewable sources in the UK. It has data on all the solar PV arrays installed in the UK with their models and estimated yearly solar PV output, calculated from a formula using the (1) shading on the roof, (2) roof slope, (3) roof azimuth or orientation towards the Sun and (4) number of solar panels that can be installed.

The problem is that determining these four input variables requires a site visit. Instead, the following script derives these values from other data source and compute the estimated solar PV output. We will focus our scope on residential buildings in the West Midlands. For more details, see our in-depth documentation.

## Note
I successfully ran the code on my local Windows machine. However, the licensed Ordinance Survey data required us to use Aridhia (a secure platform) to run the scripts. The scripts got stuck on clipping the building footprint shapefiles (function `clip_polygons`) without throwing an error and we were unable to fix the issue. Therefore, we could not get estimates for all of the West Midlands, only one 5km by 5km tile.

### Data
- Ordinance Survey Building Height Attribute (format: `{tilename}.csv`)
- Ordinance Survey Topology, Topographic Area (format: `5882272-{tilename}.gml`)
- Building footprint shapefiles (merged from `getting_proxies`, format: `{tilename}.geojson`)
- [LIDAR Composite DSM 1m](https://environment.data.gov.uk/DefraDataDownload/?Mode=survey)
- `02_calc_pv_output`: [MCS Irradiance Dataset](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&ved=2ahUKEwi2upKmosv5AhWTiFwKHRy2CSAQFnoECBIQAQ&url=https%3A%2F%2Fmcscertified.com%2Fwp-content%2Fuploads%2F2019%2F08%2FIrradiance-Datasets.xlsx&usg=AOvVaw27Q48eb99hbZqKVtBAbKzr)
- `03_test_pv_output`: MCS Baseline data on solar PV installations and estimated output

### Installations
- `01_calc_shadow`: [QGIS 3.26](https://www.qgis.org/en/site/forusers/download.html)
- `01_calc_shadow`: [UMEP](https://umep-docs.readthedocs.io/en/latest/) plugin on QGIS (Plugins > Manage and Install Plugins… and search for UMEP for Processing)
- `01_calc_shadow`: UMEP has certain dependencies on Python so if you run into any issues check [here](https://umep-docs.readthedocs.io/projects/tutorial/en/latest/Tutorials/PythonProcessing1.html?highlight=dependencies).
- `02_calc_pv_output`: [pvlib](https://pvlib-python.readthedocs.io/en/stable/user_guide/package_overview.html) Python library
- `02_calc_pv_output`: [geopandas](https://geopandas.org/en/stable/getting_started/install.html) Python library

### Folder structure
```bash
solar pv
├── 00_compare_grid   
│   ├── compare_grid.ipynb	            
│   ├── DSM_grid.txt	                # DSM tiles received from Defra
│   ├── osmapFileName.txt	            # Ordinance Survey data for West Midlands
│   ├── os_mapping.pkl	                # Dictionary to map building footprint files and DSM data
│   └── missing_tiles.txt               # Areas in West Midlands not covered by DSM
├── 01_calc_shadow              
│   ├── temp	                        # Auto-created to store temp files
│   ├── output	                        # Auto-created to store outputs
│   │   ├── roof_segments	    
│   │   ├── roof_segments_unfiltered
│   │   └── no_DSM
│   ├── shading_with_DSM.py	            # Roof segmentation & shading
│   ├── shading_without_DSM.py	        # Pseudo-DSM & shading
│   └── launch.bat	                    # Runs OSGeo Shell
├── 02_calc_pv_output                   # PV output estimates
│   ├── output                          # Stores csv outputs
│   ├── MCS_output.py	
│   └── pvlib_output.py
└── 03_test_pv_output					
    └── pv_test_set.ipynb  
```
    
### Setup
`01_calc_shadow`
1. Follow the [instructions](https://www.qgistutorials.com/en/docs/running_qgis_jobs.html) from step 14-17 to set up the paths.
2. Ensure folder structure for input data is correct. All input data should be in the top folder `data/processed/` and `data/raw/`.
3. Edit last line of `launch.bat` to select Python script to execute.
4. Run `launch.bat` from the OSGeo Shell (for Windows, other OS might need different setups).

`02_calc_pv_output`
1. Run Python script from the folder.

`03_test_pv_output`
1. Run to compare estimations for solar PV output

## Future Work
The current methodology leaves much to be desired to get better estimates:
- Acquire validation data for roof segments, aspect, slope and area
- Improve roof segmentation for each segment to at least look visually correct
- WMCA had concerns about the additional load on the electricity grid when more solar panels are installed. Estimate the self-consumption to determine the amount of electricity pushed back into the grid.
- Acquire validation data for actual solar output to better compare between estimates: (1) pvlib, (2) MCS, and (3) MCS with our inputs.
- Determine the number of solar panel modules that can fit on a roof based on its shape
- The current shading method does not account for shadows cast by houses that lie beyond the border of the tile. This means there is a higher rate of error for all the houses along the border of each tile. I had planned to solve for this by breaking each tile into overlapping smaller tiles. Tiling also prevents QGIS from crashing with too big a tile.

## References
The method applied here was largely inspired by [Mapping Solar PV Potential in Ambleside (Dec 2019) by Alex Boyd](https://aafaf.uk/uploads/7/2/0/5/72055569/mapping_solar_pv_potential_in_ambleside__final_updated__jan_2020.pdf). 
