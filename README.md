# 🇸🇬 Singapore Air Quality Data Engineering Project

## 📌 Overview

This project aims to build a data engineering pipeline that collects, processes, and visualizes Singapore’s air quality data. It automates the ingestion of daily pollutant readings, loads them into a Snowflake data warehouse, and displays insights on a Streamlit dashboard.

---

## 📊 Objectives

- Ingest daily PM2.5 and PSI pollutant readings from [Data.gov.sg](https://data.gov.sg/) APIs. (Using )
- Orchestrate automated ETL using GitHub Actions and Snowflake Tasks.
- Use dynamic tables in Snowflake for near real-time updates.
- Visualize pollution trends by region and pollutant with a Streamlit dashboard.

---

## 🗂️ Data Sources

The following 2 APIs from [Data.gov.sg](https://data.gov.sg/) are used:

- **[PM2.5 Readings API](https://data.gov.sg/datasets?query=pm25&page=1&resultId=d_e1058d6974c877257e32048ab128ad83)**  
  Retrieves hourly PM2.5 levels by region.

- **[PSI Readings API](https://data.gov.sg/datasets?query=PSI&page=1&resultId=d_fe37906a0182569d891506e815e819b7)**  
  Provides hourly PSI and sub-index pollutant levels (PM10, SO2, CO, NO2, O3) across regions.

---

## ⚙️ Data Pipeline

### ⏰ GitHub Actions (Ingestion)

- Runs daily at **1:00 AM SGT**.
- Python script calls both APIs and saves the previous day's readings as JSON files.
- Uploads JSON files to a **Snowflake internal stage**.

### ❄️ Snowflake Tasks (Staging)

- Two Snowflake tasks run daily at **2:00 AM SGT**:
  - **Task 1**: Loads PM2.5 JSON data into `stg_pm25`
  - **Task 2**: Loads PSI JSON data into `stg_psi`

---

## 🧊 Snowflake Architecture

### 🔹 Schema Layers

- **Staging Tables**:  
  - `stg_pm25`, `stg_psi`

- **Cleaned Tables**:  
  - `clean_pm25`, `clean_psi`

- **Transformed Tables** (Dynamic):
  - `dim_region`, `dim_datetime`
  - `fact_pollutants`: Hourly pollutant data
  - `agg_region_pollution`: Aggregated pollution data by region and day

### 🔁 Dynamic Tables

- Downstream tables are **dynamic tables** with a **target lag of 30 minutes**, ensuring fresh data updates every half hour.

---

## 📈 Streamlit Dashboard

### Features:

- **Most & Least Polluted Region**  
  - For any selected day based on AQI/PSI.

- **Hourly Pollutant Breakdown**  
  - View individual sub-index values by hour and region.

- **Daily Summary**  
  - Day-level breakdown for all pollutants by region.

- **User Filters**  
  - Filter by date, region, and specific pollutant type.

---

## 🧪 Tech Stack

| Component        | Tool / Platform         |
|------------------|--------------------------|
| Data Ingestion   | Python, Requests, JSON   |
| Orchestration    | GitHub Actions           |
| Data Warehouse   | Snowflake                |
| Scheduling       | Snowflake Tasks          |
| Transformation   | Snowflake Dynamic Tables |
| Visualization    | Streamlit                |
| Storage          | Snowflake Stage          |

---

## 📁 Project Structure

