from pathlib import Path

p = Path(r".\output\missed_matches_10k.tsv")
lines = p.read_text(encoding="utf-8").splitlines()

lines[0] = "s1_entity_id\tmatched_entity_id\tsource"

p.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("Header fixed.")
print(lines[0])
