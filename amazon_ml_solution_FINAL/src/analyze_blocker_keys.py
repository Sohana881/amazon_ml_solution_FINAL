from collections import defaultdict
import os
import time

from candidate_generator import make_name_keys, make_address_keys
from data_loader import read_tsv


# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

S1_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "train",
    "train_source1.tsv"
)

S2_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "train",
    "train_source2.tsv"
)

GT_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "train",
    "train_ground_truth.tsv"
)

NUM_S1 = 1000


# ============================================================
# START
# ============================================================

print("=" * 70)
print("BLOCKER KEY ANALYSIS")
print("=" * 70)

print("\nDataset location:")
print(BASE_DIR)

print("\nChecking files...")

for path in [S1_PATH, S2_PATH, GT_PATH]:

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\nFile not found:\n{path}"
        )

print("All required files found.")


# ============================================================
# LOAD FIRST 1000 S1
# ============================================================

print("\nLoading first 1000 S1...")

s1_rows = []

for row in read_tsv(S1_PATH):

    s1_rows.append(row)

    if len(s1_rows) >= NUM_S1:
        break

print(
    f"Loaded {len(s1_rows):,} S1 records."
)


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("\nLoading ground truth...")

ground_truth = {}

gt_count = 0

for row in read_tsv(GT_PATH):

    # IMPORTANT:
    # Ground truth uses source1_entity_id
    s1_id = row.get(
        "source1_entity_id",
        ""
    )

    matches = row.get(
        "matched_entity_ids",
        ""
    )

    if matches.strip():

        ground_truth[s1_id] = set(
            x.strip()
            for x in matches.split(",")
            if x.strip()
        )

    else:

        ground_truth[s1_id] = set()

    gt_count += 1

print(
    f"Loaded {gt_count:,} ground-truth rows."
)


# ============================================================
# VERIFY GROUND TRUTH
# ============================================================

print("\nChecking GT against first 1000 S1...")

matched_s1_count = 0
actual_match_count = 0

for s1 in s1_rows:

    s1_id = s1.get(
        "entity_id",
        ""
    )

    gt = ground_truth.get(
        s1_id,
        set()
    )

    if gt:
        matched_s1_count += 1
        actual_match_count += len(gt)

print(
    f"S1 with at least one GT match: "
    f"{matched_s1_count:,}"
)

print(
    f"Total actual S2/S3 matches in these S1: "
    f"{actual_match_count:,}"
)


# ============================================================
# KEY TYPES
# ============================================================

KEY_TYPES = [
    "NP6",
    "NP8",
    "NS6",
    "FL",
    "FL3",
    "F2",
    "FML",
    "AN",
    "A2",
    "AW2",
    "AL2",
    "NL",
]


# ============================================================
# BUILD PER-KEY S2 INDEXES
# ============================================================

print("\n")
print("=" * 70)
print("BUILDING PER-KEY S2 INDEXES")
print("=" * 70)

print(
    "\nScanning full S2 dataset..."
)

indexes = {
    key_type: defaultdict(set)
    for key_type in KEY_TYPES
}

count = 0

start = time.time()

for row in read_tsv(S2_PATH):

    country = row.get(
        "country",
        ""
    ).strip().upper()

    entity_id = row.get(
        "entity_id",
        ""
    )

    if not entity_id:
        continue

    # --------------------------------------------------------
    # NAME KEYS
    # --------------------------------------------------------

    for key_type, key_value in make_name_keys(
        row.get(
            "business_name",
            ""
        )
    ):

        indexes[key_type][
            (country, key_value)
        ].add(entity_id)

    # --------------------------------------------------------
    # ADDRESS KEYS
    # --------------------------------------------------------

    for key_type, key_value in make_address_keys(
        row.get(
            "business_address",
            ""
        )
    ):

        indexes[key_type][
            (country, key_value)
        ].add(entity_id)

    count += 1

    if count % 1_000_000 == 0:

        elapsed = time.time() - start

        print(
            f"Scanned {count:,} S2 records..."
            f"  Time: {elapsed / 60:.2f} min"
        )


elapsed = time.time() - start

print(
    f"\nFinished indexing {count:,} S2 records."
)

print(
    f"Indexing time: {elapsed / 60:.2f} minutes"
)


# ============================================================
# INDEX SIZE
# ============================================================

print("\nIndex sizes:")

for key_type in KEY_TYPES:

    print(
        f"{key_type:<6}: "
        f"{len(indexes[key_type]):,} unique keys"
    )


# ============================================================
# KEY-BY-KEY ANALYSIS
# ============================================================

