"""Command-line entry points for local engineering workflows."""
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
from .bundle import PredictionBundle
from .eda import dataset_summary
from .ingestion import ingest_file
from .prediction import PredictionService
from .synthetic_data import SYNTHETIC_LABEL,generate_synthetic_records
from .workflow import prepare,train_synthetic_fixture

def _write_json(path, value):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(value,indent=2,default=str),encoding="utf-8")
def _write_synthetic_records(path: str | Path, records: list[dict]) -> None:
    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        fields = list(records[0])
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(records)
        return
    _write_json(output, {"label": SYNTHETIC_LABEL, "records": records})

def _read_synthetic_records(path: str | Path) -> list[dict]:
    source = Path(path)
    if source.suffix.lower() == ".csv":
        with source.open(encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        payload = json.loads(source.read_text(encoding="utf-8"))
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("synthetic training input must contain a list of records")
    for row in records:
        value = row.get("is_synthetic")
        row["is_synthetic"] = value is True or str(value).strip().lower() == "true"
    return records
def build_parser():
    p=argparse.ArgumentParser(prog="house-price-estimator",description="Local framework for Malaysian residential price estimation")
    sub=p.add_subparsers(dest="command",required=True)
    g=sub.add_parser("generate-synthetic-data");g.add_argument("--output",required=True);g.add_argument("--count",type=int,default=240);g.add_argument("--seed",type=int,default=42);g.add_argument("--price-type",choices=["asking","completed_transaction"],default="asking")
    i=sub.add_parser("import-data");i.add_argument("--input",required=True);i.add_argument("--source-name",required=True);i.add_argument("--dataset-version",required=True);i.add_argument("--summary",required=True)
    c=sub.add_parser("clean");c.add_argument("--input",required=True);c.add_argument("--output",required=True)
    e=sub.add_parser("eda");e.add_argument("--input",required=True);e.add_argument("--output",required=True)
    t=sub.add_parser("train-synthetic-fixture");t.add_argument("--output-dir",required=True);t.add_argument("--input");t.add_argument("--count",type=int,default=240);t.add_argument("--seed",type=int,default=42)
    v=sub.add_parser("evaluate");v.add_argument("--model",required=True)
    pr=sub.add_parser("predict");pr.add_argument("--model",required=True);pr.add_argument("--input",required=True)
    mi=sub.add_parser("model-info");mi.add_argument("--model",required=True)
    return p
def main(argv=None):
    args=build_parser().parse_args(argv)
    try:
        if args.command=="generate-synthetic-data":_write_synthetic_records(args.output,generate_synthetic_records(args.count,seed=args.seed,price_type=args.price_type));print(SYNTHETIC_LABEL)
        elif args.command=="import-data":result=ingest_file(args.input,source_name=args.source_name,dataset_version=args.dataset_version);_write_json(args.summary,result.summary);print(json.dumps(result.summary,indent=2))
        elif args.command in {"clean","eda"}:
            payload=json.loads(Path(args.input).read_text(encoding="utf-8"));records=payload.get("records",payload);cleaned=prepare(records);_write_json(args.output,cleaned if args.command=="clean" else dataset_summary(cleaned));print(args.output)
        elif args.command=="train-synthetic-fixture":bundle,summary,_=train_synthetic_fixture(count=args.count,seed=args.seed,output_dir=args.output_dir,records=_read_synthetic_records(args.input) if args.input else None);print(SYNTHETIC_LABEL);print(json.dumps(summary,indent=2))
        elif args.command=="evaluate":bundle=PredictionBundle.load(args.model,trusted=True);print(json.dumps(bundle.validation_metrics,indent=2))
        elif args.command=="predict":bundle=PredictionBundle.load(args.model,trusted=True);values=json.loads(Path(args.input).read_text(encoding="utf-8"));print(json.dumps(PredictionService(bundle).predict(values).to_dict(),indent=2))
        elif args.command=="model-info":bundle=PredictionBundle.load(args.model,trusted=True);print(json.dumps({k:v for k,v in vars(bundle).items() if k!="model"},indent=2,default=str))
        return 0
    except Exception as exc:print(f"error: {exc}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
