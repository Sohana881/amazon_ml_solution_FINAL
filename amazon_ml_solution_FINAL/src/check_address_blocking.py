import csv
from pathlib import Path

from data_loader import read_tsv
from candidate_generator import build_index
from normalize import normalize_address


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

S1_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source1.tsv"
S2_FILE = BASE_DIR.parent / "dataset" / "train" / "train_source2.tsv"
GT_FILE = BASE_DIR.parent / "dataset" / "train" / "train_ground_truth.tsv"

LIMIT_S1 = 1000

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "address_blocking_test.txt"
)


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

print("=" * 60)
print("ADDRESS BLOCKING TEST")
print("=" * 60)

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
        ] = (
            set(ids.split(","))
            if ids
            else set()
        )

print(
    "Ground truth loaded:",
    len(ground_truth)
)


# ============================================================
# BUILD S2 INDEX
# ============================================================

print("\nBuilding S2 index...")

name_index, address_index = build_index(
    str(S2_FILE),
    limit=None
)

print(
    "Address keys:",
    len(address_index)
)


# ============================================================
# LOAD S1
# ============================================================

s1_rows = []

for row in read_tsv(
    str(S1_FILE)
):

    if len(s1_rows) >= LIMIT_S1:
        break

    s1_rows.append(row)

print(
    "S1 records:",
    len(s1_rows)
)


# ============================================================
# TEST EXISTING ADDRESS KEYS
# ============================================================

ADDRESS_KEY_TYPES = [
    "AN",
    "A2",
    "AW2",
    "AL2",
    "NL",
]


# ============================================================
# RESULTS
# ============================================================

results = []


for key_type in ADDRESS_KEY_TYPES:

    actual = 0
    found = 0
    total_candidates = 0

    print(
        "\nTesting:",
        key_type
    )

    for s1 in s1_rows:

        country = (
            s1.get(
                "country",
                ""
            )
            .strip()
            .upper()
        )

        true_matches = ground_truth.get(
            s1["entity_id"],
            set()
        )

        actual += len(
            true_matches
        )

        candidates = set()

        # We use the already-created
        # address index.
        #
        # Candidate generator stores
        # keys as:
        #
        # (country, key_type, key_value)

        address = normalize_address(
            s1.get(
                "business_address",
                ""
            )
        )

        if not address:
            continue

        words = address.split()

        numbers = [
            word
            for word in words
            if word.isdigit()
        ]

        non_numeric = [
            word
            for word in words
            if not word.isdigit()
        ]

        keys = []

        # ----------------------------
        # AN
        # ----------------------------

        if (
            key_type == "AN"
            and numbers
        ):

            number = numbers[0]

            for word in words:

                if (
                    not word.isdigit()
                    and len(word) >= 3
                ):

                    keys.append(
                        (
                            "AN",
                            number
                            + "|"
                            + word[:6]
                        )
                    )

                    break

        # ----------------------------
        # A2
        # ----------------------------

        if (
            key_type == "A2"
            and numbers
            and len(non_numeric) >= 2
        ):

            number = numbers[0]

            keys.append(
                (
                    "A2",
                    number
                    + "|"
                    + non_numeric[0][:4]
                    + "|"
                    + non_numeric[1][:4]
                )
            )

        # ----------------------------
        # AW2
        # ----------------------------

        if (
            key_type == "AW2"
            and len(non_numeric) >= 2
        ):

            keys.append(
                (
                    "AW2",
                    non_numeric[0][:5]
                    + "|"
                    + non_numeric[1][:5]
                )
            )

        # ----------------------------
        # AL2
        # ----------------------------

        if (
            key_type == "AL2"
            and len(non_numeric) >= 2
        ):

            keys.append(
                (
                    "AL2",
                    non_numeric[-2][:5]
                    + "|"
                    + non_numeric[-1][:5]
                )
            )

        # ----------------------------
        # NL
        # ----------------------------

        if (
            key_type == "NL"
            and numbers
            and non_numeric
        ):

            number = numbers[0]

            last_word = non_numeric[-1]

            if len(last_word) >= 3:

                keys.append(
                    (
                        "NL",
                        number
                        + "|"
                        + last_word[:6]
                    )
                )

        # ----------------------------
        # LOOK UP
        # ----------------------------

        for kt, kv in keys:

            full_key = (
                country,
                kt,
                kv
            )

            for row in address_index.get(
                full_key,
                []
            ):

                entity_id = row.get(
                    "entity_id",
                    ""
                )

                if entity_id:
                    candidates.add(
                        entity_id
                    )

        total_candidates += len(
            candidates
        )

        found += len(
            true_matches.intersection(
                candidates
            )
        )

    recall = (
        found / actual
        if actual
        else 0
    )

    avg_candidates = (
        total_candidates
        / len(s1_rows)
    )

    results.append(
        (
            key_type,
            recall,
            found,
            actual - found,
            total_candidates,
            avg_candidates,
        )
    )

    print(
        f"{key_type}: "
        f"Recall={recall * 100:.2f}% | "
        f"Candidates/S1={avg_candidates:,.2f}"
    )


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "ADDRESS BLOCKING TEST\n"
    )

    f.write(
        "=" * 70
        + "\n\n"
    )

    for (
        key_type,
        recall,
        found,
        missed,
        total_candidates,
        avg_candidates,
    ) in results:

        f.write(
            f"{key_type}\n"
        )

        f.write(
            f"Recall: "
            f"{recall * 100:.2f}%\n"
        )

        f.write(
            f"Found: "
            f"{found:,}\n"
        )

        f.write(
            f"Missed: "
            f"{missed:,}\n"
        )

        f.write(
            f"Total candidates: "
            f"{total_candidates:,}\n"
        )

        f.write(
            f"Candidates/S1: "
            f"{avg_candidates:,.2f}\n"
        )

        f.write(
            "-" * 70
            + "\n"
        )


print("\n" + "=" * 60)
print("DONE")
print("=" * 60)

print(
    "\nSaved to:"
)

print(
    OUTPUT_FILE
)