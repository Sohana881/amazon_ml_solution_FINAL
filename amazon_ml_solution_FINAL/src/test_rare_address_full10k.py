import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).resolve().parent.parent

S1 = BASE / "dataset" / "train_10k" / "train_source1.tsv"
S2 = BASE / "dataset" / "train_10k" / "train_source2.tsv"
S3 = BASE / "dataset" / "train_10k" / "train_source3.tsv"
MISSED = BASE / "output" / "correct_missed_matches_10k.tsv"


def norm(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)

    return " ".join(s.split())


def address_tokens(addr):
    s = norm(addr)

    tokens = s.split()

    result = set()

    for t in tokens:

        if re.search(r"\d", t):
            result.add(t)

        elif len(t) >= 5:
            result.add(t)

    return result


print("Loading S1...")

s1_records = []

with open(S1, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        s1_records.append(row)

print("S1:", len(s1_records))


print("Loading S2/S3...")

source_records = []

for path in [S2, S3]:

    with open(path, "r", encoding="utf-8", newline="") as f:

        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            source_records.append(row)

print("S2/S3:", len(source_records))


print("\nBuilding token frequencies...")

freq = Counter()
record_tokens = {}

for row in source_records:

    tokens = address_tokens(row["business_address"])

    record_tokens[row["entity_id"]] = tokens

    for token in tokens:
        freq[token] += 1


print("Unique tokens:", len(freq))


print("\nLoading genuine misses...")

missed_pairs = set()

with open(MISSED, "r", encoding="utf-8", newline="") as f:

    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:

        missed_pairs.add(
            (
                row["source1_entity_id"],
                row["missed_entity_id"]
            )
        )

print("Missed pairs:", len(missed_pairs))


thresholds = [5, 10, 20, 50, 100]


for threshold in thresholds:

    print("\n" + "=" * 90)
    print("THRESHOLD:", threshold)
    print("=" * 90)

    # token -> source IDs
    index = defaultdict(set)

    for entity_id, tokens in record_tokens.items():

        for token in tokens:

            if freq[token] <= threshold:

                index[token].add(entity_id)


    total_candidates = 0
    max_candidates = 0

    recovered = 0

    recovered_pairs = set()

    for row in s1_records:

        s1_id = row["entity_id"]

        tokens = address_tokens(row["business_address"])

        candidates = set()

        for token in tokens:

            if freq[token] <= threshold:

                candidates.update(index.get(token, set()))


        count = len(candidates)

        total_candidates += count

        max_candidates = max(max_candidates, count)

        for candidate in candidates:

            if (s1_id, candidate) in missed_pairs:

                recovered_pairs.add((s1_id, candidate))


    recovered = len(recovered_pairs)

    avg_candidates = total_candidates / len(s1_records)

    print("Recovered genuine misses :", recovered)
    print(
        "Recovery of 710 misses   :",
        round(100 * recovered / len(missed_pairs), 2),
        "%"
    )

    print("Extra candidate pairs    :", total_candidates)

    print(
        "Extra candidates / S1    :",
        round(avg_candidates, 2)
    )

    print("Maximum candidates / S1  :", max_candidates)


print("\nDONE")