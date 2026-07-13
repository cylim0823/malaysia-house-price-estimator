import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.bundle import PredictionBundle
from house_price_estimator.cli import main
from house_price_estimator.duplicates import group_duplicates, similarity
from house_price_estimator.eda import dataset_summary
from house_price_estimator.evaluation import evaluate_records, regression_metrics
from house_price_estimator.features import FeatureEncoder, FORBIDDEN_FEATURES
from house_price_estimator.ingestion import ingest_file
from house_price_estimator.modelling import MedianRegressor, optional_sklearn_models
from house_price_estimator.outliers import detect_outliers
from house_price_estimator.prediction import PredictionService
from house_price_estimator.schema import PriceType, RawRecord, State
from house_price_estimator.splitting import split_records
from house_price_estimator.synthetic_data import SYNTHETIC_LABEL, generate_synthetic_records
from house_price_estimator.workflow import prepare, train_synthetic_fixture
from house_price_estimator.config import ProjectConfig


class SchemaAndIngestionTests(unittest.TestCase):
    def test_invalid_enum_rejected(self):
        with self.assertRaises(ValueError): PriceType("sale-ish")
        self.assertEqual(State("Kuala Lumpur"), State.KUALA_LUMPUR)

    def test_csv_ingestion_retains_rejected_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"fixture.csv"
            path.write_text("record_id,price,price_type,state,property_type\n1,500000,asking,Selangor,Condominium\n2,,asking,Johor,Apartment\n",encoding="utf-8")
            result=ingest_file(path,source_name="synthetic_fixture",dataset_version="test-v1")
            self.assertEqual(len(result.records),1);self.assertEqual(len(result.rejected_rows),1)
            self.assertEqual(result.records[0].schema_version,"1.0.0")

    def test_json_and_jsonl_ingestion(self):
        row={"record_id":"1","price":1,"price_type":"asking","state":"Perak","property_type":"Flat","is_synthetic":True}
        with tempfile.TemporaryDirectory() as directory:
            for suffix,text in ((".json",json.dumps([row])),(".jsonl",json.dumps(row)+"\n")):
                path=Path(directory)/("input"+suffix);path.write_text(text,encoding="utf-8")
                self.assertEqual(len(ingest_file(path,source_name="test",dataset_version="v1").records),1)

    def test_parquet_ingestion_when_available(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.parquet";pd.DataFrame([{"record_id":"1","price":2,"price_type":"asking","state":"Johor","property_type":"Flat"}]).to_parquet(path)
            self.assertEqual(len(ingest_file(path,source_name="test",dataset_version="v1").records),1)

    def test_configuration_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"config.json";path.write_text(json.dumps(ProjectConfig().to_dict()),encoding="utf-8")
            self.assertEqual(ProjectConfig.load(path).random_seed,42)


class DataFrameworkTests(unittest.TestCase):
    def setUp(self): self.rows=prepare(generate_synthetic_records(96,seed=7,include_anomalies=False))

    def test_generator_is_reproducible_and_labelled(self):
        a=generate_synthetic_records(5,seed=1);b=generate_synthetic_records(5,seed=1)
        self.assertEqual(a,b);self.assertTrue(all(r["is_synthetic"] for r in a));self.assertEqual(a[0]["synthetic_disclaimer"],SYNTHETIC_LABEL)

    def test_near_duplicate_grouping_retains_rows(self):
        records=generate_synthetic_records(12,include_anomalies=True);prepared=prepare(records)
        self.assertEqual(len(prepared),11)  # invalid price retained by generator but rejected during preparation
        self.assertTrue(any(r["duplicate_status"]!="unique" for r in prepared))

    def test_outliers_flag_without_deleting(self):
        records=[{"record_id":"x","price":0,"built_up_sqft":1000,"state":"Johor","property_type":"Flat"}]
        result=detect_outliers(records);self.assertEqual(len(result),1);self.assertEqual(result[0]["outlier_status"],"confirmed_data_error")

    def test_luxury_outlier_is_retained_for_review(self):
        records=[{"record_id":str(i),"price":v,"built_up_sqft":5000,"state":"Selangor","property_type":"Bungalow"} for i,v in enumerate([1_000_000,1_100_000,1_200_000,20_000_000])]
        result=detect_outliers(records);self.assertEqual(len(result),4);self.assertEqual(result[-1]["outlier_status"],"possible_outlier");self.assertEqual(result[-1]["outlier_suggested_action"],"manual_review")

    def test_eda_empty_and_synthetic(self):
        self.assertEqual(dataset_summary([])["record_count"],0)
        self.assertEqual(dataset_summary(self.rows)["label"],SYNTHETIC_LABEL)

    def test_group_safe_reproducible_split(self):
        first=split_records([dict(r) for r in self.rows],seed=4);second=split_records([dict(r) for r in self.rows],seed=4)
        self.assertEqual([r["record_id"] for r in first.test],[r["record_id"] for r in second.test])
        sets=[{r["duplicate_group_id"] for r in part} for part in (first.train,first.validation,first.test)]
        self.assertFalse(sets[0]&sets[1]);self.assertFalse(sets[0]&sets[2]);self.assertFalse(sets[1]&sets[2])
        self.assertLessEqual(max(r["record_date"] for r in first.train),min(r["record_date"] for r in first.test))

    def test_feature_unknown_category_and_no_leakage(self):
        encoder=FeatureEncoder().fit(self.rows[:50]);modified=dict(self.rows[51],district="Never Seen")
        self.assertEqual(encoder.transform([modified]).shape[1],len(encoder.feature_names()))
        self.assertTrue(FORBIDDEN_FEATURES.isdisjoint(encoder.feature_names()))

    def test_median_model_uses_training_values(self):
        model=MedianRegressor(("state",)).fit(self.rows[:50]);self.assertEqual(len(model.predict(self.rows[50:55])),5)

    def test_optional_advanced_models_share_record_interface(self):
        models=optional_sklearn_models(seed=3);self.assertIn("random_forest",models)
        model=models["hist_gradient_boosting"].fit(self.rows[:50]);self.assertEqual(len(model.predict(self.rows[50:55])),5)

    def test_metrics_and_minimum_slice(self):
        metrics=regression_metrics([1,2,3],[1,2,4]);self.assertAlmostEqual(metrics["mae"],1/3)
        report=evaluate_records(self.rows[:20],[r["price"] for r in self.rows[:20]],minimum_segment_size=100)
        self.assertEqual(report["slices"]["state"],{})


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.bundle,cls.summary,cls.split=train_synthetic_fixture(count=192,seed=12)

    def test_save_load_predict_and_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"bundle.pkl";self.bundle.save(path)
            with self.assertRaises(ValueError):PredictionBundle.load(path)
            loaded=PredictionBundle.load(path,trusted=True);sample=dict(self.split.train[0]);result=PredictionService(loaded).predict(sample)
            self.assertGreater(result.estimate,0);self.assertLessEqual(result.lower,result.upper);self.assertEqual(result.synthetic_disclaimer,SYNTHETIC_LABEL)
            bad=dict(sample,state="Atlantis")
            with self.assertRaises(ValueError):PredictionService(loaded).predict(bad)

    def test_asking_price_assessment_is_neutral(self):
        sample=dict(self.split.train[0],asking_price=1)
        result=PredictionService(self.bundle).predict(sample)
        self.assertIn(result.asking_price_assessment,{"Below estimated range","Within estimated range","Above estimated range"})

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            data=Path(directory)/"demo.csv";out=Path(directory)/"artifacts";prediction_input=Path(directory)/"prediction.json"
            self.assertEqual(main(["generate-synthetic-data","--output",str(data),"--count","20"]),0)
            self.assertIn("synthetic_disclaimer",data.read_text(encoding="utf-8"))
            self.assertEqual(main(["train-synthetic-fixture","--output-dir",str(out),"--input",str(data)]),0)
            created=PredictionBundle.load(out/"model_bundle.pkl",trusted=True);state,district,kind=next(iter(created.segment_counts)).split("|",2)
            sample={"state":state,"district":district,"property_type":kind,"built_up_sqft":1000,"bedrooms":3,"bathrooms":2,"record_year":2026,"record_month":7}
            prediction_input.write_text(json.dumps(sample),encoding="utf-8")
            self.assertEqual(main(["predict","--model",str(out/"model_bundle.pkl"),"--input",str(prediction_input)]),0)
            self.assertTrue((out/"evaluation"/"metrics.json").is_file())
            self.assertTrue((out/"evaluation"/"actual_vs_predicted.png").is_file())

    def test_optional_api_health_import(self):
        from house_price_estimator.api import DEFAULT_MODEL_PATH,app,health
        self.assertEqual(health(),{"status":"ok"})
        self.assertEqual(app.title,"Malaysia House Price Estimator")
        self.assertIsNone(DEFAULT_MODEL_PATH)

    def test_repository_artifact_layout_and_integrity(self):
        root=Path(__file__).parents[1]
        expected={
            "data/external/napic/all_houses_by_state.xlsx":"4f492c97174ef4d437b9785ede7b290a9020fe55d51292c0a3b3aede69e1f371",
            "data/external/penang/residential_transaction_counts_2017.csv":"be4dcbe8d39e6e9d2b1f49b4023765033fe81036bb52e14d01172f289f22a05f",
            "tests/fixtures/synthetic/model_bundle.pkl":"e67df7fd53da6fd42199e9130457d0a6de6cccefc8e08c6c18fa01e6831c1739",
            "models/historical_aggregate/model_bundle.pkl":"b4d6e8a8c915aa8ace3488b6148a48dc2edce4c76d3fcf9acb3095e2899a591f",
            "models/individual_property/model_bundle.pkl":"6496b54e15941ef468c086743bb9def9021acf55279322a748d04b735028d4ba",
        }
        for relative,checksum in expected.items():
            path=root/relative
            self.assertTrue(path.is_file(),relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),checksum)
        self.assertFalse((root/"data"/"official").exists())
        self.assertFalse((root/"malaysia-house-price-estimator").exists())

    def test_streamlit_app_smoke(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [item.label for item in app.tabs],
            ["Historical Market Explorer", "Individual Property Estimator"],
        )
        self.assertTrue(
            any("does not estimate the exact value" in item.value for item in app.warning)
        )
        self.assertFalse(any("quarter" in item.label.lower() for item in app.selectbox))
        next(item for item in app.button if item.label == "Show historical benchmark").click().run()
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.metric), 2)
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertTrue(any(item.value == "Historical market benchmark" for item in app.subheader))
        self.assertIn("**Available data period:**", rendered)
        self.assertIn("**Dataset version:**", rendered)
        self.assertIn("**Data age:**", rendered)

    def test_streamlit_dynamic_multistate_year_path(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        next(item for item in app.selectbox if item.key == "history-state").select("Selangor").run()
        history = [item for item in app.selectbox if item.key and item.key.startswith("history-")]
        self.assertEqual(
            [item.label for item in history[:4]],
            ["State or federal territory", "Year", "District or area", "Property type"],
        )
        self.assertTrue(any(item.key.startswith("history-district-") for item in app.selectbox))
        year = next(item for item in app.selectbox if item.key.startswith("history-year-"))
        self.assertEqual(year.options, ["2026", "2025", "2024", "2023", "2022", "2021"])
        self.assertEqual(year.value, 2026)
        labels = next(item for item in app.selectbox if item.key.startswith("history-type-")).options
        self.assertIn("Condominium / apartment", labels)
        self.assertFalse(any("Storey" in label for label in labels))
        next(item for item in app.button if item.label == "Show historical benchmark").click().run()
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.metric), 2)

    def test_streamlit_penang_newest_year_and_year_change_reset(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        next(item for item in app.selectbox if item.key == "history-state").select("Penang").run()
        year = next(item for item in app.selectbox if item.key.startswith("history-year-"))
        self.assertEqual(year.value, 2026)
        self.assertEqual(year.options, ["2026", "2025", "2024", "2023", "2022", "2021", "2017"])
        self.assertTrue(any(item.key.startswith("history-district-") for item in app.selectbox))

        next(item for item in app.selectbox if item.key == "history-state").select("Sabah").run()
        next(item for item in app.selectbox if item.key.startswith("history-year-")).select(2022).run()
        next(item for item in app.selectbox if item.key.startswith("history-district-")).select("Kota Marudu").run()
        next(item for item in app.selectbox if item.key.startswith("history-year-")).select(2026).run()
        district = next(item for item in app.selectbox if item.key.startswith("history-district-"))
        self.assertNotEqual(district.value, "Kota Marudu")
        self.assertNotIn("Kota Marudu", district.options)
        self.assertFalse(app.exception)

    def test_streamlit_same_history_path_covers_east_malaysia_and_federal_territory(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        for state in ("Sarawak", "Kuala Lumpur"):
            next(item for item in app.selectbox if item.key == "history-state").select(state).run()
            self.assertEqual(
                next(item for item in app.selectbox if item.key.startswith("history-year-")).value,
                2026,
            )
            next(item for item in app.button if item.label == "Show historical benchmark").click().run()
            self.assertFalse(app.exception)
        self.assertFalse(
            any(item.key and item.key.startswith("history-district-") for item in app.selectbox)
        )
        self.assertTrue(any(item.value == "Coverage: State-level" for item in app.caption))

    def test_streamlit_build_identifier_and_no_legacy_penang_runtime_text(self):
        from streamlit.testing.v1 import AppTest
        root=Path(__file__).parents[1]
        app=AppTest.from_file(str(root/"app"/"streamlit_app.py"),default_timeout=10).run()
        rendered="\n".join(
            str(item.value)
            for collection in (app.markdown, app.caption, app.subheader, app.button)
            for item in collection
        )
        self.assertNotIn("Show Penang", rendered)
        self.assertNotIn("2017 quarter", rendered)
        self.assertNotIn("Penang district result", rendered)
        self.assertTrue(any("generic-history-2026.07.13.1" in item.value for item in app.markdown))
        self.assertFalse((root/"src"/"house_price_estimator"/"penang_district.py").exists())
        self.assertFalse((root/"tests"/"test_penang_district.py").exists())

    def test_streamlit_individual_form_is_visible_and_accepts_blank_optionals(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("official NAPIC/JPPH" in item.value for item in app.success))
        labels = {
            item.label
            for collection in (app.selectbox, app.text_input, app.checkbox)
            for item in collection
        }
        expected = {
            "District", "City or township", "Development or project name",
            "Property type", "Property subtype", "Tenure", "Furnishing",
            "Renovation status", "Property condition",
            "I know the built-up area (sq ft)", "I know the bedrooms",
            "I know the additional/helper bedrooms", "I know the bathrooms",
            "I know the car parks", "I know the completion year",
            "I know the property age (years)", "I know the asking price (rm)",
        }
        self.assertTrue(expected.issubset(labels), expected - labels)
        next(item for item in app.selectbox if item.key == "property-state").select("Penang").run()
        next(item for item in app.selectbox if item.key == "property-district").select("Timur Laut").run()
        next(item for item in app.selectbox if item.key == "property-type").select("Condominium/Apartment").run()
        self.assertTrue(any("Land area: Not applicable" in item.value for item in app.info))
        self.assertTrue(any("Storeys: Not applicable" in item.value for item in app.info))
        next(item for item in app.button if item.label == "Estimate completed transaction price").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(item.label == "Estimated completed transaction price" for item in app.metric))
        self.assertTrue(any("Missing optional information" in item.value for item in app.markdown))

    def test_streamlit_landed_form_marks_floor_level_not_applicable(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).parents[1]/"app"/"streamlit_app.py"),default_timeout=10).run()
        next(item for item in app.selectbox if item.key == "property-state").select("Johor").run()
        next(item for item in app.selectbox if item.key == "property-district").select("Johor Bahru").run()
        next(item for item in app.selectbox if item.key == "property-type").select("2 - 2 1/2 Storey Terraced").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Floor level: Not applicable" in item.value for item in app.info))
        self.assertTrue(any(item.label == "I know the land area (sq ft)" for item in app.checkbox))
        self.assertTrue(any(item.label == "I know the storeys" for item in app.checkbox))


if __name__=="__main__":unittest.main()
