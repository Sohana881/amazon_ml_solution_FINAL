import csv
import sys

TARGET = "International Automation Consultants"


def search_file(path):
    print("\n" + "=" * 80)
    print("SEARCHING:", path)
    print("=" * 80)

    count = 0

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:

        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            name = row["business_name"]

            if TARGET.lower() in name.lower():
                print(row)
                count += 1

                if count >= 20:
                    break

    print("\nFound:", count)


search_file(r"dataset\train\train_source2.tsv")
search_file(r"dataset\train\train_source3.tsv")
