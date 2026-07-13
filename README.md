# Malaysia House Price Estimator

## Project overview

Malaysia House Price Estimator is a planned machine-learning application for estimating residential property prices across Malaysia. It will combine data collection, cleaning, validation, exploratory analysis, feature engineering, regression modelling, model evaluation, and a simple web interface.

The project includes a source-neutral engineering framework and a local area-level real-data prototype. It uses 460 JPPH terraced-house quarterly averages across 46 districts/regions in 14 states/territories, plus 212 richer Penang district/property-type/quarter transaction averages. All selected sources are marked Creative Commons Attribution in Malaysia's government open-data archive.

**Important limitation:** Penang district data covers 2017; other regional coverage is terraced houses only from 2016 Q1 through 2018 Q2. The data contains no individual-property floor area, bedrooms, condition, tenure, project, street, or coordinates. Output is a historical area benchmark, not an individual home valuation or current-market prediction.

Data quality is more important than interface complexity. The first implementation will focus on residential properties for sale and will expand only when sufficient verified, legally usable data is available.

## Problem statement

Residential prices vary greatly within every state and federal territory. A model must not assume that properties throughout Selangor, Johor, Penang, Sabah, or any other region have similar values. State alone is not sufficient for a meaningful prediction.

More detailed location and property information should be used whenever available. District, city, township, development, property type, size, tenure, age, and listing or transaction date may all materially affect price. Official transaction prices and online listing asking prices represent different concepts: an asking price must not automatically be treated as market value. Rental, auction, asking-price, and completed-transaction records must remain clearly labelled and must not be mixed indiscriminately.

## Intended users

Potential users include:

- Homebuyers comparing an asking price with estimated market conditions
- Homeowners seeking general market context
- Students and developers learning applied machine learning
- Property researchers exploring Malaysian housing data

The application will not replace a licensed property valuer, financial adviser, bank valuation, or legal professional.

## Nationwide scope

The intended final product covers all 13 Malaysian states and all 3 federal territories:

- Johor, Kedah, Kelantan, Melaka, Negeri Sembilan, Pahang, Penang, Perak, Perlis, Sabah, Sarawak, Selangor, and Terengganu
- Kuala Lumpur, Putrajaya, and Labuan

Implementation will be incremental and may begin with several regions, selected districts, selected property types, or a small verified dataset. No single state represents the whole MVP or all of Malaysia. Support will depend on legal permission, data availability, data quality, consistent coverage, sufficient local records, and demonstrated model accuracy.

The application must identify locations where data is limited, confidence is low, validation is incomplete, or predictions are unavailable. Nationwide support must not be claimed until actual validated coverage justifies it.

## Planned user inputs

- State or federal territory
- District
- City or township
- Project or development name
- Property type and subtype
- Built-up area and, where relevant, land area
- Bedrooms, bathrooms, and storeys
- Tenure and furnishing
- Property age
- Optional asking price

## Planned outputs

- Central estimated price
- Reasonable estimated price range
- Estimated price per square foot
- Neutral assessment of whether an asking price is below, within, or above the estimated range
- Confidence indicator and local data-coverage information
- Important contributing factors
- Comparable properties when suitable data is available
- Clear coverage and model limitations

A prediction range communicates uncertainty; neither the central estimate nor the range is a guarantee.

## Proposed workflow

```text
Data-source investigation
        ↓
Legal and technical approval
        ↓
Raw data collection
        ↓
Schema validation
        ↓
Cleaning and deduplication
        ↓
Exploratory data analysis
        ↓
Feature engineering
        ↓
Geographic and time-based splitting
        ↓
Baseline models
        ↓
Advanced model comparison
        ↓
Model evaluation by state and district
        ↓
Saved prediction pipeline
        ↓
Streamlit web application
        ↓
Deployment and monitoring
```

Raw, interim, cleaned, and processed data will remain separate. Duplicate properties must be grouped before train/test splitting so copies of one property cannot cause data leakage. Time-based evaluation is preferred because housing markets change over time, and performance must be analysed by state, district, property type, price range, and data coverage.

## Proposed technology stack

Python is the proposed primary language. Likely early tools include Pandas, NumPy, scikit-learn, CSV or Parquet storage, and Jupyter notebooks for exploration only. Requests, BeautifulSoup, Scrapy, or other suitable import tools may be considered only after a source is approved. Official APIs and downloadable datasets are preferred.

CatBoost is a candidate modelling library. Streamlit is the current choice for the first web MVP. SQLite or PostgreSQL may be introduced when structured storage becomes necessary. FastAPI with a custom HTML/CSS/JavaScript frontend and an optional C# WPF client are possible future improvements. Git and GitHub are planned for version control and collaboration.

