# World Bank API Data Pipeline & Analytics Dashboard

An end-to-end data pipeline and interactive analytics dashboard built to answer one question:

> **Is there a measurable relationship between digital adoption and economic development across countries? Do nations with higher internet and mobile penetration tend to have stronger GDP growth and better health outcomes?**

The project extracts 25+ development indicators from the World Bank REST API across 526 paginated pages, cleans and transforms nested JSON into structured datasets using Python, and visualizes global development patterns through an interactive Power BI dashboard with geographic and regional filtering.

---

## Dashboard Preview

![World Indicators Analysis Dashboard](dashboard_preview.jpg)

**Key numbers visible on dashboard:**
- Average GDP per Capita: **$17.97K**
- Average Health Spending: **6.69% of GDP**
- Average GDP Growth: **2.68%**
- North America health spend (14.0%) vs South Asia (4.6%) — 3x regional disparity

---

## Research Question & Finding

**Question:** Do countries with higher internet and mobile adoption tend to have higher GDP per capita and better health outcomes?

**Finding:** The dashboard shows a positive directional relationship — countries and regions with higher internet penetration cluster toward higher GDP per capita and higher health expenditure. North America (highest internet adoption) shows the highest health spending at 14% of GDP. Sub-Saharan Africa (lowest internet adoption) shows the lowest at 5.4%.

**Important caveat:** This is correlation, not causation. Wealthier countries can afford both better digital infrastructure and better healthcare simultaneously — digital adoption may be a symptom of development rather than a cause. The project establishes the visual and descriptive relationship, not the causal one.

---

## Data Pipeline Architecture

```
World Bank REST API
        │
        │  requests + time.sleep(0.3)  ← rate limiting
        │
Stage 1: Country Metadata Extraction
  └── Fetch all countries → flatten nested JSON (region, incomeLevel, lendingType)
  └── Drop adminregion, capitalCity → clean countries DataFrame
        │
Stage 2: Indicator Data Extraction (per domain, per indicator, per page)
  └── Paginated while loop → check total_pages from data[0] → fetch until exhausted
  └── pd.json_normalize → flatten nested country/indicator fields
  └── Filter: year > 2015 → keep post-2015 observations only
  └── Rename columns → country_id, country_value, indicator_name, year, value
        │
Stage 3: Merge & Enrich
  └── pd.merge(indicator_df, countries, on="country_id", how="inner")
  └── Inner join auto-excludes World Bank aggregate entries (World, High Income etc.)
        │
Stage 4: Export to CSV → Load into Power BI
```

---

## 25 Indicators Across 6 Domains

Organized as a Python dictionary — adding a new indicator requires one line, no pipeline logic changes:

```python
indicators_group = {
    "economic_activity_growth": [
        "NY.GDP.MKTP.KD.ZG",   # GDP Growth (annual %)
        "NY.GDP.PCAP.CD",       # GDP per Capita (current US$)
    ],
    "labour_market_indicators": [
        "SL.UEM.TOTL.ZS",       # Unemployment, total (%)
        "SL.UEM.1524.ZS",       # Youth unemployment, ages 15-24 (%)
        "SL.TLF.TOTL.IN",       # Labour Force, Total
    ],
    "poverty_inequality": [
        "SI.POV.NHAC",           # Poverty headcount at national poverty lines (%)
        "SI.POV.GINI",           # Gini Index (income inequality)
    ],
    "enviromental_indicators": [
        "EG.FEC.RNEW.ZS",        # Renewable energy consumption (% of total)
        "AG.LND.FRST.ZS",        # Forest area (% of land area)
    ],
    "health_indicators": [
        "SP.DYN.LEOO.IN",        # Life expectancy at birth
        "SP.DYN.IMRT.IN",        # Infant mortality rate
        "SH.H20.BASW.ZS",        # Access to basic water services (%)
        "SH.XPD.CHEX.GD.ZS",    # Health expenditure (% of GDP)
        "SH.INM.IDPT",           # DPT immunization (% of children 12-23 months)
        "SH.INM.MEAS",           # Measles immunization (%)
        "SH.MMR.RISK.ZS",        # Risk of maternal death
        "SH.DTH.COMM.ZS",        # Deaths from communicable diseases (% of total)
        "SH.TBS.INCD",           # Tuberculosis incidence (per 100,000)
        "SH.STA.BRTC.ZS",        # Births attended by skilled health staff (%)
        "SH.STA.MMRT",           # Maternal mortality ratio
        "SH.POP.65UP.TO.ZS",     # Population 65+ (% of total)
        "SH.HIV.INCD.ZS",        # HIV incidence rate
    ],
    "technology_indicators": [
        "IT.NET.USER.ZS",         # Internet users (% of population)
        "IT.CEL.SETS.P2",         # Mobile cellular subscriptions (per 100 people)
    ]
}
```

