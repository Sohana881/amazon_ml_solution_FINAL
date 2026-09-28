from pathlib import Path
import csv
import re
import unicodedata
from collections import Counter


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MISSED_FILE = BASE_DIR / "output" / "s2_missed_matches_inspection.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"


# ============================================================
# TSV READER
# ============================================================

def read_tsv(path):

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline=""
    ) as f:

        reader = csv.DictReader(
            f,
            delimiter="\t"
        )

        for row in reader:
            yield row


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
# LOAD MISSED PAIRS
# ============================================================

print("=" * 70)
print("A4 FREQUENCY ANALYSIS ON MISSED MATCHES")
print("=" * 70)

print("\nLoading 138 missed pairs...")

missed_pairs = list(
    read_tsv(MISSED_FILE)
)

print(
    f"Loaded: {len(missed_pairs):,}"
)


# ============================================================
# REQUIRED S2 IDS
# ============================================================

needed_s2 = {
    row["missed_s2_entity_id"]
    for row in missed_pairs
}

print(
    f"Unique S2 IDs needed: {len(needed_s2):,}"
)


# ============================================================
# LOAD ONLY MISSED S2 RECORDS
# ============================================================

print("\nScanning S2...")

s2_records = {}

scanned = 0

for row in read_tsv(S2_FILE):

    entity_id = row.get(
        "entity_id",
        ""
    )

    if entity_id in needed_s2:

        s2_records[entity_id] = row

    scanned += 1

    if len(s2_records) == len(needed_s2):

        print(
            f"Found all {len(needed_s2):,} records "
            f"after scanning {scanned:,} rows."
        )

        break

    if scanned % 1000000 == 0:

        print(
            f"Scanned {scanned:,} rows..."
        )


# ============================================================
# GET A4 KEYS FOR EACH MISSED MATCH
# ============================================================

print("\nGenerating A4 keys for missed matches...")

match_info = []

all_needed_keys = set()

for row in missed_pairs:

    s1_id = row["source1_entity_id"]

    s2_id = row["missed_s2_entity_id"]

    s1_address = row[
        "s1_business_address"
    ]

    s2_row = s2_records.get(
        s2_id
    )

    if not s2_row:
        continue

    s2_address = s2_row.get(
        "business_address",
        ""
    )

    s1_keys = make_a4_keys(
        s1_address
    )

    s2_keys = make_a4_keys(
        s2_address
    )

    common_keys = s1_keys & s2_keys

    for key in common_keys:
        all_needed_keys.add(key)

    match_info.append(
        {
            "s1": s1_id,
            "s2": s2_id,
            "common_keys": common_keys
        }
    )


print(
    f"Unique A4 keys involved in missed matches: "
    f"{len(all_needed_keys):,}"
)


# ============================================================
# SCAN S2 AGAIN
#
# This time only count how frequently the needed A4 keys
# occur in the FULL S2 dataset.
# ============================================================

print("\nCalculating full-S2 frequency of relevant A4 keys...")

key_frequency = Counter()

scanned = 0

for row in read_tsv(S2_FILE):

    address = row.get(
        "business_address",
        ""
    )

    keys = make_a4_keys(
        address
    )

    relevant = keys & all_needed_keys

    for key in relevant:
        key_frequency[key] += 1

    scanned += 1

    if scanned % 1000000 == 0:

        print(
            f"Scanned {scanned:,} rows..."
        )


# ============================================================
# FREQUENCY BUCKETS
# ============================================================

thresholds = [
    1,
    2,
    3,
    5,
    10,
    20,
    50,
    100
]

print("\n")
print("=" * 70)
print("MISSED MATCHES BY A4 KEY FREQUENCY")
print("=" * 70)

for threshold in thresholds:

    recoverable = 0

    for item in match_info:

        frequencies = [
            key_frequency.get(
                key,
                0
            )
            for key in item["common_keys"]
        ]

        if any(
            freq <= threshold
            for freq in frequencies
        ):

            recoverable += 1

    print(
        f"Frequency <= {threshold:3d} : "
        f"{recoverable:3d} / {len(match_info):3d} "
        f"({recoverable / len(match_info) * 100:.2f}%)"
    )


# ============================================================
# MINIMUM FREQUENCY PER MISSED MATCH
# ============================================================

print("\n")
print("=" * 70)
print("MINIMUM A4 FREQUENCY FOR EACH MISSED MATCH")
print("=" * 70)

rows = []

for item in match_info:

    frequencies = [
        key_frequency.get(
            key,
            0
        )
        for key in item["common_keys"]
    ]

    if frequencies:

        minimum_frequency = min(
            frequencies
        )

    else:

        minimum_frequency = None

    rows.append(
        (
            minimum_frequency,
            item["s1"],
            item["s2"],
            len(item["common_keys"])
        )
    )


rows.sort(
    key=lambda x: (
        x[0] if x[0] is not None else 999999999
    )
)


for frequency, s1, s2, common_count in rows:

    if frequency is None:
        frequency_text = "NO KEY"
    else:
        frequency_text = str(frequency)

    print(
        f"{frequency_text:>8} | "
        f"{s1} -> {s2} | "
        f"common keys: {common_count}"
    )

print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)