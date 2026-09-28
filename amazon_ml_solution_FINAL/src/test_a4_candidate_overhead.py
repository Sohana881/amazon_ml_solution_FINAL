from pathlib import Path
import csv
import re
import unicodedata
from collections import defaultdict, Counter

from candidate_generator import build_index, find_candidates
from data_loader import read_tsv


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source1.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"
GT_FILE = BASE_DIR.parent / "dataset" / "train" / "train_ground_truth.tsv"

LIMIT_S1 = 1000


# ============================================================
# ADDRESS NORMALIZATION
# ============================================================

def normalize_address(text):

    text = text or ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = text.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# A4 KEY GENERATOR
# ============================================================

def make_a4_keys(address):

    address = normalize_address(address)

    if not address:
        return set()

    numbers = re.findall(
        r"\d+",
        address
    )

    words = re.findall(
        r"[a-z]+",
        address
    )

    if not numbers or not words:
        return set()

    keys = set()

    for number in numbers:

        for i in range(len(words)):

            for j in range(i + 1, len(words)):

                word1 = words[i]
                word2 = words[j]

                if len(word1) < 2:
                    continue

                if len(word2) < 2:
                    continue

                keys.add(
                    f"NUM2:{number}:{word1}:{word2}"
                )

                keys.add(
                    f"NUM2:{number}:{word2}:{word1}"
                )

    return keys


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("=" * 70)
print("CURRENT BLOCKER + A4 OVERHEAD TEST")
print("=" * 70)

print("\nLoading ground truth...")

ground_truth = {}

for row in read_tsv(str(GT_FILE)):

    # Ground truth uses source1_entity_id
    s1_id = row.get(
        "source1_entity_id",
        ""
    )

    matches = set(
        x.strip()
        for x in row.get(
            "matched_entity_ids",
            ""
        ).split(",")
        if x.strip().startswith("S2-")
    )

    if s1_id:
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

print(
    f"Loaded {len(s1_records):,} S1 records."
)


# ============================================================
# BUILD CURRENT INDEX
# ============================================================

print("\nBuilding current candidate index...")
print("(This is the expensive part; only once.)")

name_index, address_index = build_index(
    str(S2_FILE),
    limit=None
)

print("\nCurrent index ready.")


# ============================================================
# BUILD A4 INDEX WITH FREQUENCY
# ============================================================

print("\nBuilding A4 index...")

a4_index = defaultdict(set)
a4_frequency = Counter()

count = 0

for row in read_tsv(str(S2_FILE)):

    s2_id = row.get(
        "entity_id",
        ""
    )

    address = row.get(
        "business_address",
        ""
    )

    keys = make_a4_keys(address)

    for key in keys:

        a4_index[key].add(s2_id)
        a4_frequency[key] += 1

    count += 1

    if count % 1000000 == 0:

        print(
            f"Indexed {count:,} S2 records..."
        )


print(
    f"Finished {count:,} S2 records."
)


# ============================================================
# TEST THRESHOLDS
# ============================================================

THRESHOLDS = [
    3,
    5,
    10
]


for threshold in THRESHOLDS:

    print("\n")
    print("=" * 70)
    print(
        f"CURRENT BLOCKER + A4 FREQUENCY <= {threshold}"
    )
    print("=" * 70)

    actual_total = 0
    found_total = 0

    current_candidate_total = 0
    hybrid_candidate_total = 0

    for row in s1_records:

        s1_id = row.get(
            "entity_id",
            ""
        )

        actual_matches = ground_truth.get(
            s1_id,
            set()
        )

        actual_total += len(
            actual_matches
        )

        # ----------------------------------------------------
        # CURRENT CANDIDATES
        # ----------------------------------------------------

        current_candidates = set(
            find_candidates(
                row,
                name_index,
                address_index
            )
        )

        # ----------------------------------------------------
        # A4 CANDIDATES
        # ----------------------------------------------------

        a4_candidates = set()

        address = row.get(
            "business_address",
            ""
        )

        keys = make_a4_keys(address)

        for key in keys:

            frequency = a4_frequency.get(
                key,
                0
            )

            if frequency <= threshold:

                a4_candidates.update(
                    a4_index.get(
                        key,
                        set()
                    )
                )

        # ----------------------------------------------------
        # HYBRID
        # ----------------------------------------------------

        hybrid_candidates = (
            current_candidates |
            a4_candidates
        )

        current_candidate_total += len(
            current_candidates
        )

        hybrid_candidate_total += len(
            hybrid_candidates
        )

        found_total += len(
            actual_matches &
            hybrid_candidates
        )


    # ========================================================
    # RESULTS
    # ========================================================

    missed = (
        actual_total -
        found_total
    )

    recall = (
        found_total / actual_total
        if actual_total
        else 0
    )

    avg_current = (
        current_candidate_total /
        len(s1_records)
    )

    avg_hybrid = (
        hybrid_candidate_total /
        len(s1_records)
    )

    extra = (
        avg_hybrid -
        avg_current
    )

    print(
        f"\nActual S2 matches     : {actual_total:,}"
    )

    print(
        f"Matches found         : {found_total:,}"
    )

    print(
        f"Matches missed        : {missed:,}"
    )

    print(
        f"S2 recall             : {recall * 100:.2f}%"
    )

    print(
        f"Current candidates/S1 : {avg_current:,.2f}"
    )

    print(
        f"Hybrid candidates/S1  : {avg_hybrid:,.2f}"
    )

    print(
        f"Extra candidates/S1   : {extra:,.2f}"
    )


print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)