import csv
import re
import unicodedata
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent

FILE = BASE / "output" / "correct_missed_matches_10k.tsv"


def norm_text(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s)
    s = s.lower()

    # Replace punctuation with spaces
    s = re.sub(r"[^a-z0-9]+", " ", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def compact(s):
    return re.sub(r"[^a-z0-9]", "", norm_text(s))


def address_numbers(s):
    return set(re.findall(r"\d+", norm_text(s)))


def token_set(s):
    return set(norm_text(s).split())


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


rows = []

with open(FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        rows.append(row)


print("=" * 100)
print("ANALYSIS OF THE 710 GENUINELY MISSED MATCHES")
print("=" * 100)

categories = Counter()

strong_address = []
strong_name = []
both_weak = []

for row in rows:

    s1_name = row["s1_business_name"]
    s2_name = row["missed_business_name"]

    s1_addr = row["s1_business_address"]
    s2_addr = row["missed_business_address"]

    name_a = token_set(s1_name)
    name_b = token_set(s2_name)

    addr_a = token_set(s1_addr)
    addr_b = token_set(s2_addr)

    name_score = jaccard(name_a, name_b)
    addr_score = jaccard(addr_a, addr_b)

    nums_a = address_numbers(s1_addr)
    nums_b = address_numbers(s2_addr)

    number_overlap = len(nums_a & nums_b)

    same_number = number_overlap > 0

    if addr_score >= 0.50 and same_number:
        categories["strong_address"] += 1
        strong_address.append(row)

    elif name_score >= 0.50:
        categories["strong_name"] += 1
        strong_name.append(row)

    else:
        categories["other"] += 1
        both_weak.append(row)


print("\nCATEGORY COUNTS")
print("-" * 50)

for k, v in categories.items():
    print(f"{k:20s}: {v:5d}")


print("\nSAMPLE STRONG ADDRESS MATCHES")
print("=" * 100)

for row in strong_address[:20]:

    print("\nS1:", row["s1_business_name"])
    print("   ", row["s1_business_address"])

    print("SRC:", row["missed_business_name"])
    print("   ", row["missed_business_address"])


print("\nSAMPLE STRONG NAME MATCHES")
print("=" * 100)

for row in strong_name[:20]:

    print("\nS1:", row["s1_business_name"])
    print("SRC:", row["missed_business_name"])


print("\nSAMPLE OTHER / HARD MATCHES")
print("=" * 100)

for row in both_weak[:20]:

    print("\nS1:", row["s1_business_name"])
    print("   ", row["s1_business_address"])

    print("SRC:", row["missed_business_name"])
    print("   ", row["missed_business_address"])

print("\nDONE")