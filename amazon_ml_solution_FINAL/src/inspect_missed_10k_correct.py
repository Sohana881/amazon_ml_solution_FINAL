import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

S1_FILE = BASE / "dataset" / "train_10k" / "train_source1.tsv"
S2_FILE = BASE / "dataset" / "train_10k" / "train_source2.tsv"
S3_FILE = BASE / "dataset" / "train_10k" / "train_source3.tsv"
GT_FILE = BASE / "dataset" / "train_10k" / "train_ground_truth.tsv"

CAND_FILE = BASE / "output" / "candidate_pairs_train_10k.tsv"

OUT_FILE = BASE / "output" / "correct_missed_matches_10k.tsv"


def read_tsv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


print("Loading candidate pairs...")
candidate_rows = read_tsv(CAND_FILE)

print("Candidate columns:", candidate_rows[0].keys())

# Candidate pairs into a set
candidate_set = set()

for row in candidate_rows:
    s1 = row.get("source1_entity_id", "").strip()
    sid = row.get("candidate_entity_id", "").strip()

    if s1 and sid:
        candidate_set.add((s1, sid))

print("Candidate pairs:", len(candidate_set))


print("\nLoading ground truth...")
gt_rows = read_tsv(GT_FILE)

print("GT rows:", len(gt_rows))

missed = []

for row in gt_rows:
    s1 = row["source1_entity_id"].strip()

    matched_ids = row.get("matched_entity_ids", "").strip()

    if not matched_ids:
        continue

    for sid in matched_ids.split(","):
        sid = sid.strip()

        if not sid:
            continue

        if (s1, sid) not in candidate_set:
            missed.append((s1, sid))


print("\nMissed matches:", len(missed))
print("Unique S1:", len(set(x[0] for x in missed)))
print("Unique missed entity IDs:", len(set(x[1] for x in missed)))


print("\nLoading S1 records...")
s1_records = {}

with open(S1_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        s1_records[row["entity_id"].strip()] = row


print("S1 records:", len(s1_records))


print("Loading S2/S3 records...")
source_records = {}

for path in [S2_FILE, S3_FILE]:

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            source_records[row["entity_id"].strip()] = row


print("S2/S3 records:", len(source_records))


print("\nWriting diagnostic file...")


with open(
    OUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.writer(f, delimiter="\t")

    writer.writerow([
        "source1_entity_id",
        "s1_business_name",
        "s1_business_address",
        "s1_country",
        "missed_entity_id",
        "missed_business_name",
        "missed_business_address",
        "missed_country",
    ])

    for s1_id, source_id in missed:

        s1 = s1_records.get(s1_id, {})
        src = source_records.get(source_id, {})

        writer.writerow([
            s1_id,
            s1.get("business_name", ""),
            s1.get("business_address", ""),
            s1.get("country", ""),
            source_id,
            src.get("business_name", ""),
            src.get("business_address", ""),
            src.get("country", ""),
        ])


print("\nDONE")
print("Output:", OUT_FILE)
print("Rows written:", len(missed))