"""Reproducible duplicate-group-safe dataset splitting."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import random
from typing import Any

@dataclass(frozen=True)
class SplitResult:
    train:tuple[dict[str,Any],...]; validation:tuple[dict[str,Any],...]; test:tuple[dict[str,Any],...]; report:dict[str,Any]

def split_records(records:list[dict[str,Any]],*,validation_fraction=.2,test_fraction=.2,seed=42,use_time=True)->SplitResult:
    if len(records)<5: raise ValueError("at least five records are required")
    if validation_fraction<=0 or test_fraction<=0 or validation_fraction+test_fraction>=1: raise ValueError("invalid split fractions")
    groups={}
    for record in records: groups.setdefault(str(record.get("duplicate_group_id") or f"unique_{record.get('record_id')}"),[]).append(record)
    grouped=list(groups.values())
    if len(grouped)<3: raise ValueError("at least three independent duplicate groups are required")
    if use_time and all(any(r.get("record_date") for r in group) for group in grouped): grouped.sort(key=lambda g:max(str(r.get("record_date")) for r in g))
    else: random.Random(seed).shuffle(grouped)
    total=len(records); train=[]; validation=[]; test=[]
    for group in grouped:
        if len(train)<total*(1-validation_fraction-test_fraction): train.extend(group)
        elif len(validation)<total*validation_fraction: validation.extend(group)
        else: test.extend(group)
    if not train or not validation or not test: raise ValueError("insufficient independent groups for requested split")
    assigned=[(train,"train"),(validation,"validation"),(test,"test")]
    for rows,name in assigned:
        for r in rows:r["data_split"]=name
    return SplitResult(tuple(train),tuple(validation),tuple(test),{"strategy":"time_group" if use_time else "random_group","seed":seed,"train":len(train),"validation":len(validation),"test":len(test)})

