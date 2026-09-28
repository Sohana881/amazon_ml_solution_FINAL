from src.evaluate_recall import evaluate
from src.indexer import build_index

s1 = r".\dataset\train_10k\train_source1.tsv"
s2 = r".\dataset\train_10k\train_source2.tsv"
s3 = r".\dataset\train_10k\train_source3.tsv"
gt = r".\dataset\train_10k\train_ground_truth.tsv"

print("Building S2 index...")
s2_index = build_index(s2, "S2")

print("Building S3 index...")
s3_index = build_index(s3, "S3")

print("Evaluating...")
report, missed, stats, combined = evaluate(
    s1,
    {"S2": s2_index, "S3": s3_index},
    gt
)

print(report)

out = r".\output\missed_matches_10k.tsv"

with open(out, "w", encoding="utf-8") as f:
    f.write("s1_entity_id`tmatched_entity_id`tsource\n".replace("`", "\t"))
    for s1_id, match_id, source in missed:
        f.write(f"{s1_id}\t{match_id}\t{source}\n")

print(f"\nMISSED MATCHES: {len(missed):,}")
print(f"Saved to: {out}")
