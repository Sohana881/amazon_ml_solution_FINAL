import csv
from pathlib import Path

from data_loader import read_tsv


BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR / "dataset" / "train_10k" / "train_source1.tsv"
S2_FILE = BASE_DIR / "dataset" / "train_10k" / "train_source2.tsv"

MISSED_FILE = BASE_DIR / "output" / "s2_missed_matches.tsv"
OUTPUT_FILE = BASE_DIR / "output" / "s2_missed_matches_inspection.tsv"


# ============================================================
# LOAD MISSED PAIRS
# ============================================================

missed_pairs = []

with open(
    MISSED_FILE,
    "r",
    encoding="utf-8",
    errors="replace",
    newline=""
) as f:

    reader = csv.DictReader(
        f,
        delimiter="\t"
    )

    for row in reader:

        missed_pairs.append(
            (
                row["source1_entity_id"],
                row["missed_s2_entity_id"]
            )
        )


print(
    f"Loaded {len(missed_pairs)} missed S2 matches."
)


# ============================================================
# CREATE ID SETS
# ============================================================

s1_ids_needed = {
    x[0]
    for x in missed_pairs
}

s2_ids_needed = {
    x[1]
    for x in missed_pairs
}


print(
    f"Unique S1 records needed: {len(s1_ids_needed)}"
)

print(
    f"Unique S2 records needed: {len(s2_ids_needed)}"
)


# ============================================================
# READ S1
# ============================================================

print("\nReading S1...")

s1_records = {}

for row in read_tsv(
    str(S1_FILE)
):

    entity_id = row["entity_id"]

    if entity_id in s1_ids_needed:

        s1_records[entity_id] = row


# ============================================================
# READ S2
# ============================================================

print("Reading S2...")

s2_records = {}

for row in read_tsv(
    str(S2_FILE)
):

    entity_id = row["entity_id"]

    if entity_id in s2_ids_needed:

        s2_records[entity_id] = row


# ============================================================
# SAVE INSPECTION
# ============================================================

print("\nWriting inspection file...")

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    errors="replace",
    newline=""
) as f:

    writer = csv.writer(
        f,
        delimiter="\t"
    )

    writer.writerow(
        [
            "source1_entity_id",
            "s1_business_name",
            "s1_business_address",
            "s1_country",
            "missed_s2_entity_id",
            "s2_business_name",
            "s2_business_address",
            "s2_country"
        ]
    )

    for s1_id, s2_id in missed_pairs:

        s1 = s1_records.get(
            s1_id,
            {}
        )

        s2 = s2_records.get(
            s2_id,
            {}
        )

        writer.writerow(
            [
                s1_id,
                s1.get("business_name", ""),
                s1.get("business_address", ""),
                s1.get("country", ""),
                s2_id,
                s2.get("business_name", ""),
                s2.get("business_address", ""),
                s2.get("country", "")
            ]
        )


print("\nDONE!")

print(
    "Saved to:"
)

print(
    OUTPUT_FILE
)