These are proposed choices, not commitments. Technologies should be adopted only when their phase begins and their need is demonstrated.

## Proposed machine-learning models

- National median-price baseline
- Median price grouped by location and property type
- Linear Regression
- Random Forest Regressor
- Histogram Gradient Boosting when suitable
- CatBoost Regressor
- K-Nearest Neighbours as an optional learning experiment

Simple baselines will be implemented before advanced models, and no final model is preselected. CatBoost may suit a dataset with many categorical features, but it must earn selection through evaluation. K-Nearest Neighbours may be educational, but it needs careful feature scaling, can struggle with categorical data, may become slow on large datasets, and cannot represent geographic similarity through simple numerical distance alone. Deep learning is outside the initial modelling plan.

## Evaluation metrics

- Mean Absolute Error (MAE), reported in Malaysian ringgit
- Median Absolute Error
- Mean Absolute Percentage Error (MAPE), interpreted carefully for low-priced records
- R² as a supporting metric
- Error by state and district
- Error by property type and price range
- Error by data-coverage level

A high R² alone does not prove that a model is useful. Models must use identical evaluation splits, outperform meaningful baselines, avoid leakage, and demonstrate acceptable performance in each supported area. Areas with insufficient evidence must not receive misleading predictions.

## Proposed future project structure

This structure has **not** been created. Folders will be added gradually only when their related implementation begins.

```text
malaysia-house-price-estimator/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── notebooks/
├── src/
│   ├── collection/
│   ├── validation/
│   ├── cleaning/
│   ├── features/
│   ├── modelling/
│   ├── prediction/
│   └── common/
├── models/
├── reports/
├── tests/
├── app/
│   └── streamlit/
├── README.md
├── ROADMAP.md
└── AGENTS.md
```

## Data acquisition principles

No data source or scraper is approved yet. Before collection, each source must be reviewed for terms of service, robots rules, licensing, copyright, privacy, access controls, and technical restrictions. Collection must respect rate limits and must never bypass login systems, CAPTCHAs, paywalls, or anti-bot controls. Secrets and private data must never be committed to Git.

## Limitations

- Listing prices may differ from completed transaction prices.
- Property records may be incomplete, inconsistent, duplicated, or outdated.
- Some states, districts, and especially rural areas may have limited coverage.
- Luxury properties may behave differently from ordinary homes.
- Renovation quality and exact physical condition may be unavailable.
- Location and property-type names may be inconsistent across sources.
- Model performance may deteriorate as market conditions change.
- Comparable properties may be unavailable in low-data areas.
- Predictions are estimates, not official valuations.

## Disclaimer

All outputs are for educational and informational purposes only. They are not financial advice, an official property valuation, or a guaranteed sale price. Outputs must not be the sole basis for purchasing, selling, borrowing, lending, or investment decisions. Users should consult appropriately licensed professionals when making consequential decisions.

## Documentation

- [Project roadmap](ROADMAP.md)
- [Instructions for future Codex tasks](AGENTS.md)
- [Data-source investigation](docs/DATA_SOURCE_INVESTIGATION.md)
- [Canonical data schema](docs/DATA_SCHEMA.md)
- [Cleaning and validation rules](docs/CLEANING_AND_VALIDATION.md)
- [Project progress](docs/PROJECT_PROGRESS.md)
- [Current blockers](docs/BLOCKERS.md)
- [Architecture and local usage](docs/ARCHITECTURE_AND_USAGE.md)
- [Real-data onboarding](docs/REAL_DATA_ONBOARDING.md)
- [Real dataset assessment](docs/REAL_DATASET_ASSESSMENT.md)
- [Streamlit deployment](docs/STREAMLIT_DEPLOYMENT.md)

## Local validation

With Python 3.11 or newer:

```powershell
python -m pip install -e ".[ml,ui,api,charts,dev]"
python -m unittest discover -s tests -v
python scripts/train_official_averages.py
python scripts/train_penang_district.py
python scripts/train_regional_terraced.py
python -m streamlit run app/streamlit_app.py
```

See [Architecture and local usage](docs/ARCHITECTURE_AND_USAGE.md) for CLI and optional API commands. Synthetic fixtures remain only for pipeline tests. The official-average test metrics describe historical aggregates and do not establish individual-home accuracy.

## Public deployment status

Repository: https://github.com/cylim0823/malaysia-house-price-estimator

Live app: https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app

The repository includes the licensed source workbooks, normalized CSV, reproducible training script, and trained historical-average model. GitHub Pages cannot run the Python model.
