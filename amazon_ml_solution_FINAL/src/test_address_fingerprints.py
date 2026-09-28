import csv
import re
from pathlib import Path
from collections import defaultdict

from data_loader import read_tsv


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source1.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"
GT_FILE = BASE_DIR.parent / "dataset" / "train" / "train_ground_truth.tsv"

MISSED_FILE = BASE_DIR / "output" / "s2_missed_matches.tsv"

LIMIT_S1 = 1000


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower()

    # Remove accents / non-ASCII noise
    text = (
        text.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
    )

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def address_tokens(address):
    return normalize(address).split()


# ============================================================
# EXTRACT ADDRESS FEATURES
# ============================================================

def get_numbers(tokens):
    """
    Extract numeric-looking address components.

    Examples:
        26-352
        401
        18057
        12831
    """

    nums = []

    for token in tokens:

        if any(char.isdigit() for char in token):

            nums.append(token)

    return nums


def get_alpha_tokens(tokens):
    """
    Keep meaningful alphabetic tokens.
    Remove very common address words.
    """

    stopwords = {
        "road",
        "rd",
        "street",
        "st",
        "avenue",
        "ave",
        "lane",
        "ln",
        "drive",
        "dr",
        "road",
        "floor",
        "flat",
        "unit",
        "house",
        "no",
        "number",
        "plot",
        "building",
        "block",
        "near",
        "opp",
        "opposite",
        "city",
        "town",
        "county",
        "district",
        "india",
        "maharashtra",
        "karnataka",
        "delhi",
        "texas",
        "illinois",
        "ohio",
        "new",
        "york",
    }

    result = []

    for token in tokens:

        if (
            token.isalpha()
            and len(token) >= 4
            and token not in stopwords
        ):
            result.append(token)

    return result


# ============================================================
# ADDRESS FINGERPRINTS
# ============================================================

def make_address_keys(address):
    tokens = address_tokens(address)

    if not tokens:
        return {
            "A1": set(),
            "A2": set(),
            "A3": set(),
            "A4": set(),
        }

    numbers = get_numbers(tokens)
    alpha = get_alpha_tokens(tokens)

    keys = {
        "A1": set(),
        "A2": set(),
        "A3": set(),
        "A4": set(),
    }

    # --------------------------------------------------------
    # A1: numeric component
    # --------------------------------------------------------

    for num in numbers:

        keys["A1"].add(
            f"NUM:{num}"
        )

    # --------------------------------------------------------
    # A2: numeric + nearby meaningful word
    # --------------------------------------------------------

    for num in numbers:

        try:
            idx = tokens.index(num)
        except ValueError:
            continue

        nearby = []

        for j in range(
            max(0, idx - 3),
            min(len(tokens), idx + 4)
        ):

            if tokens[j] == num:
                continue

            if (
                tokens[j].isalpha()
                and len(tokens[j]) >= 4
            ):
                nearby.append(
                    tokens[j]
                )

        for word in nearby:

            keys["A2"].add(
                f"NUMWORD:{num}:{word}"
            )

    # --------------------------------------------------------
    # A3: numeric + last meaningful word
    # --------------------------------------------------------

    if numbers and alpha:

        for num in numbers:

            for word in alpha[-3:]:

                keys["A3"].add(
                    f"NUMCITY:{num}:{word}"
                )

    # --------------------------------------------------------
    # A4: numeric + TWO meaningful words
    #     Most selective
    # --------------------------------------------------------

    if numbers and len(alpha) >= 2:

        for num in numbers:

            for i in range(len(alpha)):

                for j in range(
                    i + 1,
                    len(alpha)
                ):

                    keys["A4"].add(
                        f"NUM2:{num}:{alpha[i]}:{alpha[j]}"
                    )

    return keys


# ============================================================
# BUILD INDEX FOR ONE ADDRESS KEY TYPE
# ============================================================

def build_index(s2_file, key_type):

    index = defaultdict(set)

    count = 0

    print(
        f"\nBuilding {key_type} index..."
    )

    for row in read_tsv(
        str(s2_file)
    ):

        entity_id = row["entity_id"]

        keys = make_address_keys(
            row.get("business_address", "")
        )

        for key in keys[key_type]:

            index[key].add(
                entity_id
            )

        count += 1

        if count % 500000 == 0:

            print(
                f"Indexed {count:,} records..."
            )

    print(
        f"Finished {count:,} S2 records."
    )

    return index


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("=" * 70)
print("ADDRESS FINGERPRINT EXPERIMENT")
print("=" * 70)

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

        ids = row[
            "matched_entity_ids"
        ].strip()

        ground_truth[
            row["source1_entity_id"]
        ] = {
            x.strip()
            for x in ids.split(",")
            if x.strip().startswith("S2-")
        }


# ============================================================
# LOAD FIRST 1000 S1
# ============================================================

print(
    "\nLoading first 1000 S1..."
)

s1_records = []

for row in read_tsv(
    str(S1_FILE)
):

    if len(s1_records) >= LIMIT_S1:
        break

    s1_records.append(row)

print(
    f"Loaded {len(s1_records)} S1 records."
)


# ============================================================
# TEST EACH KEY
# ============================================================

results = []


for key_type in [
    "A1",
    "A2",
    "A3",
    "A4",
]:

    index = build_index(
        S2_FILE,
        key_type
    )

    total_candidates = 0
    actual_matches = 0
    found_matches = 0

    for s1 in s1_records:

        keys = make_address_keys(
            s1.get(
                "business_address",
                ""
            )
        )[key_type]

        candidates = set()

        for key in keys:

            candidates.update(
                index.get(
                    key,
                    set()
                )
            )

        total_candidates += len(
            candidates
        )

        true_matches = ground_truth.get(
            s1["entity_id"],
            set()
        )

        actual_matches += len(
            true_matches
        )

        found_matches += len(
            true_matches
            & candidates
        )

    recall = (
        found_matches / actual_matches
        if actual_matches
        else 0
    )

    avg_candidates = (
        total_candidates
        / len(s1_records)
    )

    results.append(
        (
            key_type,
            actual_matches,
            found_matches,
            actual_matches - found_matches,
            recall,
            total_candidates,
            avg_candidates
        )
    )

    print("\n" + "-" * 70)

    print(
        f"{key_type}"
    )

    print(
        f"Actual matches     : {actual_matches:,}"
    )

    print(
        f"Matches found      : {found_matches:,}"
    )

    print(
        f"Matches missed     : "
        f"{actual_matches - found_matches:,}"
    )

    print(
        f"Recall             : "
        f"{recall * 100:.2f}%"
    )

    print(
        f"Total candidates   : "
        f"{total_candidates:,}"
    )

    print(
        f"Candidates/S1      : "
        f"{avg_candidates:,.2f}"
    )

    del index


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("FINAL ADDRESS FINGERPRINT RESULTS")
print("=" * 70)

print(
    "\nKey | Recall | Candidates/S1"
)

print("-" * 70)

for row in results:

    (
        key_type,
        actual,
        found,
        missed,
        recall,
        total,
        avg
    ) = row

    print(
        f"{key_type:3} | "
        f"{recall * 100:6.2f}% | "
        f"{avg:12,.2f}"
    )