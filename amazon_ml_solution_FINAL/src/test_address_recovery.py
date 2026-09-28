import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent

MISSED = BASE / "output" / "correct_missed_matches_10k.tsv"
S2 = BASE / "dataset" / "train_10k" / "train_source2.tsv"
S3 = BASE / "dataset" / "train_10k" / "train_source3.tsv"


def norm(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s).lower()

    # Keep ASCII letters/numbers only
    s = re.sub(r"[^a-z0-9]+", " ", s)

    return " ".join(s.split())


def address_key(addr):
    s = norm(addr)

    tokens = s.split()

    # numbers
    nums = re.findall(r"\d+", s)

    # useful geographic/address tokens
    useful = []

    for t in tokens:
        if len(t) >= 4:
            useful.append(t)

    # Keep only relatively distinctive tokens
    useful = sorted(set(useful))

    return (
        tuple(sorted(set(nums))),
        tuple(useful)
    )


def compact_address(addr):
    s = norm(addr)
    return re.sub(r"[^a-z0-9]", "", s)


print("Loading missed matches...")

missed = []

with open(MISSED, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        missed.append(row)

print("Missed:", len(missed))


print("Loading S2/S3...")

source_records = []

for path in [S2, S3]:

    with open(path, "r", encoding="utf-8", newline="") as f:

        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            source_records.append(row)


print("Source records:", len(source_records))


# Build exact normalized compact-address index
index = defaultdict(list)

for row in source_records:

    addr = compact_address(row["business_address"])

    if addr:
        index[addr].append(row["entity_id"])


print("Address index keys:", len(index))


recovered = 0
unique_recovered = set()

print("\nChecking missed pairs...\n")


for row in missed:

    s1_addr = compact_address(row["s1_business_address"])
    missed_id = row["missed_entity_id"]

    ids = index.get(s1_addr, [])

    if missed_id in ids:

        recovered += 1
        unique_recovered.add((row["source1_entity_id"], missed_id))


print("=" * 80)
print("RESULT")
print("=" * 80)

print("Total missed pairs:", len(missed))
print("Recovered by exact compact address:", recovered)
print("Recovery %:", round(100 * recovered / len(missed), 2))

print("\nDONE")