---

## Key Technical Implementations

### 1. Paginated While Loop
The World Bank API returns 500 records per page. Total indicator catalog spans 526 pages (29,323 indicators). The loop reads total_pages from API metadata and runs until exhausted:

```python
page = 1
while True:
    url = base_url.format(indicator_code, page)
    response = requests.get(url)
    data = response.json()

    total_pages = data[0]["pages"]  # API tells you how many pages exist
    record = data[1]                # actual data for this page

    df = pd.json_normalize(record)
    all_dfs_for_category.append(df)

    if page >= total_pages:
        break   # stop when last page reached

    page += 1
    time.sleep(0.3)  # rate limiting — 3 requests/second max
```

### 2. Nested JSON Flattening
World Bank API returns nested objects — country and indicator are dictionaries inside dictionaries. pd.json_normalize flattens them into dot-notation columns:

**Raw API response:**
```json
{
    "country": {"id": "IN", "value": "India"},
    "indicator": {"id": "IT.NET.USER.ZS", "value": "Internet users"},
    "date": "2022",
    "value": 52.4
}
```

**After pd.json_normalize:**
```
country.id | country.value | indicator.id   | indicator.value | date | value
IN         | India         | IT.NET.USER.ZS | Internet users  | 2022 | 52.4
```

**Column selection and renaming:**
```python
df = pd.json_normalize(record)
df = df[
    ["country.id", "country.value", "indicator.id", "indicator.value", "date", "value"]
].rename(columns={
    "country.id": "country_id",
    "country.value": "country_value",
    "indicator.id": "indicator_id",
    "indicator.value": "indicator_name",
    "date": "year"
})
df["year"] = df["year"].astype(int)
df = df[df["year"] > 2015]  # post-2015 filter
```

**Country metadata — different nesting structure handled with lambda:**
```python
countries["region"] = countries["region"].apply(lambda x: x["value"])
countries["incomeLevel"] = countries["incomeLevel"].apply(lambda x: x["value"])
countries["lendingType"] = countries["lendingType"].apply(lambda x: x["value"])
```

### 3. Inner Join for Automatic Aggregate Filtering
World Bank includes aggregate entries (World, High Income, Sub-Saharan Africa region codes) in indicator data. These don't exist in the countries metadata. Inner join automatically excludes them — no explicit filter needed:

```python
technology = pd.merge(
    technology_indicators,
    countries,
    on="country_id",
    how="inner"   # only keeps rows where country_id exists in BOTH DataFrames
)
```

### 4. RUN_API Flag — Fetch Once, Cache Locally
Prevents re-hitting the API on every script run — standard production pipeline practice:

```python
RUN_API = False  # set True only when fresh data is needed

if RUN_API:
    # run full 526-page pipeline → save to CSV
    final_df.to_csv("final_df.csv", index=False)
else:
    final_df = pd.read_csv("final_df.csv")  # load from cache
```

---

## Power BI Dashboard

### Data Model
```
Fact Tables (one per domain):
  economic_activity → country_id, indicator_name, year, value, region, incomeLevel
  labour_market     → same structure
  poverty           → same structure
  environment       → same structure
  health            → same structure
  technology        → same structure

Dimension Table:
  countries → country_id, country_value, region, incomeLevel, lendingType
```

Relationships established between all fact tables and the countries dimension table on country_id — enabling cross-domain filtering by region and income level.

### DAX Measures

```dax
// Average GDP per Capita
Avg GDP per Capita = AVERAGE(economic_activity[value])

// Average GDP Growth
Avg GDP Growth = 
CALCULATE(
    AVERAGE(economic_activity[value]),
    economic_activity[indicator_name] = "GDP growth (annual %)"
)

// Average Health Expenditure
Avg Health Spend = 
CALCULATE(
    AVERAGE(health[value]),
    health[indicator_name] = "Current health expenditure (% of GDP)"
)
```

### Dashboard Visuals

**1. KPI Cards (3 headline metrics):**

