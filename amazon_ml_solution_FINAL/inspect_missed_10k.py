import csv

base = r".\dataset\train_10k"
missed_file = r".\output\missed_matches_10k.tsv"

wanted_s1 = set()
wanted_s2 = set()
wanted_s3 = set()

with open(missed_file, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        wanted_s1.add(r["s1_entity_id"])
        if r["source"] == "S2":
            wanted_s2.add(r["matched_entity_id"])
        else:
            wanted_s3.add(r["matched_entity_id"])

def load_records(path, wanted):
    found = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r["entity_id"] in wanted:
                found[r["entity_id"]] = r
                if len(found) == len(wanted):
                    break
    return found

print("Loading missed S1 records...")
s1 = load_records(base + r"\train_source1.tsv", wanted_s1)

print("Loading missed S2 records...")
s2 = load_records(base + r"\train_source2.tsv", wanted_s2)

print("Loading missed S3 records...")
s3 = load_records(base + r"\train_source3.tsv", wanted_s3)

print("\n" + "="*100)
print("MISSED MATCH DETAILS")
print("="*100)

with open(missed_file, encoding="utf-8") as f:
    for r in list(csv.DictReader(f, delimiter="\t"))[:30]:
        a = s1.get(r["s1_entity_id"], {})
        b = s2.get(r["matched_entity_id"], {}) if r["source"] == "S2" else s3.get(r["matched_entity_id"], {})

        print(f"\n{r['s1_entity_id']}  ->  {r['matched_entity_id']} ({r['source']})")
        print(f"  S1 NAME : {a.get('business_name','')}")
        print(f"  S1 ADDR : {a.get('business_address','')}")
        print(f"  S1 CNTRY: {a.get('country','')}")
        print(f"  MX NAME : {b.get('business_name','')}")
        print(f"  MX ADDR : {b.get('business_address','')}")
        print(f"  MX CNTRY: {b.get('country','')}")
