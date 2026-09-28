import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

S1_FILE = BASE / "dataset" / "train_10k" / "train_source1.tsv"
S2_FILE = BASE / "dataset" / "train_10k" / "train_source2.tsv"
MISSED_FILE = BASE / "output" / "s2_missed_matches_inspection.tsv"

# ------------------------------------------------------------
# Load missed S1/S2 IDs
# ------------------------------------------------------------

missed = []

with open(MISSED_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        s1_id = row["source1_entity_id"].strip()
        s2_id = row["missed_s2_entity_id"].strip()

        if s1_id and s2_id:
            missed.append((s1_id, s2_id))

print(f"Missed pairs loaded: {len(missed)}")

s1_needed = {x[0] for x in missed}
s2_needed = {x[1] for x in missed}

print(f"Unique S1 IDs: {len(s1_needed)}")
print(f"Unique S2 IDs: {len(s2_needed)}")

# ------------------------------------------------------------
# Read S1
# ------------------------------------------------------------

s1_records = {}

print("\nReading S1...")

with open(S1_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        eid = row["entity_id"].strip()

        if eid in s1_needed:
            s1_records[eid] = row

# ------------------------------------------------------------
# Read S2
# ------------------------------------------------------------

s2_records = {}

print("Reading S2...")

with open(S2_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        eid = row["entity_id"].strip()

        if eid in s2_needed:
            s2_records[eid] = row

# ------------------------------------------------------------
# Print diagnostic information
# ------------------------------------------------------------

print("\n" + "=" * 100)
print("MISSED S2 MATCH DIAGNOSTICS")
print("=" * 100)

for i, (s1_id, s2_id) in enumerate(missed, 1):

    s1 = s1_records.get(s1_id)
    s2 = s2_records.get(s2_id)

    print(f"\n[{i}]")
    print(f"S1 ID: {s1_id}")
    print(f"S2 ID: {s2_id}")

    if s1 is None:
        print("ERROR: S1 record not found")
        continue

    if s2 is None:
        print("ERROR: S2 record not found")
        continue

    print("\nS1:")
    print("  Name   :", repr(s1.get("business_name", "")))
    print("  Address:", repr(s1.get("business_address", "")))
    print("  Country:", repr(s1.get("country", "")))

    print("\nS2:")
    print("  Name   :", repr(s2.get("business_name", "")))
    print("  Address:", repr(s2.get("business_address", "")))
    print("  Country:", repr(s2.get("country", "")))

    print("-" * 100)