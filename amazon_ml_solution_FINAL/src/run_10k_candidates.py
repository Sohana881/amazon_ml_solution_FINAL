from collections import defaultdict
import csv
import os
import time

from candidate_generator import build_index, find_candidates
from data_loader import read_tsv


# =========================
# SETTINGS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

S1_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "train",
    "train_source1.tsv"
)

S2_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "train",
    "train_source2.tsv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "candidate_benchmark_10k.tsv"
)

NUM_S1 = 10_000


# =========================
# MAIN
# =========================

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("10K CANDIDATE GENERATION BENCHMARK")
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------
    # 1. Build FULL S2 index
    # --------------------------------------------------

    print("\n[1/3] Building FULL S2 index...")
    print("This may take some time.\n")

    name_index, address_index = build_index(
        S2_PATH,
        limit=None
    )

    index_time = time.time() - start_time

    print(f"\nS2 index built in {index_time / 60:.2f} minutes")

    # --------------------------------------------------
    # 2. Read first 10K S1
    # --------------------------------------------------

    print("\n[2/3] Generating candidates for first 10,000 S1...")

    total_candidates = 0
    s1_count = 0

    candidate_counts = []

    start_generation = time.time()

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
        newline=""
    ) as fout:

        writer = csv.writer(
            fout,
            delimiter="\t"
        )

        writer.writerow([
            "source1_id",
            "candidate_entity_id"
        ])

        for s1_row in read_tsv(S1_PATH):

            if s1_count >= NUM_S1:
                break

            s1_id = s1_row.get("entity_id", "")

            candidates = find_candidates(
                s1_row,
                name_index,
                address_index
            )

            count = len(candidates)

            candidate_counts.append(count)
            total_candidates += count
            s1_count += 1

            for candidate in candidates:

                candidate_id = candidate.get(
                    "entity_id",
                    ""
                )

                if candidate_id:
                    writer.writerow([
                        s1_id,
                        candidate_id
                    ])

            if s1_count % 500 == 0:

                elapsed = time.time() - start_generation

                avg = (
                    total_candidates / s1_count
                    if s1_count
                    else 0
                )

                print(
                    f"Processed {s1_count:,}/"
                    f"{NUM_S1:,} S1 | "
                    f"Candidates: {total_candidates:,} | "
                    f"Avg/S1: {avg:,.2f} | "
                    f"Time: {elapsed / 60:.2f} min"
                )

    generation_time = time.time() - start_generation

    # --------------------------------------------------
    # 3. Statistics
    # --------------------------------------------------

    print("\n[3/3] BENCHMARK RESULTS")
    print("=" * 70)

    average_candidates = (
        total_candidates / s1_count
        if s1_count
        else 0
    )

    minimum = (
        min(candidate_counts)
        if candidate_counts
        else 0
    )

    maximum = (
        max(candidate_counts)
        if candidate_counts
        else 0
    )

    sorted_counts = sorted(candidate_counts)

    median = (
        sorted_counts[len(sorted_counts) // 2]
        if sorted_counts
        else 0
    )

    print(f"S1 processed           : {s1_count:,}")
    print(f"Total candidate pairs  : {total_candidates:,}")
    print(f"Average candidates/S1  : {average_candidates:,.2f}")
    print(f"Minimum candidates/S1  : {minimum:,}")
    print(f"Median candidates/S1   : {median:,}")
    print(f"Maximum candidates/S1  : {maximum:,}")
    print(f"Generation time        : {generation_time / 60:.2f} minutes")

    print("\nOutput:")
    print(OUTPUT_PATH)

    # --------------------------------------------------
    # Projection to complete 2.2M S1
    # --------------------------------------------------

    if s1_count > 0:

        projected_total = (
            average_candidates * 2_206_821
        )

        print("\n" + "=" * 70)
        print("PROJECTED FULL DATASET SIZE")
        print("=" * 70)

        print(
            f"Projected candidate pairs for "
            f"2,206,821 S1: "
            f"{projected_total:,.0f}"
        )

        if projected_total > 100_000_000:

            print("\n⚠️ WARNING")
            print(
                "The current blocker is producing too many "
                "candidate pairs for a direct full-scale run."
            )

            print(
                "Do NOT start all 2.2M S1 yet."
            )

        else:

            print("\nCandidate volume looks manageable.")
            print(
                "We can proceed toward the full training run."
            )

    print("\nDone.")


if __name__ == "__main__":
    main()