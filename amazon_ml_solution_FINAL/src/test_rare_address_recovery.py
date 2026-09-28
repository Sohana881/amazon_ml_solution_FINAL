import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).resolve().parent.parent

MISSED = BASE / "output" / "correct_missed_matches_10k.tsv"
S2 = BASE / "dataset" / "train_10k" / "train_source2.tsv"
S3 = BASE / "dataset" / "train_10k" / "train_source3.tsv"


def norm(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)

    return " ".join(s.split())


def address_tokens(addr):
    s = norm(addr)

    tokens = s.split()

    # Keep useful tokens:
    # numbers, alphanumeric identifiers, and reasonably long words
    result = set()

    for t in tokens:

        if re.search(r"\d", t):
            result.add(t)

        elif len(t) >= 5:
            result.add(t)

    return result


print("Loading missed matches...")

missed = []

with open(MISSED, "r", encoding="utf-8", newline="") as f:

    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        missed.append(row)

print("Missed:", len(missed))


print("\nLoading S2/S3...")

source_records = []

for path in [S2, S3]:

    with open(path, "r", encoding="utf-8", newline="") as f:

        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            source_records.append(row)

print("Source records:", len(source_records))


# ---------------------------------------------------------
# BUILD TOKEN FREQUENCIES
# ---------------------------------------------------------

print("\nBuilding address token frequencies...")

token_frequency = Counter()

record_tokens = {}

for row in source_records:

    tokens = address_tokens(row["business_address"])

    record_tokens[row["entity_id"]] = tokens

    for token in tokens:
        token_frequency[token] += 1


print("Unique address tokens:", len(token_frequency))


# ---------------------------------------------------------
# TEST DIFFERENT RARITY THRESHOLDS
# ---------------------------------------------------------

thresholds = [1, 2, 3, 5, 10, 20, 50, 100]


for threshold in thresholds:

    print("\n" + "=" * 80)
    print("MAX TOKEN FREQUENCY:", threshold)
    print("=" * 80)

    index = defaultdict(set)

    for entity_id, tokens in record_tokens.items():

        for token in tokens:

            if token_frequency[token] <= threshold:
                index[token].add(entity_id)


    recovered = 0
    candidate_counts = []

    for row in missed:

        missed_id = row["missed_entity_id"]

        s1_tokens = address_tokens(row["s1_business_address"])

        source_candidates = set()

        for token in s1_tokens:

            if token_frequency[token] <= threshold:

                source_candidates.update(index.get(token, set()))


        candidate_counts.append(len(source_candidates))

        if missed_id in source_candidates:

            recovered += 1


    avg_candidates = (
        sum(candidate_counts) / len(candidate_counts)
        if candidate_counts
        else 0
    )

    print("Recovered:", recovered)
    print("Recovery %:", round(100 * recovered / len(missed), 2))
    print("Avg candidates for missed S1:", round(avg_candidates, 2))


print("\nDONE")