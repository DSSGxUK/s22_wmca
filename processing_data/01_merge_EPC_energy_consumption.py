
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import pickle
from tqdm import tqdm
import os
from dotenv import load_dotenv, find_dotenv

PROC_DATA_PATH = 'data/processed/'
RAW_DATA_PATH = 'data/raw/'


# Get all local authority codes and corresponding council names
page = requests.get("https://epc.opendatacommunities.org/docs/api/domestic#domestic-local-authority").text
soup = BeautifulSoup(page)

table = soup.findAll('table')[3]
la_code_dict = {}

for tr in table.findAll('tr')[1:]:
   code, local_auth = tr.findAll('td')
   la_code_dict[local_auth.text] = code.text

# Get local authority codes for councils in WMCA
WMCA_councils = open(RAW_DATA_PATH+"WMCA_council.txt").read().split(",")[:-1]
WMCA_code = [la_code_dict[i] for i in WMCA_councils]
WMCA = dict(zip(WMCA_code, WMCA_councils))

# Save codes for future use
with open(RAW_DATA_PATH+'WMCA_council_code.pkl', 'wb') as f:
    pickle.dump(WMCA, f)


# Electricity consumption data
elec_consump_df = pd.read_excel(RAW_DATA_PATH+'LSOA_domestic_elec_2010-20.xlsx', sheet_name="2020", header=4)
elec_consump_df.columns = [
        'la_code', 'la', 'msoa_code', 'msoa', 'lsoa_code', 'lsoa', 'num_meter', 'total_consumption', 'mean_counsumption', 'median_consumption'
        ]

# Filter for local authorities in WMCA
elec_consump_df = elec_consump_df[elec_consump_df['la_code'].isin(WMCA_code)]


# Post code to LSOA to MSOA converting data
postcode_df = pd.read_csv(RAW_DATA_PATH+"PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU.csv", low_memory=False)

with open(RAW_DATA_PATH+'WMCA_council_code.pkl', 'rb') as f:
    WMCA_code = pickle.load(f)

# Filter for local authorities in WMCA
postcode_df = postcode_df[postcode_df['ladcd'].isin(WMCA_code)]


# Merge data to get postcodes associated with each LSOA code
postcode_elec_consump_df = pd.merge(postcode_df, elec_consump_df, left_on="lsoa11cd", right_on="lsoa_code", how="left")
postcode_elec_consump_df = postcode_elec_consump_df[['pcds', 'la', 'la_code', 'msoa_code', 'msoa', 'lsoa_code', 'lsoa', 'num_meter', 'total_consumption', 'mean_counsumption',
       'median_consumption']]


# find .env automagically by walking up directories until it's found
dotenv_path = find_dotenv()

# load up the entries as environment variables
load_dotenv(dotenv_path)

AUTH_TOKEN = os.environ.get("EPC_AUTH_TOKEN")


def get_epc_data(postcode, num_rows=5000):
    """
    Pull data from Domestic Energy Performance Certificates API.

    Input:
    postcode(str): (1) Postcode 
    num_rows(int): Number of rows to pull. Max 5000 allowed at one time

    Output:
    (str): Pulled data from API

    """
    headers = {
        'Authorization': f'Basic {AUTH_TOKEN}',
        'Accept': 'application/json'
    }
    params = {
        'postcode': postcode,
        'size': num_rows
    }
    url = f'https://epc.opendatacommunities.org/api/v1/domestic/search'
    res = requests.get(url, headers=headers, params=params)
    return res.text


# Pull WMCA postcode data and save as CSV
result = list()

for code in tqdm(postcode_elec_consump_df.pcds.unique()):
    requested_data = get_epc_data(code)
    if len(requested_data)!=0:
        result.extend(json.loads(requested_data)['rows'])


EPC_data = pd.DataFrame(result)

EPC_data['uprn'] = pd.to_numeric(EPC_data['uprn'],errors='coerce') # needs to be float for joining

# Merge EPC and electricity consumption data on postcode
EPC_postcode_elec_consump = pd.merge(EPC_data, postcode_elec_consump_df, left_on="postcode", right_on="pcds", how="left")
EPC_postcode_elec_consump.drop(columns=["pcds", "address1", "address2", "address3", 'uprn-source'], inplace=True)


# Export postcodes
with open(PROC_DATA_PATH+'WMCA_postcodes.pkl', 'wb') as fp:
    pickle.dump(EPC_postcode_elec_consump.postcode.unique(), fp)


fuel_poverty_df = pd.read_excel(RAW_DATA_PATH+"sub-regional-fuel-poverty-2022-tables.xlsx", sheet_name="Table 3", header=2)
fuel_poverty_df.drop(columns=["LSOA Name", "LA Code", "LA Name", "Region", "Unnamed: 8"], inplace=True)
fuel_poverty_df.columns = ["lsoa_code", "num_households", "num_households_fuel_poverty", "prop_households_fuel_poor"]


EPC_postcode_elec_consump_fuel_poverty = pd.merge(EPC_postcode_elec_consump, fuel_poverty_df, on="lsoa_code", how="left")


uprn_df = pd.read_csv(RAW_DATA_PATH+"osopenuprn_202205.csv")
uprn_df = uprn_df[['UPRN', 'LATITUDE', 'LONGITUDE']]


# Match column type with EPC UPRN so that we can merge
uprn_df.UPRN = uprn_df.UPRN.astype('object')


EPC_postcode_elec_consump_fuel_poverty_uprn = pd.merge(old_df, uprn_df, left_on="uprn", right_on="UPRN", how="left")
# EPC_postcode_elec_consump_fuel_poverty_uprn.drop(columns=["UPRN", 'la', 'la_code'], inplace=True)
EPC_postcode_elec_consump_fuel_poverty_uprn.drop(columns=["UPRN"], inplace=True)


EPC_postcode_elec_consump_fuel_poverty_uprn.to_csv(PROC_DATA_PATH+"pre_clean_merged_epc_data.csv", index=False)


