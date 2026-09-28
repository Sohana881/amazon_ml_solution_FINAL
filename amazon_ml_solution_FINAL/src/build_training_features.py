"""
build_training_features.py
============================================================
Build ML training data for business-entity matching.

S1
 |
 v
active candidates.py
 |
 +---- S2 candidates
 |
 +---- S3 candidates
 |
 v
features.py
 |
 v
ground-truth label
 |
 v
training_features_10k.tsv
"""

import csv
from pathlib import Path

from data_loader import read_tsv
from labels import load_ground_truth

from indexer import build_index
from candidates import find_candidates
from features import calculate_features, FEATURE_COLUMNS
from blocking import DEFAULT_FREQ_CAPS


# ============================================================
# SETTINGS
# ============================================================

SOURCE1_PATH = r"dataset\train_10k\train_source1.tsv"

SOURCE2_PATH = r"dataset\train_10k\train_source2.tsv"

SOURCE3_PATH = r"dataset\train_10k\train_source3.tsv"

GROUND_TRUTH_PATH = (
    r"dataset\train_10k\train_ground_truth.tsv"
)

OUTPUT_PATH = (
    r"output\training_features_10k.tsv"
)

S1_LIMIT = 10_000

S2_LIMIT = 100_000

S3_LIMIT = 100_000


# ============================================================
# SAVE
# ============================================================

def save_features(rows, path):

    if not rows:
        print("No feature rows generated.")
        return

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "source1_entity_id",
        "candidate_entity_id",
        "candidate_source",
    ]

    fieldnames += FEATURE_COLUMNS

    fieldnames.append("label")

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )

        writer.writeheader()

        writer.writerows(rows)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("BUILDING ML TRAINING FEATURES")
    print("=" * 70)

    # ========================================================
    # LOAD GROUND TRUTH
    # ========================================================

    print("\nLoading ground truth...")

    ground_truth = load_ground_truth(
        GROUND_TRUTH_PATH
    )

    print(
        "Ground truth records:",
        len(ground_truth)
    )

    # ========================================================
    # BUILD S2 INDEX
    # ========================================================

    print("\nBuilding S2 index...")

    s2_index = build_index(
        SOURCE2_PATH,
        "S2",
        limit=S2_LIMIT,
    )

    # ========================================================
    # BUILD S3 INDEX
    # ========================================================

    print("\nBuilding S3 index...")

    s3_index = build_index(
        SOURCE3_PATH,
        "S3",
        limit=S3_LIMIT,
    )

    indexes = {
        "S2": s2_index,
        "S3": s3_index,
    }

    # ========================================================
    # FREQUENCY CAPS
    # ========================================================

    freq_caps = dict(
        DEFAULT_FREQ_CAPS
    )

    # Explicitly use RAT20.
    freq_caps["RAT20"] = 20

    print(
        "\nRAT20 bucket cap:",
        freq_caps["RAT20"]
    )

    # ========================================================
    # PROCESS S1
    # ========================================================

    feature_rows = []

    processed = 0

    positive_count = 0
    negative_count = 0

    print("\nProcessing S1 rows...")

    for s1 in read_tsv(
        SOURCE1_PATH
    ):

        if processed >= S1_LIMIT:
            break

        s1_id = s1.get(
            "entity_id",
            ""
        )

        gt_entry = ground_truth.get(
            s1_id,
            {
                "S2": set(),
                "S3": set(),
                "all": set(),
            },
        )

        # ====================================================
        # PROCESS S2 AND S3
        # ====================================================

        for source, index in indexes.items():

            candidates = find_candidates(
                s1,
                index,
                freq_caps=freq_caps,
            )

            true_matches = gt_entry.get(
                source,
                set(),
            )

            for candidate_suffix in candidates:

                candidate_id = (
                    f"{source}-{candidate_suffix}"
                )

                # ------------------------------------------------
                # Retrieve candidate attributes
                # ------------------------------------------------

                attrs = index.get_attrs(
                    candidate_suffix
                )

                if attrs is None:
                    continue

                candidate_name = attrs[0]
                candidate_address = attrs[1]
                candidate_country = attrs[2]

                # ------------------------------------------------
                # Calculate full ML feature vector
                # ------------------------------------------------

                feature_values = calculate_features(
                    s1.get(
                        "business_name",
                        "",
                    ),

                    s1.get(
                        "business_address",
                        "",
                    ),

                    s1.get(
                        "country",
                        "",
                    ),

                    candidate_name,
                    candidate_address,
                    candidate_country,
                )

                # ------------------------------------------------
                # Ground truth
                # ------------------------------------------------

                if candidate_id in true_matches:

                    label = 1

                    positive_count += 1

                else:

                    label = 0

                    negative_count += 1

                # ------------------------------------------------
                # Output row
                # ------------------------------------------------

                output_row = {
                    "source1_entity_id": s1_id,

                    "candidate_entity_id": candidate_id,

                    "candidate_source": source,
                }

                for feature_name in FEATURE_COLUMNS:

                    output_row[
                        feature_name
                    ] = feature_values.get(
                        feature_name,
                        0,
                    )

                output_row["label"] = label

                feature_rows.append(
                    output_row
                )

        processed += 1

        if processed % 100 == 0:

            print(
                f"Processed S1: "
                f"{processed:,}"
                f" | Feature rows: "
                f"{len(feature_rows):,}"
                f" | Positives: "
                f"{positive_count:,}"
                f" | Negatives: "
                f"{negative_count:,}"
            )

    # ========================================================
    # SAVE
    # ========================================================

    print(
        "\nSaving training features..."
    )

    save_features(
        feature_rows,
        OUTPUT_PATH,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "TRAINING FEATURE BUILD COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "S1 processed      :",
        processed,
    )

    print(
        "Feature rows      :",
        len(feature_rows),
    )

    print(
        "Positive examples :",
        positive_count,
    )

    print(
        "Negative examples :",
        negative_count,
    )

    if positive_count:

        print(
            "Negative/positive :",
            f"{negative_count / positive_count:.2f}",
        )

    print(
        "\nSaved to:",
        OUTPUT_PATH,
    )