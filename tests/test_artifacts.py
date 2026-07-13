"""Application artefact selection, compatibility, and report-contract tests."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.artifacts import (
    HISTORICAL_MODEL_METADATA_PATH,
    ModelArtifactError,
    load_active_historical_model,
)


ROOT = Path(__file__).parents[1]


class ApplicationArtifactTests(unittest.TestCase):
    def test_explicit_active_historical_model_matches_manifest(self):
        active = load_active_historical_model()
        self.assertEqual(
            active.path,
            ROOT / "models" / "historical_aggregate" / "model_bundle.pkl",
        )
        self.assertFalse(active.metadata["synthetic"])
        self.assertTrue(active.metadata["active"])
        self.assertEqual(active.bundle.model_version, active.metadata["model_version"])
        self.assertEqual(active.bundle.dataset_version, active.metadata["dataset_version"])

    def _modified_manifest(self, **updates: object) -> tuple[tempfile.TemporaryDirectory, Path]:
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "metadata.json"
        values = json.loads(HISTORICAL_MODEL_METADATA_PATH.read_text(encoding="utf-8"))
        values.update(updates)
        path.write_text(json.dumps(values), encoding="utf-8")
        return directory, path

    def test_synthetic_fixture_is_rejected_in_production_mode(self):
        directory, path = self._modified_manifest(synthetic=True)
        with directory, self.assertRaisesRegex(ModelArtifactError, "non-synthetic"):
            load_active_historical_model(path)

    def test_missing_active_model_has_clear_error(self):
        directory, path = self._modified_manifest(artifact_path="models/missing/model.pkl")
        with directory, self.assertRaisesRegex(ModelArtifactError, "unavailable"):
            load_active_historical_model(path)

    def test_model_and_dataset_version_mismatches_are_rejected(self):
        for field in ("model_version", "dataset_version"):
            directory, path = self._modified_manifest(**{field: "incompatible"})
            with directory, self.assertRaisesRegex(ModelArtifactError, "version"):
                load_active_historical_model(path)

    def test_no_vague_runtime_model_path_or_first_pickle_fallback_remains(self):
        runtime = "\n".join(
            path.read_text(encoding="utf-8")
            for base in (ROOT / "src", ROOT / "app", ROOT / "scripts")
            for path in base.rglob("*.py")
        )
        self.assertNotIn("models/real", runtime.replace("\\", "/"))
        self.assertNotIn("models/demo", runtime.replace("\\", "/"))
        self.assertNotIn("rglob(\"*.pkl\")", runtime)
        self.assertNotIn("glob(\"*.pkl\")", runtime)

    def test_generated_json_reports_identify_data_and_model(self):
        reports = [
            ROOT / "models" / "historical_aggregate" / "evaluation_summary.json",
            *(ROOT / "reports" / "generated").rglob("*.json"),
        ]
        self.assertGreaterEqual(len(reports), 5)
        for path in reports:
            values = json.loads(path.read_text(encoding="utf-8"))
            for field in (
                "dataset_name", "dataset_version", "synthetic",
                "model_version", "generated_at",
            ):
                self.assertIn(field, values, f"{path}: {field}")


if __name__ == "__main__":
    unittest.main()
