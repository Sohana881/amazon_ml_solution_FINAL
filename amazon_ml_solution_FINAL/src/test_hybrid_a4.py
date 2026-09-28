from pathlib import Path
from collections import defaultdict, Counter

from data_loader import read_tsv
from candidate_generator import build_index, find_candidates
from test_address_fingerprints import make_address_keys


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source1.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"
GT_FILE = BASE_DIR.parent / "dataset" / "train" / "train_ground_truth.tsv"


LIMIT_S1 = 1000


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("=" * 70)
print("HYBRID CURRENT BLOCKER + RARE A4 EXPERIMENT")
print("=" * 70)

print("\nLoading ground truth...")

ground_truth = {}

for row in read_tsv(str(GT_FILE)):
    s1_id = row["entity_id"]

    matches = set(
        x.strip()
        for x in row.get("matched_entity_ids", "").split(",")
        if x.strip().startswith("S2-")
    )

    ground_truth[s1_id] = matches


# ============================================================
# LOAD FIRST 1000 S1
# ============================================================

print("\nLoading first 1000 S1...")

s1_records = []

for row in read_tsv(str(S1_FILE)):
    s1_records.append(row)

    if len(s1_records) >= LIMIT_S1:
        break

print(f"Loaded {len(s1_records):,} S1 records.")


# ============================================================
# BUILD CURRENT CANDIDATE INDEX
# ============================================================

print("\nBuilding CURRENT candidate index...")

current_name_index, current_address_index = build_index(
    str(S2_FILE),
    limit=None
)

print("Current candidate index ready.")


# ============================================================
# BUILD A4 INDEX + FREQUENCY
# ============================================================

print("\nBuilding A4 index...")

a4_index = defaultdict(set)
a4_frequency = Counter()

count = 0

for row in read_tsv(str(S2_FILE)):

    s2_id = row["entity_id"]

    keys = make_address_keys(
        row.get("business_address", "")
    )["A4"]

    for key in keys:
        a4_index[key].add(s2_id)
        a4_frequency[key] += 1

    count += 1

    if count % 500000 == 0:
        print(f"Indexed {count:,} S2 records...")

print(f"Finished {count:,} S2 records.")

print(f"Unique A4 keys: {len(a4_index):,}")


# ============================================================
# TEST DIFFERENT FREQUENCY THRESHOLDS
# ============================================================

THRESHOLDS = [1, 2, 3, 5, 10]


for threshold in THRESHOLDS:

    print("\n")
    print("=" * 70)
    print(f"A4 FREQUENCY <= {threshold}")
    print("=" * 70)

    actual_total = 0
    found_total = 0

    total_current_candidates = 0
    total_hybrid_candidates = 0

    rescued_matches = 0

    for row in s1_records:

        s1_id = row["entity_id"]

        actual_matches = ground_truth.get(s1_id, set())

        actual_total += len(actual_matches)

        # ----------------------------------------------------
        # CURRENT CANDIDATES
        # ----------------------------------------------------

        current_candidates = find_candidates(
            row,
            current_name_index,
            current_address_index
        )

        current_candidates = set(current_candidates)

        # ----------------------------------------------------
        # RARE A4 CANDIDATES
        # ----------------------------------------------------

        rare_a4_candidates = set()

        a4_keys = make_address_keys(
            row.get("business_address", "")
        )["A4"]

        for key in a4_keys:

            if a4_frequency.get(key, 0) <= threshold:

                rare_a4_candidates.update(
                    a4_index.get(key, set())
                )

        # ----------------------------------------------------
        # HYBRID
        # ----------------------------------------------------

        hybrid_candidates = (
            current_candidates |
            rare_a4_candidates
        )

        total_current_candidates += len(current_candidates)
        total_hybrid_candidates += len(hybrid_candidates)

        # ----------------------------------------------------
        # RECALL
        # ----------------------------------------------------

        found = actual_matches & hybrid_candidates

        found_total += len(found)

        # ----------------------------------------------------
        # HOW MANY MISSED MATCHES WERE RESCUED?
        # ----------------------------------------------------

        current_found = actual_matches & current_candidates

        rescued = (
            found -
            current_found
        )

        rescued_matches += len(rescued)


    # ========================================================
    # RESULTS
    # ========================================================

    missed = actual_total - found_total

    recall = (
        found_total / actual_total
        if actual_total
        else 0
    )

    avg_current = (
        total_current_candidates / len(s1_records)
    )

    avg_hybrid = (
        total_hybrid_candidates / len(s1_records)
    )

    additional_candidates = (
        avg_hybrid - avg_current
    )

    print("\nActual S2 matches      :", f"{actual_total:,}")
    print("Matches found          :", f"{found_total:,}")
    print("Matches missed         :", f"{missed:,}")

    print(
        "S2 recall              :",
        f"{recall * 100:.2f}%"
    )

    print(
        "Current candidates/S1  :",
        f"{avg_current:,.2f}"
    )

    print(
        "Hybrid candidates/S1   :",
        f"{avg_hybrid:,.2f}"
    )

    print(
        "Additional candidates  :",
        f"{additional_candidates:,.2f}"
    )

    print(
        "Missed matches rescued :",
        f"{rescued_matches:,}"
    )


print("\n")
print("=" * 70)
print("EXPERIMENT COMPLETE")
print("=" * 70)