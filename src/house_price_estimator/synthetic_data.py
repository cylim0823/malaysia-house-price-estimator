"""Deterministic fictional data for tests and local demonstrations only."""

from __future__ import annotations

from datetime import date, timedelta
import random
from typing import Any

from .schema import State

SYNTHETIC_LABEL = "Synthetic demonstration data - not real Malaysian property market data."


def generate_synthetic_records(count: int = 240, *, seed: int = 42, price_type: str = "asking",
                               include_anomalies: bool = True) -> list[dict[str, Any]]:
    if count < 1: raise ValueError("count must be positive")
    if price_type not in {"asking", "completed_transaction"}: raise ValueError("synthetic generator supports separate sale-price datasets only")
    rng=random.Random(seed); states=[state.value for state in State]; types=["Condominium","Apartment","Terraced House","Semi-Detached House","Bungalow"]
    records=[]
    for index in range(count):
        state=states[index%len(states)]; kind=rng.choice(types); high=kind in {"Condominium","Apartment"}
        built=max(350, round(rng.gauss(950 if high else 1800,300))); land=None if high else max(700,round(rng.gauss(2200,600)))
        bedrooms=max(1,min(7,round(built/500+rng.uniform(-1,1)))); bathrooms=max(1,bedrooms-1)
        age=rng.randint(0,40); year=2018+(index//len(states))%8; state_factor=1+(states.index(state)%8)*.06
        type_factor={"Apartment":.8,"Condominium":1,"Terraced House":1.1,"Semi-Detached House":1.35,"Bungalow":1.7}[kind]
        price=(90000+built*260+(land or 0)*55+bedrooms*18000-age*2500)*(state_factor*type_factor)*rng.uniform(.9,1.1)
        if price_type=="asking": price*=1.06
        records.append({"record_id":f"syn-{price_type[:3]}-{index:05d}","source_name":"synthetic_generator","price":round(max(price,50000),2),
                        "price_type":price_type,"state":state,"district":f"Fictional Segment {index%4+1}","city":f"Demo City {index%6+1}",
                        "project_name":f"Synthetic Residence {index%20+1}","property_type":kind,"property_subtype":None,
                        "built_up_area":built,"built_up_unit":"sqft","land_area":land,"land_area_unit":"sqft" if land else None,
                        "bedrooms":str(bedrooms),"bathrooms":str(bathrooms),"storeys":rng.choice([1,2,3]),"tenure":rng.choice(["Freehold","Leasehold"]),
                        "furnishing":rng.choice(["Unfurnished","Partly Furnished","Fully Furnished"]),"property_age_years":age,
                        "record_date":(date(year,1,1)+timedelta(days=rng.randrange(365))).isoformat(),"is_synthetic":True,"synthetic_disclaimer":SYNTHETIC_LABEL})
    if include_anomalies and count >= 12:
        duplicate=dict(records[2]); duplicate["record_id"]="syn-duplicate-00001"; duplicate["price"]=round(float(duplicate["price"])*1.01,2); records[-1]=duplicate
        records[-2]["price"]="Contact for price"; records[-3]["built_up_area"]="0.1 hectare"; records[-4]["furnishing"]="Unknown"
    return records
