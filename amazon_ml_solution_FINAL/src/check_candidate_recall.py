import csv
from pathlib import Path

from data_loader import read_tsv
from candidate_generator import build_index, find_candidates


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source1.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"
GT_FILE = BASE_DIR.parent / "dataset" / "train" / "train_ground_truth.tsv"

LIMIT_S1 = 1000
LIMIT_S2 = None

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "s2_candidate_recall.txt"
MISSED_FILE = OUTPUT_DIR / "s2_missed_matches.tsv"


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("=" * 60)
print("S2 CANDIDATE RECALL TEST")
print("=" * 60)

print("\nLoading ground truth...")

ground_truth = {}

with open(
    GT_FILE,
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

        ids = row["matched_entity_ids"].strip()

        # IMPORTANT:
        # Keep ONLY S2 matches.
        s2_ids = {
            x.strip()
            for x in ids.split(",")
            if x.strip().startswith("S2-")
        }

        ground_truth[
            row["source1_entity_id"]
        ] = s2_ids

print(
    "Ground truth loaded:",
    len(ground_truth)
)


# ============================================================
# BUILD S2 INDEX
# ============================================================

print("\nBuilding S2 index...")

name_index, address_index = build_index(
    str(S2_FILE),
    limit=LIMIT_S2
)

print(
    "Name keys    :",
    len(name_index)
)

print(
    "Address keys :",
    len(address_index)
)


# ============================================================
# CHECK S1
# ============================================================

processed = 0
actual = 0
found = 0
total_candidates = 0

missed = []

print(
    "\nChecking first",
    LIMIT_S1,
    "S1 records..."
)

for s1 in read_tsv(
    str(S1_FILE)
):

    if processed >= LIMIT_S1:
        break

    candidates = find_candidates(
        s1,
        name_index,
        address_index
    )

    candidate_ids = {
        row["entity_id"]
        for row in candidates
        if row.get("entity_id")
    }

    total_candidates += len(
        candidate_ids
    )

    true_s2_matches = ground_truth.get(
        s1["entity_id"],
        set()
    )

    actual += len(
        true_s2_matches
    )

    for match_id in true_s2_matches:

        if match_id in candidate_ids:

            found += 1

        else:

            missed.append(
                (
                    s1["entity_id"],
                    match_id
                )
            )

    processed += 1

    if processed % 100 == 0:

        print(
            "Processed:",
            processed
        )


# ============================================================
# RESULTS
# ============================================================

missed_count = actual - found

recall = (
    found / actual
    if actual
    else 0
)

avg_candidates = (
    total_candidates / processed
    if processed
    else 0
)

summary = f"""
============================================================
S2 CANDIDATE RECALL RESULT
============================================================

S1 processed      : {processed}
Actual S2 matches : {actual}
S2 matches found  : {found}
S2 matches missed : {missed_count}
S2 recall         : {recall:.4f}
S2 recall %       : {recall * 100:.2f}%

Total candidates  : {total_candidates}
Avg candidates/S1 : {avg_candidates:.2f}

============================================================
"""


print(summary)


# ============================================================
# SAVE SUMMARY
# ============================================================

with open(
    SUMMARY_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(summary)

print(
    "Summary saved to:"
)

print(
    SUMMARY_FILE
)


# ============================================================
# SAVE MISSED S2 MATCHES
# ============================================================

with open(
    MISSED_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.writer(
        f,
        delimiter="\t"
    )

    writer.writerow(
        [
            "source1_entity_id",
            "missed_s2_entity_id"
        ]
    )

    for s1_id, match_id in missed:

        writer.writerow(
            [
                s1_id,
                match_id
            ]
        )

print(
    "Missed S2 matches saved to:"
)

print(
    MISSED_FILE
)

print(
    f"\nTotal missed S2 matches: {len(missed):,}"
)