import csv

S1_ID = "S1-302869473"

S2_IDS = set()
S3_IDS = set()


def find_ids(path, wanted_ids):
    found = []

    print(f"\nSearching: {path}")

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:

        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            if row["entity_id"] in wanted_ids:
                found.append(row)

                if len(found) == len(wanted_ids):
                    break

    return found


s1 = find_ids(
    r"dataset\train\train_source1.tsv",
    {S1_ID}
)

print("\n" + "=" * 80)
print("SOURCE 1 — NO MATCH EXAMPLE")
print("=" * 80)

for row in s1:
    print(row)