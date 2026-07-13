# Included Models

## Penang district transaction model

`penang_district_bundle.pkl` is trained reproducibly with:

```powershell
python scripts/train_penang_district.py
```

- Source: Penang government transaction counts and values, Creative Commons Attribution
- Observations: 212 district/property-type/quarter completed-transaction averages
- Coverage: five Penang districts, 11 residential types, 2017 Q1-Q4
- Training: Q1-Q3; final test: Q4 (54 observations)
- Selected model: district/property-type median baseline
- Test MAE: RM55,154.82
- Log-target ridge comparison MAE: RM79,520.97
- SHA-256: `162074FE474103D331004DE47EEE1ADB372F0C1A2C473AC2BC55EA506597E0BC`

The simple baseline was selected because it outperformed ridge regression on the untouched quarter.

## Official historical-average model

`official_average_bundle.pkl` is trained reproducibly with:

```powershell
python scripts/train_official_averages.py
```

- Source: JPPH/NAPIC government open-data workbooks, Creative Commons Attribution
- Observations: 2,090 quarterly state/property-type averages
- Coverage: 2009 Q1 through 2018 Q2
- Final holdout: 2018 Q1-Q2, 110 observations
- Test MAE: RM94,268.28
- Test RMSE: RM276,407.99
- Test R²: 0.7670
- State/property-type median baseline MAE: RM101,457.44
- SHA-256: `3ABBFC906FF546AE3364F24695D6A203043C85D0836CA20A9FF247F6EA1522B3`

These metrics describe aggregated historical averages, not individual-property accuracy.

## Synthetic engineering model

`demo_bundle.pkl` is a small deterministic synthetic demonstration artifact generated with:

```powershell
python -m house_price_estimator train-demo --output-dir models --count 240 --seed 42
```

- Dataset: synthetic, 240 generated input records
- Selected model: linear ridge regression
- Validation MAE: RM84,717.44 on the synthetic validation split
- SHA-256: `E67DF7FD53DA6FD42199E9130457D0A6DE6CCCEFC8E08C6C18FA01E6831C1739`

These metrics are not Malaysian property-market accuracy. The bundle exists only so the public Streamlit demonstration can run without external data or credentials. Python pickle files must be loaded only from trusted repository artifacts.
