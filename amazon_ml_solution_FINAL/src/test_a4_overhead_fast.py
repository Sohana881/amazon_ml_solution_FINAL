from pathlib import Path
from collections import defaultdict, Counter
import csv
import re
import unicodedata

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

THRESHOLDS = [3, 5, 10]


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
print("FAST A4 CANDIDATE OVERHEAD TEST")
print("=" * 70)

print("\nLoading ground truth...")

ground_truth = {}

for row in read_tsv(str(GT_FILE)):

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
# PREPARE A4 QUERY KEYS
# ============================================================

print("\nPreparing A4 keys for S1...")

# country -> set of A4 keys requested by S1
query_keys_by_country = defaultdict(set)

# For each S1, store its A4 keys
s1_a4_keys = {}

for row in s1_records:

    s1_id = row.get(
        "entity_id",
        ""
    )

    country = row.get(
        "country",
        ""
    ).strip().upper()

    keys = make_a4_keys(
        row.get(
            "business_address",
            ""
        )
    )

    s1_a4_keys[s1_id] = keys

    for key in keys:
        query_keys_by_country[country].add(key)


total_query_keys = sum(
    len(keys)
    for keys in query_keys_by_country.values()
)

print(
    f"Unique S1 A4 keys: {total_query_keys:,}"
)


# ============================================================
# BUILD CURRENT INDEX
# ============================================================

print("\nBuilding CURRENT candidate index...")
print("This is the only large in-memory index.")

name_index, address_index = build_index(
    str(S2_FILE),
    limit=None
)

print("\nCurrent index ready.")


# ============================================================
# GET CURRENT CANDIDATES
# ============================================================

print("\nCalculating current candidates for S1...")

current_candidates_by_s1 = {}

current_total = 0

for row in s1_records:

    s1_id = row.get(
        "entity_id",
        ""
    )

    candidates = find_candidates(
        row,
        name_index,
        address_index
    )

    candidate_ids = {
        candidate.get(
            "entity_id",
            ""
        )
        for candidate in candidates
    }

    candidate_ids.discard("")

    current_candidates_by_s1[s1_id] = candidate_ids

    current_total += len(candidate_ids)


print(
    f"Current candidates total: {current_total:,}"
)

print(
    f"Current candidates/S1: "
    f"{current_total / len(s1_records):,.2f}"
)


# ============================================================
# FIRST S2 PASS
#
# Count only A4 keys that are actually requested by our
# first 1000 S1 records.
# ============================================================

print("\n")
print("=" * 70)
print("PASS 1/2 - COUNTING RELEVANT A4 KEYS")
print("=" * 70)

a4_frequency = Counter()

scanned = 0

for row in read_tsv(str(S2_FILE)):

    country = row.get(
        "country",
        ""
    ).strip().upper()

    requested_keys = query_keys_by_country.get(
        country,
        set()
    )

    if requested_keys:

        s2_keys = make_a4_keys(
            row.get(
                "business_address",
                ""
            )
        )

        relevant_keys = (
            s2_keys &
            requested_keys
        )

        for key in relevant_keys:

            a4_frequency[
                (country, key)
            ] += 1

    scanned += 1

    if scanned % 1000000 == 0:

        print(
            f"Scanned {scanned:,} S2 records..."
        )


print(
    f"Finished first pass: {scanned:,} records."
)

print(
    f"Relevant A4 keys counted: "
    f"{len(a4_frequency):,}"
)


# ============================================================
# SECOND S2 PASS
#
# Instead of building an A4 index, directly add qualifying
# S2 IDs to the S1 candidate sets.
# ============================================================

print("\n")
print("=" * 70)
print("PASS 2/2 - COLLECTING QUALIFYING A4 CANDIDATES")
print("=" * 70)


# threshold -> S1 -> A4 candidate IDs
a4_candidates = {}

for threshold in THRESHOLDS:

    a4_candidates[threshold] = defaultdict(set)


scanned = 0

for row in read_tsv(str(S2_FILE)):

    country = row.get(
        "country",
        ""
    ).strip().upper()

    requested_keys = query_keys_by_country.get(
        country,
        set()
    )

    if requested_keys:

        s2_keys = make_a4_keys(
            row.get(
                "business_address",
                ""
            )
        )

        relevant_keys = (
            s2_keys &
            requested_keys
        )

        qualifying_keys = [
            key
            for key in relevant_keys
            if (
                country,
                key
            ) in a4_frequency
        ]

        if qualifying_keys:

            s2_id = row.get(
                "entity_id",
                ""
            )

            # Find which S1 records requested each key
            for s1_id, s1_keys in s1_a4_keys.items():

                if not s1_keys:
                    continue

                common = (
                    s1_keys &
                    relevant_keys
                )

                if not common:
                    continue

                for threshold in THRESHOLDS:

                    if any(
                        a4_frequency[
                            (country, key)
                        ] <= threshold
                        for key in common
                    ):

                        a4_candidates[
                            threshold
                        ][s1_id].add(
                            s2_id
                        )

    scanned += 1

    if scanned % 1000000 == 0:

        print(
            f"Scanned {scanned:,} S2 records..."
        )


print(
    f"Finished second pass: {scanned:,} records."
)


# ============================================================
# EVALUATE
# ============================================================

print("\n")
print("=" * 70)
print("RESULTS")
print("=" * 70)


actual_total = 0

for row in s1_records:

    s1_id = row.get(
        "entity_id",
        ""
    )

    actual_total += len(
        ground_truth.get(
            s1_id,
            set()
        )
    )


print(
    f"\nActual S2 matches: {actual_total:,}"
)


for threshold in THRESHOLDS:

    print("\n")
    print("-" * 70)
    print(
        f"CURRENT BLOCKER + A4 FREQUENCY <= {threshold}"
    )
    print("-" * 70)

    found_total = 0

    hybrid_total = 0

    a4_total = 0

    extra_total = 0

    for row in s1_records:

        s1_id = row.get(
            "entity_id",
            ""
        )

        current = current_candidates_by_s1.get(
            s1_id,
            set()
        )

        a4 = a4_candidates[
            threshold
        ].get(
            s1_id,
            set()
        )

        hybrid = current | a4

        actual = ground_truth.get(
            s1_id,
            set()
        )

        found_total += len(
            actual & hybrid
        )

        hybrid_total += len(
            hybrid
        )

        a4_total += len(
            a4
        )

        extra_total += len(
            a4 - current
        )

    recall = (
        found_total / actual_total
        if actual_total
        else 0
    )

    current_avg = (
        current_total /
        len(s1_records)
    )

    hybrid_avg = (
        hybrid_total /
        len(s1_records)
    )

    a4_avg = (
        a4_total /
        len(s1_records)
    )

    extra_avg = (
        extra_total /
        len(s1_records)
    )

    print(
        f"Matches found         : {found_total:,}"
    )

    print(
        f"Matches missed        : "
        f"{actual_total - found_total:,}"
    )

    print(
        f"S2 recall             : "
        f"{recall * 100:.2f}%"
    )

    print(
        f"Current candidates/S1 : "
        f"{current_avg:,.2f}"
    )

    print(
        f"A4 candidates/S1      : "
        f"{a4_avg:,.2f}"
    )

    print(
        f"NEW hybrid/S1         : "
        f"{hybrid_avg:,.2f}"
    )

    print(
        f"EXTRA candidates/S1   : "
        f"{extra_avg:,.2f}"
    )


print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)