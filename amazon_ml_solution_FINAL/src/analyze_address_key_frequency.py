from pathlib import Path
from collections import Counter

from data_loader import read_tsv
from test_address_fingerprints import make_address_keys


BASE_DIR = Path(__file__).resolve().parent.parent

S2_FILE = (
    BASE_DIR.parent
    / "dataset"
    / "train"
    / "train_source2.tsv"
)


print("=" * 70)
print("ADDRESS KEY FREQUENCY ANALYSIS")
print("=" * 70)


counter = Counter()

records = 0


for row in read_tsv(
    str(S2_FILE)
):

    keys = make_address_keys(
        row.get(
            "business_address",
            ""
        )
    )["A4"]

    for key in keys:

        counter[key] += 1

    records += 1

    if records % 500000 == 0:

        print(
            f"Processed {records:,} records..."
        )


print(
    f"\nFinished {records:,} S2 records."
)


print("\nNumber of unique A4 keys:")
print(
    f"{len(counter):,}"
)


# ============================================================
# FREQUENCY DISTRIBUTION
# ============================================================

distribution = Counter(
    counter.values()
)


print("\nFrequency distribution:")

for frequency in sorted(
    distribution
):

    if frequency <= 20:

        print(
            f"Keys occurring {frequency:2d} time(s): "
            f"{distribution[frequency]:,}"
        )


# ============================================================
# THRESHOLDS
# ============================================================

print("\n" + "=" * 70)
print("KEYS BY MAXIMUM FREQUENCY")
print("=" * 70)

for threshold in [
    1,
    2,
    3,
    5,
    10,
    20,
    50,
    100,
]:

    usable = sum(
        1
        for count in counter.values()
        if count <= threshold
    )

    print(
        f"Frequency <= {threshold:3d}: "
        f"{usable:,} keys"
    )


# ============================================================
# EXAMPLES
# ============================================================

print("\n" + "=" * 70)
print("EXAMPLES OF RARE KEYS")
print("=" * 70)

rare_keys = [
    (key, count)
    for key, count in counter.items()
    if count <= 3
]

rare_keys.sort(
    key=lambda x: (x[1], x[0])
)


for key, count in rare_keys[:100]:

    print(
        f"{count:3d} | {key}"
    )