| KPI | Global Value | What it measures |
|-----|-------------|-----------------|
| Average GDP per Capita | $17.97K | Average standard of living |
| Average Health Spending | 6.69% of GDP | Healthcare investment as share of economy |
| Average GDP Growth | 2.68% | Economic expansion rate |

**2. Multi-indicator Trend Chart (2020–2025):**
Line chart tracking 6 indicators simultaneously over time — Forest area, GDP growth, Internet users, Mobile subscriptions, Renewable energy, Unemployment. 2020-2025 window captures COVID-19 impact, recovery trajectory, and digital adoption acceleration during remote work expansion.

**3. Regional Health Expenditure Bar Chart:**

| Region | Health Spend (% GDP) |
|--------|---------------------|
| North America | 14.0% |
| Europe & Central Asia | 8.0% |
| East Asia & Pacific | 7.1% |
| Latin America & Caribbean | 6.8% |
| Aggregates | 6.4% |
| Middle East & North Africa | 6.1% |
| Sub-Saharan Africa | 5.4% |
| South Asia | 4.6% |

**4. World Map — GDP Growth vs Internet Penetration:**
Country-level map plotting both GDP growth and internet users % simultaneously. Geographic clustering makes the correlation pattern immediately visible — high internet penetration countries cluster toward stronger economic performance. Power BI's Bing Maps integration handles geocoding from country names automatically.

**5. Region Slicer:**
Filters all 4 visuals simultaneously by World Bank geographic region — North America, Europe & Central Asia, East Asia & Pacific, South Asia, Sub-Saharan Africa, Latin America & Caribbean, Middle East & North Africa.

---

## Key Findings

- **North America vs South Asia health gap:** 14.0% vs 4.6% of GDP — a 3x disparity in healthcare investment
- **Internet adoption trend:** Consistent upward trajectory 2020-2025 — accelerated by remote work and digital payments
- **GDP growth volatility:** COVID-19 visible as 2020 dip across most regions with recovery 2021-2023
- **Directional answer to research question:** Regions with higher internet penetration cluster toward higher GDP per capita — positive correlation observed but causation not established

---

## Why Post-2015 Filter

Three reasons:
1. **SDG baseline** — UN Sustainable Development Goals adopted September 2015 — post-2015 is the measurement era for these targets
2. **Data completeness** — older data has significantly more missing values for developing countries
3. **Relevance** — recent trends (remote work, renewable energy, post-COVID recovery) are more actionable than historical patterns

---

## Project Structure

```
world-bank-api-powerbi-analytics-dashboard/
│
├── project3.py                  # Full data pipeline — API extraction, cleaning, merging
├── World_Bank_Dashboard.pbix    # Power BI dashboard file
├── data/
│   └── final_df.csv             # Cached indicator catalog (29,323 rows)
├── images/
│   └── dashboard_preview.png    # Dashboard screenshot
└── README.md
```

---

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/kanishknarwani/world-bank-api-powerbi-analytics-dashboard.git
cd world-bank-api-powerbi-analytics-dashboard

# Install Python dependencies
pip install pandas numpy requests

# Run the pipeline (set RUN_API = True in project3.py for fresh data fetch)
# Leave RUN_API = False to load from cached final_df.csv
python project3.py

# Open dashboard
# Open World_Bank_Dashboard.pbix in Power BI Desktop
# Refresh data connections if needed
# Use region slicer to filter all visuals
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Data pipeline — API calls, cleaning, transformation |
| requests | HTTP requests to World Bank REST API |
| Pandas | DataFrame operations, pd.json_normalize, pd.merge |
| NumPy | Numerical operations |
| time | Rate limiting (time.sleep) between API requests |
| Power BI | Interactive dashboard and data visualization |
| DAX | Calculated measures for KPI cards and aggregations |

---

## Limitations

- Dataset covers post-2015 only — long-term historical trends not captured
- World Bank data has reporting lag — most recent year may be 1-2 years behind current
- Correlation observed between digital adoption and GDP — causation not established without regression with control variables
- Some developing countries have missing values for specific indicators — gaps in coverage for health and poverty metrics

---

## Author

**Kanishk Narwani**
B.Com | Masters in Applied Statistics and Informatics
Gokhale Institute of Politics and Economics, Pune

[GitHub](https://github.com/kanishknarwani) | [LinkedIn](https://linkedin.com/in/kanishk-narwani)