print("\n")
print("=" * 70)
print("KEY-BY-KEY RESULTS")
print("=" * 70)

results = []

all_ground_truth = set()

for s1 in s1_rows:

    s1_id = s1.get(
        "entity_id",
        ""
    )

    all_ground_truth.update(
        ground_truth.get(
            s1_id,
            set()
        )
    )


for key_type in KEY_TYPES:

    total_candidates = 0

    matched_found = set()

    for s1 in s1_rows:

        s1_id = s1.get(
            "entity_id",
            ""
        )

        gt = ground_truth.get(
            s1_id,
            set()
        )

        country = s1.get(
            "country",
            ""
        ).strip().upper()

        candidate_ids = set()

        # ----------------------------------------------------
        # NAME KEYS
        # ----------------------------------------------------

        for kt, key_value in make_name_keys(
            s1.get(
                "business_name",
                ""
            )
        ):

            if kt == key_type:

                candidate_ids.update(
                    indexes[key_type].get(
                        (country, key_value),
                        set()
                    )
                )

        # ----------------------------------------------------
        # ADDRESS KEYS
        # ----------------------------------------------------

        for kt, key_value in make_address_keys(
            s1.get(
                "business_address",
                ""
            )
        ):

            if kt == key_type:

                candidate_ids.update(
                    indexes[key_type].get(
                        (country, key_value),
                        set()
                    )
                )

        total_candidates += len(
            candidate_ids
        )

        matched_found.update(
            candidate_ids.intersection(gt)
        )

    actual_matches = len(
        all_ground_truth
    )

    recall = (
        len(matched_found)
        / actual_matches
        * 100
        if actual_matches
        else 0
    )

    average_candidates = (
        total_candidates
        / len(s1_rows)
        if s1_rows
        else 0
    )

    results.append(
        (
            key_type,
            average_candidates,
            len(matched_found),
            recall
        )
    )


# ============================================================
# PRINT KEY RESULTS
# ============================================================

print()

print(
    f"{'KEY':<8}"
    f"{'AVG CAND/S1':>18}"
    f"{'MATCHES FOUND':>18}"
    f"{'RECALL':>12}"
)

print("-" * 70)

for (
    key_type,
    average_candidates,
    found,
    recall
) in results:

    print(
        f"{key_type:<8}"
        f"{average_candidates:>18,.2f}"
        f"{found:>18,}"
        f"{recall:>11.2f}%"
    )


# ============================================================
# COMBINED BLOCKER
# ============================================================

print("\n")
print("=" * 70)
print("COMBINED BLOCKER ANALYSIS")
print("=" * 70)

combined_candidates = 0

combined_found = set()

for s1 in s1_rows:

    s1_id = s1.get(
        "entity_id",
        ""
    )

    gt = ground_truth.get(
        s1_id,
        set()
    )

    country = s1.get(
        "country",
        ""
    ).strip().upper()

    candidate_ids = set()

    # --------------------------------------------------------
    # ALL NAME KEYS
    # --------------------------------------------------------

    for key_type, key_value in make_name_keys(
        s1.get(
            "business_name",
            ""
        )
    ):

        candidate_ids.update(
            indexes[key_type].get(
                (country, key_value),
                set()
            )
        )

    # --------------------------------------------------------
    # ALL ADDRESS KEYS
    # --------------------------------------------------------

    for key_type, key_value in make_address_keys(
        s1.get(
            "business_address",
            ""
        )
    ):

        candidate_ids.update(
            indexes[key_type].get(
                (country, key_value),
                set()
            )
        )

    combined_candidates += len(
        candidate_ids
    )

    combined_found.update(
        candidate_ids.intersection(gt)
    )


combined_average = (
    combined_candidates
    / len(s1_rows)
    if s1_rows
    else 0
)

combined_recall = (
    len(combined_found)
    / len(all_ground_truth)
    * 100
    if all_ground_truth
    else 0
)


# ============================================================
# FINAL RESULTS
# ============================================================

print()

print(
    f"S1 records analyzed     : "
    f"{len(s1_rows):,}"
)

print(
    f"Actual GT matches       : "
    f"{len(all_ground_truth):,}"
)

print(
    f"Combined candidates     : "
    f"{combined_candidates:,}"
)

print(
    f"Unique candidates/S1    : "
    f"{combined_average:,.2f}"
)

print(
    f"Matches found           : "
    f"{len(combined_found):,}"
)

print(
    f"S2/S3-inclusive recall  : "
    f"{combined_recall:.2f}%"
)


# ============================================================
# DONE
# ============================================================

print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)