# 🇸🇬 Singapore Air Quality Data Engineering Project

## 📈 Streamlit SG AQI Dashboard
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://singaporeairqualitydashboardpy-7eftmph7oespw6mejasnum.streamlit.app/)

## 📌 Overview

This project aims to build a data engineering pipeline that collects, processes, and visualizes Singapore’s air quality data. It automates the ingestion of daily pollutant readings, loads them into a Snowflake data warehouse, and displays insights on a Streamlit dashboard.

## 📊 Objectives

- Ingest daily PM2.5 and PSI pollutant readings from data.gov.sg APIs.
- Orchestrate automated ETL using GitHub Actions and Snowflake Tasks.
- Use dynamic tables in Snowflake for near real-time updates.
- Visualize pollution trends by region and pollutant with a Streamlit dashboard.

## 🗂️ Data Sources

The following 2 APIs from data.gov.sg are used:

### [PM2.5 Readings API](https://data.gov.sg/datasets?query=PM2.5&resultId=d_e1058d6974c877257e32048ab128ad83&page=1)
Retrieves hourly PM2.5 levels by region. 

### [PSI Readings API](https://data.gov.sg/datasets?query=Psi&page=1&resultId=d_fe37906a0182569d891506e815e819b7)
Provides hourly PSI and sub-index pollutant levels (PM10, SO2, CO, NO2, O3) across regions.

##  Architecture
![E2E Diagram](https://github.com/ArronATW/Singapore_Air_Quality_Project/blob/main/architecture.png)

### ⏰ GitHub Actions (Data Ingestion Workflow)

- Calls the data.gov.sg PM2.5 and PSI APIs to fetch air quality readings for the previous day.
- Saves the responses as structured `.json` files with timestamped filenames.
- Uploads these files to the appropriate folders in the Snowflake external stage.

This ensures a reliable and automated pipeline to bring external environmental data into Snowflake for downstream processing.

### ❄️ Snowflake
![Data Lineage Diagram](https://github.com/ArronATW/Singapore_Air_Quality_Project/blob/main/Snowflake%20Data%20Lineage%20Diagram.png)
![Schemas Diagram](https://github.com/ArronATW/Singapore_Air_Quality_Project/blob/main/SG_AQI_DB_SCHEMAS.png)
#### Staging Layer

The staging layer handles the initial loading and preparation of air quality data from raw sources before further transformation.

- **Data Sources:**  
  Historical 2024 data was initially downloaded from data.gov.sg to populate the `sg_pm25_raw` and `sg_psi_raw` tables.

- **Workflow:**  
  Raw files are ingested into temporary staging tables (`sg_pm25_stage_temp`, `sg_psi_temp`) for validation and standardization.  
  Cleaned data is then inserted into the raw tables (`sg_pm25_raw`, `sg_psi_raw`) with metadata fields such as file name, MD5 hash, and load timestamp to ensure traceability.  
  A daily scheduled task (`UPDATE_SG_PSI_AIR_QUALITY_DATA`) loads new PSI readings from JSON API dumps and merges them into the `sg_psi_raw` table at 2am SGT (UTC+8).

#### Cleaned Layer

The cleaned layer consolidates and standardizes air quality data by joining and harmonizing the PM2.5 and PSI raw datasets.

- PM2.5 hourly data from `sg_pm25_raw` is cleaned by replacing nulls with zero.
- PSI data from `sg_psi_raw` is filtered to exclude the 'national' region and similarly cleaned.
- The two datasets are joined on date, timestamp, and region to produce a unified, consistent view without duplicate columns.

This layer ensures minimal, clean, and complete records ready for further analysis or downstream processing.

#### Transformed Layer

This layer performs key transformations and prepares data for analytical consumption through fact and dimension tables:

- **Custom Functions:**  
  - `three_sub_index_met`: Checks if at least three pollutant sub-indices are greater than zero.  
  - `get_prominent_pollutant`: Determines the pollutant with the highest sub-index value.

- **Date Dimension (`sg_aqi_date_dim`):**  
  Creates a date dimension keyed by hashed timestamp, including year, month, quarter, day, hour, and day of the week for time-based analysis.

- **Location Dimension (`sg_aqi_location_dim`):**  
  Aggregates unique locations with latitude, longitude, and region, keyed by hashed coordinates.

- **Fact Table (`sg_air_quality_fact`):**  
  Combines date and location foreign keys with pollutant sub-indices, prominent pollutant, and conditional AQI for efficient querying in downstream analytics and reporting.

- **Wide Transformed Table (`sg_aqi_transformed_wide_dt`):**  
  - Extracts date-time parts (year, month, quarter, day, hour) and geographic coordinates.  
  - Calculates the most prominent pollutant and conditionally sets the AQI based on the presence of at least three active pollutant sub-indices.  
  - This wide table consolidates multiple pollutant metrics and calculated fields into a single flattened dataset, reducing complex joins in downstream queries and dashboards, improving query performance and simplifying data consumption.  
  - By including detailed date parts and geographic coordinates, it provides a comprehensive, ready-to-use snapshot of air quality data.

- **Hourly Regional Aggregation (`agg_region_fact_hour_level`):**  
  - Aggregates pollutant sub-indices to hourly averages by region.  
  - Joins fact data with date and location dimensions.  
  - Calculates average values for PM10, PM2.5, O3, CO, and SO2 sub-indices.  
  - Computes the prominent pollutant and AQI based on the average sub-indices using custom functions.  
  - Designed for near real-time (30-minute lag) hourly air quality insights by region.

- **Daily Regional Aggregation (`agg_region_fact_day_level`):**  
  - Further aggregates the hourly regional data to daily averages by region.  
  - Averages hourly pollutant values across each day.  
  - Computes prominent pollutant and daily AQI similarly to the hourly table.  
  - Supports daily trend analysis and summary reporting in dashboards.






