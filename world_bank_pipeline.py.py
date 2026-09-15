import numpy as np
import pandas as pd
import requests
import time #We imported time because when we run our loop, we send request like for 346 pages we send req 346 times by doing this our API may consider us a chatbot and it blocks our requests. So to ensure this we use time like 0.2 seconds or 0.3 seconds delay between each req and 

url = "https://api.worldbank.org/countries?format=json&per_page=300"

response = requests.get(url)
print(response.status_code)
data = response.json()
print(data)
print(data[0]) #For getting information of data also called metadata.
print(len(data)) 

countries = data[1]
countries = pd.DataFrame(countries)
print(countries)
print(countries["region"][0])

# Data cleaning: Drop 'adminregion' and 'capitalcity'; extract nested values from 'region', 'incomeLevel', and 'lendingType'.

countries["region"] = countries["region"].apply(lambda x:x["value"])
print(countries["region"])

countries["incomeLevel"] = countries["incomeLevel"].apply(lambda x:x["value"])
print(countries["incomeLevel"])

countries["lendingType"] = countries["lendingType"].apply(lambda x:x["value"])
print(countries["lendingType"])

countries.drop(columns=["adminregion", "capitalCity"], inplace=True) #This inplace = True, modifies the existing data frame rather than creating a new one.
print(countries["region"].unique()) #To check which all countries are present in our dataset
print(countries[countries["region"]=="Aggregates"])

#--------------code for indicators--------------
base_url = "https://api.worldbank.org/v2/indicators?format=json" # Initial url "https://api.worldbank.org/countries/USA/indicators" v2 means passing the information of that particular region where it is used and the output passes on to next information. question mark means to get complete information of that particular parameter after which question mark is placed.
response = requests.get(base_url)
print(response.status_code) #If this output is 200 that indicates that connection is estabilished; 200 is the standardized HTTP code for “success”.

indicators_data = response.json() # To bring response in json mode.

print(indicators_data[0]) #Here 0 means (Metadata about the request) and 1 means (Actual indicator data).
print(pd.DataFrame(indicators_data[1]))

RUN_API = False

if RUN_API:
    all_dfs=[]
    for i in range(1, 526):
        url = f"https://api.worldbank.org/v2/indicators?format=json&per_page=500&page={i}" 
        response = requests.get(url)

        if response.status_code==200:
            data=response.json()

            if len(data)<2:
                print(f"No data at page{i}")

            indicators=data[1]
            df = pd.DataFrame([{"id": item["id"],
                            "name": item["name"]} for item in indicators])
            all_dfs.append(df)
            print(f"Page{i}: {len(df)} indicators collected")

        else:
            print(f"Failed to fetch page{i}, status_code {response.status_code}")

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv("final_df.csv", index=False)
    print("API data saved")

else:
    final_df = pd.read_csv("final_df.csv")

'''
To check if above code is working or not 
print("Rows:", len(final_df))
print("Columns:", final_df.columns.tolist())
print(final_df.head()) 
'''

# Extract values for various indicators under the domain for each country 

indicators_group = {
    "economic_activity_growth": [
        "NY.GDP.MKTP.KD.ZG", #GDP GROWTH ( annual % )
        "NY.GDP.PCAP.CD", #GDP per capita ( Current US$ )
        ],

    "labour_market_indicators": [
        "SL.UEM.TOTL.ZS", #Unemployment level
        "SL.UEM.1524.ZS", #Unemployment youth total ( ages 15-24 )
        "SL.TLF.TOTL.IN", #Labour Force, Total
        ],

    "poverty_inequality": [
        "SI.POV.NHAC", #Poverty head count ratio at national poverty lines ( % of population )
        "SI.POV.GINI", #Gini Index ( measure of income inequality )             
        ],

    "enviromental_indicators": [
        "EG.FEC.RNEW.ZS", #Renewable energy consumption ( % of total final energy consumption )
        "AG.LND.FRST.ZS", #Forest area ( % of land area )
        ],

    "health_indicators": [
        "SP.DYN.LEOO.IN", #Life expectancy at birht
        "SP.DYN.IMRT.IN", #Infant Mortality rate
        "SH.H20.BASW.ZS", #Access to atleast basic water services ( % of population )
        "SH.XPD.CHEX.GD.ZS", #Current health expenditure ( % of GDP ) 
        "SH.INM.IDPT", #Immunization, DPT ( % of children ages 12-23 months )
        "SH.INM.MEAS", #Immunization, measles ( % of children ages 12-23 months )
        "SH.MMR.RISK.ZS", #Risk of maternal death
        "SH.DTH.COMM.ZS", #Death from communicable diseases ( % of total )
        "SH.TBS.INCD", #Tuberculosis incidence ( per 100,000 people)
        "SH.STA.BRTC.ZS", #Births attended by skilled health staff ( % )
        "SH.STA.MMRT", #Maternal Mortality Ratio ( Modeled estimate, per 100,000 live birth)
        "SH.POP.65UP.TO.ZS", #Population ages 65 and above ( o% of total population ) 
        "SH.HIV.INCD.ZS" #HIV incidence rate ( per 100,000 uninfected population ages 15-49)
        ],

    "technology_indicators": [
        "IT.NET.USER.ZS", #Individual using the internet ( % of population )
        "IT.CEL.SETS.P2", #Mobile cellular subscriptions ( per 100 people )
        ]
}

