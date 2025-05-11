import requests
import json
from datetime import datetime, timedelta
from snowflake.snowpark import Session
import sys 
import pytz
import logging
import os

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s - %(message)s')
ist_timezone = pytz.timezone('Asia/Singapore')
current_time_ist = datetime.now(ist_timezone)
timestamp = current_time_ist.strftime('%Y_%m_%d_%H_%M_%S')
file_name = f'sg_pm2.5_air_quality_data_{timestamp}.json'
today_string = current_time_ist.strftime('%Y_%m_%d')

def snowpark_basic_auth() -> Session:
  connection_parameters = {
        "ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT"),
        "USER": os.getenv("SNOWFLAKE_USER"),
        "PASSWORD": os.getenv("SNOWFLAKE_PASSWORD"),
        "ROLE": os.getenv("SNOWFLAKE_ROLE"),
        "DATABASE": os.getenv("SNOWFLAKE_DATABASE"),
        "SCHEMA": os.getenv("SNOWFLAKE_SCHEMA"),
        "WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE")
    }

  # creating snowflake session object
  return Session.builder.configs(connection_parameters).create()

def get_data_for_yesterday():
  sgt = pytz.timezone("Asia/Singapore")
  now_sgt = datetime.now(sgt)
  yesterday = (now_sgt - timedelta(days=1)).strftime('%Y-%m-%d')
  get_data_for_data_range(yesterday, yesterday)

def get_data_for_data_range(starting, ending):

  start_date = datetime.strptime(starting, "%Y-%m-%d")
  end_date = datetime.strptime(ending, "%Y-%m-%d")
  current_date = start_date

  api_urls = {
    'PSI': 'https://api-open.data.gov.sg/v2/real-time/api/psi',
    'pm2.5': 'https://api-open.data.gov.sg/v2/real-time/api/pm25'
  }

  while current_date <= end_date:

    for dataname, api_url in api_urls.items():
      file_name = f'sg_{dataname}_air_quality_data_{current_date.strftime("%Y_%m_%d")}.json'
      today_string = current_date.strftime('%Y_%m_%d')
      params = {'date': current_date.strftime('%Y-%m-%d')}
      headers = {'accept': 'application/json'}
      try:
        response = requests.get(api_url, params=params, headers=headers)
        logging.info(f"Fetching {dataname} data for date: {current_date.strftime('%Y-%m-%d')}")
        if response.status_code == 200:
          json_data = response.json()
          with open(file_name, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)
          logging.info(f'File written: {file_name}')
                  
          stg_location = f'@SG_AQI_DB.STAGE_SCH.SG_AQI_STAGE_2025/{dataname.upper()}/{today_string}/'
          sf_session = snowpark_basic_auth()
          sf_session.file.put(file_name, stg_location)
          logging.info(f'File placed in stage: {stg_location}')
                  
          lst_query = f'list {stg_location}{file_name}'
          result_lst = sf_session.sql(lst_query).collect()
          logging.info(f'Listed in stage: {result_lst}')
        else:
          logging.error(f"Error: {response.status_code} - {response.text}")
      except Exception as e:
        logging.error(f"An error occurred on {current_date.strftime('%Y-%m-%d')}: {e}")
      
    current_date += timedelta(days=1)  # Always move forward, even on failure

#run to populate my snowflake stage with json files
# get_PM25_data_till_yesterday()
# get_PSI_data_till_yesterday()

# get_data_for_yesterday()
get_data_for_data_range("2025-01-01", "2025-05-09")
