# Included Demonstration Model

`demo_bundle.pkl` is a small deterministic synthetic demonstration artifact generated with:

```powershell
python -m house_price_estimator train-demo --output-dir models --count 240 --seed 42
```

- Dataset: synthetic, 240 generated input records
- Selected model: linear ridge regression
- Validation MAE: RM84,717.44 on the synthetic validation split
- SHA-256: `87F93C57AE7D35813204580240EE18E979B6CF78FA116F7DB8E8FE9559063804`

These metrics are not Malaysian property-market accuracy. The bundle exists only so the public Streamlit demonstration can run without external data or credentials. Python pickle files must be loaded only from trusted repository artifacts.