#base_url = f"https://api.worldbank.org/countries/all/indicators/{}?format=json&per_page=1000&page={}" #Here, "{}" means we will put something later in this place while using it 

base_url = f"https://api.worldbank.org/countries/all/indicators/IT.CEL.SETS.P2?format=json"

response = requests.get(base_url)
print(response.json()[0])
    
base_url = "https://api.worldbank.org/countries/all/indicators/{}?format=json&per_page=1000&page={}"

category_dataframes = {}
   
for category, indicators in indicators_group.items():
    print(f"\nFetching information for category: {category}")
    all_dfs_for_category = []

    for indicator_code in indicators:
        print(f"  Fetching indicator: {indicator_code}")
        page = 1

        while True:
            url = base_url.format(indicator_code, page)
            response = requests.get(url)

            if response.status_code != 200:
                print(f"    No data for indicator {indicator_code} on page {page}")
                break

            data = response.json()
            if len(data) < 2 or not data[1]:
                break

            total_pages = data[0]["pages"]
            record = data[1]

            df = pd.json_normalize(record)

            df = df[
                ["country.id", "country.value", "indicator.id",
                 "indicator.value", "date", "value"]
            ].rename(columns={
                "country.id": "country_id",
                "country.value": "country_value",
                "indicator.id": "indicator_id",
                "indicator.value": "indicator_name",
                "date": "year"
            })
            
            df["year"] = df["year"].astype(int)

            df["year"] = df["year"].astype(int)
            df = df[df["year"] > 2015]

            all_dfs_for_category.append(df)

            if page >= total_pages:
                break

            page += 1
            time.sleep(0.3)

    if all_dfs_for_category:
        combined_df = pd.concat(all_dfs_for_category, ignore_index=True)
        category_dataframes[category] = combined_df
        print(f"Total rows collected for {category}: {len(combined_df)}")
    else:
        print(f"No data collected for {category}")

print("\nData fetching completed")

countries = countries.rename(columns={"iso2Code": "country_id"})

economic_activity = category_dataframes.get("economic_activity_growth", pd.DataFrame())
print(economic_activity)
labour_market_jobs = category_dataframes.get("labour_market_indicators", pd.DataFrame())
poverty_inequality = category_dataframes.get("poverty_inequality", pd.DataFrame())
enviromental_indicators = category_dataframes.get("enviromental_indicators", pd.DataFrame())
health_indicators = category_dataframes.get("health_indicators", pd.DataFrame())
technology_indicators = category_dataframes.get("technology_indicators", pd.DataFrame())

print(category_dataframes.keys())

economic = pd.merge(economic_activity, countries, on="country_id", how="inner")
labour_market = pd.merge(labour_market_jobs, countries, on ="country_id", how="inner")
poverty = pd.merge(poverty_inequality, countries, on ="country_id", how="inner")
environment = pd.merge(enviromental_indicators, countries, on ="country_id", how="inner")
health = pd.merge(health_indicators, countries, on ="country_id", how="inner")
technology = pd.merge(technology_indicators, countries, on ="country_id", how="inner")

economic.drop(columns=["indicator_id", "name", "id"], inplace=True)
labour_market.drop(columns=["indicator_id", "name", "id"], inplace=True)
poverty.drop(columns=["indicator_id", "name", "id"], inplace=True)
environment.drop(columns=["indicator_id", "name", "id"], inplace=True)
health.drop(columns=["indicator_id", "name", "id"], inplace=True)
technology.drop(columns=["indicator_id", "name", "id"], inplace=True)

print(health)

df_wide = health.pivot_table(index = ["country_value", "year"],
    columns ="indicator_name",
    values = "value")
print(df_wide)

