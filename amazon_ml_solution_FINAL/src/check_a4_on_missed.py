from pathlib import Path
import csv
import re
import unicodedata


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MISSED_FILE = BASE_DIR / "output" / "s2_missed_matches_inspection.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"


# ============================================================
# SIMPLE TSV READER
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
# NORMALIZE ADDRESS
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
# A4 KEYS
#
# NUMERIC COMPONENT + TWO ADDRESS WORDS
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

        # Use every pair of meaningful words
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
# LOAD MISSED MATCHES
# ============================================================

print("=" * 70)
print("FAST A4 CHECK ON MISSED S2 MATCHES")
print("=" * 70)

print("\nLoading missed matches...")

missed_pairs = list(
    read_tsv(MISSED_FILE)
)

print(
    f"Missed rows loaded: {len(missed_pairs):,}"
)


# ============================================================
# GET REQUIRED S2 IDS
# ============================================================

needed_s2 = {
    row["missed_s2_entity_id"]
    for row in missed_pairs
}

print(
    f"Unique missed S2 IDs: {len(needed_s2):,}"
)


# ============================================================
# LOAD ONLY THOSE S2 RECORDS
# ============================================================

print("\nScanning S2 for the 138 missed records...")

s2_records = {}

scanned = 0

for row in read_tsv(S2_FILE):

    s2_id = row.get(
        "entity_id",
        ""
    )

    if s2_id in needed_s2:

        s2_records[s2_id] = row

    scanned += 1

    if len(s2_records) == len(needed_s2):

        print(
            f"Found all required records after "
            f"{scanned:,} S2 rows."
        )

        break

    if scanned % 1000000 == 0:

        print(
            f"Scanned {scanned:,} S2 rows..."
        )


print(
    f"Required S2 records found: "
    f"{len(s2_records):,}/{len(needed_s2):,}"
)


# ============================================================
# CHECK A4 MATCH
# ============================================================

print("\nChecking A4 overlap...")

rescued = 0
not_rescued = 0

recovered_rows = []
not_recovered_rows = []


for row in missed_pairs:

    s1_id = row["source1_entity_id"]

    s2_id = row["missed_s2_entity_id"]

    s1_address = row[
        "s1_business_address"
    ]

    s2_row = s2_records.get(
        s2_id
    )

    if s2_row is None:

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

    common = s1_keys & s2_keys

    if common:

        rescued += 1

        recovered_rows.append(
            (
                s1_id,
                s2_id,
                len(common),
                s1_address,
                s2_address
            )
        )

    else:

        not_rescued += 1

        not_recovered_rows.append(
            (
                s1_id,
                s2_id
            )
        )


# ============================================================
# RESULTS
# ============================================================

total = rescued + not_rescued


print("\n")
print("=" * 70)
print("RESULT")
print("=" * 70)

print(
    f"Missed pairs checked : {total:,}"
)

print(
    f"A4 can recover       : {rescued:,}"
)

print(
    f"A4 cannot recover    : {not_rescued:,}"
)

if total:

    print(
        f"Recovery percentage  : "
        f"{rescued / total * 100:.2f}%"
    )


# ============================================================
# SHOW RECOVERED
# ============================================================

print("\n")
print("=" * 70)
print("RECOVERED BY A4")
print("=" * 70)

for item in recovered_rows[:30]:

    s1_id, s2_id, common_count, s1_addr, s2_addr = item

    print(
        f"{s1_id} -> {s2_id} "
        f"| common A4 keys = {common_count}"
    )

    print(
        f"   S1: {s1_addr}"
    )

    print(
        f"   S2: {s2_addr}"
    )


print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)