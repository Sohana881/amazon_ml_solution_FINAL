import csv


PATH = r"amazon_ml_solution\output\training_features_test.tsv"


if __name__ == "__main__":

    print("=" * 70)
    print("CHECKING POSITIVE TRAINING EXAMPLES")
    print("=" * 70)

    positive_count = 0

    with open(
        PATH,
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

            if row["label"] == "1":

                positive_count += 1

                print(
                    f"\nS1: {row['source1_entity_id']}"
                    f"\nCandidate: {row['candidate_entity_id']}"
                    f"\nSource: {row['candidate_source']}"
                    f"\nName similarity: {row['name_similarity']}"
                    f"\nAddress similarity: {row['address_similarity']}"
                    f"\nAddress number: {row['address_number_match']}"
                    f"\nCountry: {row['country_match']}"
                )

    print("\n" + "=" * 70)
    print("TOTAL POSITIVE EXAMPLES:", positive_count)
    print("=" * 70)