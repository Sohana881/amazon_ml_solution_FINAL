import pandas as pd

PATH = r"..\dataset\train\train_ground_truth.tsv"

print("Loading ground truth...")

df = pd.read_csv(
    PATH,
    sep="\t",
    dtype=str
)

print("\nTotal rows:", len(df))

# Convert empty values to empty strings
df["matched_entity_ids"] = df["matched_entity_ids"].fillna("")

# Count matches
df["match_count"] = df["matched_entity_ids"].apply(
    lambda x: 0 if not x.strip() else len(x.split(","))
)

print("\nMatch count distribution:")
print(df["match_count"].value_counts().sort_index())

print("\nBasic statistics:")
print(df["match_count"].describe())

print("\nMaximum matches for one Source 1:")
print(df["match_count"].max())

# Count S2 and S3 matches
def count_source(x, prefix):
    if not x.strip():
        return 0
    return sum(
        1 for item in x.split(",")
        if item.startswith(prefix)
    )

df["s2_count"] = df["matched_entity_ids"].apply(
    lambda x: count_source(x, "S2-")
)

df["s3_count"] = df["matched_entity_ids"].apply(
    lambda x: count_source(x, "S3-")
)

print("\nTotal S2 matches:", df["s2_count"].sum())
print("Total S3 matches:", df["s3_count"].sum())

print("\nS1 entities with NO matches:",
      (df["match_count"] == 0).sum())

print("S1 entities with AT LEAST ONE match:",
      (df["match_count"] > 0).sum())

print("\nTop 10 entities with most matches:")
print(
    df.nlargest(10, "match_count")[
        ["source1_entity_id", "matched_entity_ids", "match_count"]
    ].to_string(index=False)
)