# Import Python packages
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from snowflake.snowpark import Session

#######################
# Page configuration
st.set_page_config(
    page_title="SG Air Quality Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


#######################

def get_date_selection():
  date_query = f"""
      SELECT DATE(MEASUREMENT_TIME) AS measurement_date 
      FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_HOUR_LEVEL 
      GROUP BY measurement_date
      ORDER BY measurement_date DESC
  """
  date_list = session.sql(date_query)
  date_options = [date[0] for date in date_list.collect()]
  date_option = st.date_input('Select Date', min_value=min(date_options), max_value=max(date_options), value=max(date_options))
  return date_option

def get_region_selection():
  region_query = """
      SELECT REGION FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_HOUR_LEVEL 
      GROUP BY REGION
      ORDER BY REGION
  """
  region_list = session.sql(region_query)
  region_options = [row["REGION"] for row in region_list.collect()]
  region_option = st.selectbox('Select Region', region_options)
  return region_option

def most_polluted_region_box_header():

  # SQL Query to get the Most Polluted Region (Highest AQI)
  most_polluted_sql = f"""
      SELECT REGION, MAX(AQI) AS MAX_AQI
      FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_DAY_LEVEL
      WHERE MEASUREMENT_DATE = '{date_option}'
      GROUP BY REGION
      ORDER BY MAX_AQI DESC
      LIMIT 1;
  """
   
  # Fetch data for the Most Polluted Region
  most_polluted_data = session.sql(most_polluted_sql).collect()
  most_polluted_region = most_polluted_data[0]["REGION"]
  most_polluted_aqi = most_polluted_data[0]["MAX_AQI"]

  st.metric(
            label="Most Polluted Region",
            value=most_polluted_region,
            delta=f"AQI: {most_polluted_aqi}",
            delta_color="inverse"  # Inverse color to highlight the delta (positive/negative)
        )
  return most_polluted_region

def least_polluted_region_box_header():

  # SQL Query to get the Least Polluted Region (Lowest AQI)
  least_polluted_sql = f"""
      SELECT REGION, MIN(AQI) AS MIN_AQI
      FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_DAY_LEVEL
      WHERE MEASUREMENT_DATE = '{date_option}'
      GROUP BY REGION
      ORDER BY MIN_AQI ASC
      LIMIT 1;
  """
   
  # Fetch data for the Least Polluted Region
  least_polluted_data = session.sql(least_polluted_sql).collect()
  least_polluted_region = least_polluted_data[0]["REGION"]
  least_polluted_aqi = least_polluted_data[0]["MIN_AQI"]

  st.metric(
          label="Least Polluted Region",
          value=least_polluted_region,
          delta=f"AQI: {least_polluted_aqi}",
          delta_color="normal"  # Normal color for the delta
      )
  return least_polluted_region

def most_polluted_region_pollutant_distribution_donut_chart(most_polluted_region):

  # SQL Query to get pollutant sub-indices for the most polluted region
  most_pollutants_sql = f"""
            SELECT 
                MEASUREMENT_DATE,
                REGION,
                PM10_AVG,
                PM25_AVG,
                O3_AVG,
                CO_AVG,
                SO2_AVG
            FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_DAY_LEVEL
            WHERE REGION = '{most_polluted_region}' AND
                MEASUREMENT_DATE = '{date_option}'
        """
  most_pollutants_data = session.sql(most_pollutants_sql).collect()

  most_pollutants_df = pd.DataFrame(most_pollutants_data, columns=["MEASUREMENT_DATE", "REGION", "PM10", "PM2.5", "O3", "CO", "SO2"])
    
    # Create a DataFrame for donut chart
  most_polluted_donut_df = most_pollutants_df.melt(id_vars=["REGION"], var_name="Pollutant", value_name="SubIndex")

    # Donut Chart with discrete darkmint color scale
  most_polluted_fig = px.pie(
      most_polluted_donut_df, 
      names="Pollutant", 
      values="SubIndex", 
      hole=0.7,  # Creates the donut effect
      title=f"Distribution for {most_polluted_region} region",
      color="Pollutant",  # Use Pollutant for the color scale
      color_discrete_sequence=px.colors.sequential.Plasma  # Apply darkmint discrete color scale
  )

  st.plotly_chart(most_polluted_fig, use_container_width=True)

def least_polluted_region_pollutant_distribution_donut_chart(least_polluted_region):
   # DISTRIBUTION OF POLLUTANTS (DONUT CHARTS)
      
  least_pollutants_sql = f"""
      SELECT 
          MEASUREMENT_DATE,
          REGION,
          PM10_AVG,
          PM25_AVG,
          O3_AVG,
          CO_AVG,
          SO2_AVG
      FROM SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_DAY_LEVEL
      WHERE REGION = '{least_polluted_region}' AND
          MEASUREMENT_DATE = '{date_option}'
  """
  least_pollutants_data = session.sql(least_pollutants_sql).collect()

  # Convert to DataFrame for processing
  least_pollutants_df = pd.DataFrame(least_pollutants_data, columns=["MEASUREMENT_DATE", "REGION", "PM10", "PM2.5", "O3", "CO", "SO2"])
  
  least_polluted_donut_df = least_pollutants_df.melt(id_vars=["REGION"], var_name="Pollutant", value_name="SubIndex")

  least_polluted_fig = px.pie(
      least_polluted_donut_df, 
      names="Pollutant", 
      values="SubIndex", 
      hole=0.7,  # Creates the donut effect
      title=f"Distribution for {least_polluted_region} region",
      color="Pollutant",  # Use Pollutant for the color scale
      color_discrete_sequence=px.colors.sequential.YlGnBu  # Apply darkmint discrete color scale
  )

  st.plotly_chart(least_polluted_fig, use_container_width=True)

def AQI_by_hour_line_chart():
  # AQI by Hour (Line Chart)
  # Query hourly AQI values for selected region and date
  aqi_hour_sql = f"""
      SELECT 
          HOUR(MEASUREMENT_TIME) AS Hour,
          AQI
      FROM 
          SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_HOUR_LEVEL
      WHERE 
          REGION = '{region_option}' 
          AND DATE(MEASUREMENT_TIME) = '{date_option}'
      ORDER BY HOUR
  """

  # Execute query and visualize results
  aqi_hour_df = session.sql(aqi_hour_sql).collect()

  
  if not aqi_hour_df:
    st.warning("No AQI hourly data available for this region and date.")
  else:
      df_aqi_hour = pd.DataFrame(aqi_hour_df, columns=['Hour', 'AQI'])

      line_chart = alt.Chart(df_aqi_hour).mark_line(point=True, color='green').encode(
          x=alt.X('Hour:O', title='Hour of Day'),
          y=alt.Y('AQI:Q', title='AQI'),
          tooltip=['Hour', 'AQI']
      ).properties(
          width=700,
          height=400
      )

      st.altair_chart(line_chart, use_container_width=True)

def Pollutant_sub_index_by_hour_bar_chart():
   
  # POLLUTANT SUB-INDICES BY HOUR (BAR CHART)
  trend_sql = f"""
      SELECT 
          HOUR(MEASUREMENT_TIME) AS Hour,
          PM10_AVG,
          PM25_AVG,
          O3_AVG,
          CO_AVG,
          SO2_AVG
      FROM 
          SG_AQI_DB.CONSUMPTION_SCH.AGG_REGION_FACT_HOUR_LEVEL
      WHERE 
          REGION = '{region_option}' and
          DATE(MEASUREMENT_TIME) = '{date_option}'
      ORDER BY MEASUREMENT_TIME
  """

  sf_df = session.sql(trend_sql).collect()

  if not sf_df:
      st.warning("No data to plot.")
  else:
      pd_df = pd.DataFrame(sf_df, columns=['Hour', 'PM10', 'PM2.5', 'O3', 'CO', 'SO2'])
      melted_df = pd_df.melt(id_vars='Hour', var_name='Pollutant', value_name='SubIndex')

      bar_chart = alt.Chart(melted_df).mark_bar().encode(
          x=alt.X('Hour:O', title='Hour of Day'),
          y=alt.Y('SubIndex:Q', title='Sub-Index Value'),
          color=alt.Color('Pollutant:N', scale=alt.Scale(scheme='viridis')),
          tooltip=['Hour', 'Pollutant', 'SubIndex']
      ).properties(width=700, height=400)

      st.altair_chart(bar_chart, use_container_width=True)

def Max_AQI_by_region_heat_map():
   
  # heat-style scatter map
  aqi_map_sql = f"""
      SELECT 
          REGION,
          LATITUDE,
          LONGITUDE,
          MAX(AQI) AS MAX_AQI
      FROM 
          SG_AQI_DB.CONSUMPTION_SCH.SG_AQI_TRANSFORMED_WIDE_DT
      WHERE 
          DATE(TIMESTAMP) = '{date_option}'
      GROUP BY REGION, LATITUDE, LONGITUDE
  """
  aqi_map_data = session.sql(aqi_map_sql).collect()
  df_map = pd.DataFrame(aqi_map_data)

  fig = px.scatter_mapbox(
      df_map,
      lat="LATITUDE",
      lon="LONGITUDE",
      size="MAX_AQI",  # optional: size bubbles by AQI
      color="MAX_AQI",
      color_continuous_scale="darkmint",
      size_max=40,
      zoom=10,
      mapbox_style="carto-positron",
      hover_name="REGION",
      hover_data={"LATITUDE": False, "LONGITUDE": False, "MAX_AQI": True}
  )

  fig.update_traces(
      marker=dict(
      sizemode='area',
      sizeref=2.*max(df_map["MAX_AQI"])/(100**2),  # adjust for better scaling
      sizemin=6  # minimum bubble size to ensure visibility
    ), 
    textposition="top center",
    textfont=dict(size=12, color="black")  # label styling
  )
  st.plotly_chart(fig, use_container_width=True)

connection_parameters = {
    "account": st.secrets["snowflake"]["account"],
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
    "role": st.secrets["snowflake"]["role"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
}
session = Session.builder.configs(connection_parameters).create()

#######################
# Sidebar
with st.sidebar:
    st.title('SG Air Quality Dashboard')
    date_option = get_date_selection()
    region_option = get_region_selection()
    
#######################

with st.container():
  
  st.markdown("<h3 style='text-align: center;'>Air Quality Extremes by Region</h3>", unsafe_allow_html=True)  
  # Row 1: Metric boxes
  col1, col2, col3 = st.columns([1, 1, 2])
  with col1:
    most_polluted_region = most_polluted_region_box_header()
    most_polluted_region_pollutant_distribution_donut_chart(most_polluted_region)
        
  with col2:
    least_polluted_region = least_polluted_region_box_header()
    least_polluted_region_pollutant_distribution_donut_chart(least_polluted_region)
    
  with col3: 
    st.markdown("<h3 style='text-align: center;'>AQI by Hour</h3>", unsafe_allow_html=True)
    AQI_by_hour_line_chart()


st.markdown("<h3 style='text-align: center;'>Pollutant Sub-Indices by Hour</h3>", unsafe_allow_html=True)
Pollutant_sub_index_by_hour_bar_chart()

st.markdown(f"<h3 style='text-align: center;'>Maximum AQI by Region on {date_option.strftime('%Y-%m-%d')}</h3>", unsafe_allow_html=True)
Max_AQI_by_region_heat_map()
