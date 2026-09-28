from pathlib import Path

p = Path("./src/blocking.py")
text = p.read_text(encoding="utf-8")

# Add AT2 function before A4 section
marker = "# ============================================================\n# A4 BLOCKING (numeric address component + NEARBY words)\n# ============================================================\n"

insert = r'''
# ============================================================
# AT2 BLOCKING (informative address-token pairs)
# ============================================================

# Very common address words are poor blocking signals.
# Keep this list deliberately small.
GENERIC_ADDRESS_WORDS = {
    "street", "st", "road", "rd", "avenue", "ave",
    "lane", "ln", "drive", "dr", "boulevard", "blvd",
    "highway", "hwy", "near", "opposite", "opp",
    "building", "bldg", "floor", "fl", "block",
    "district", "city", "state", "india",
    "private", "limited", "ltd", "pvt",
}

def make_at2_keys(address):
    """
    Generate a small number of informative address-token-pair keys.

    Unlike AW2/AL2, this does not depend on token position.
    It selects informative tokens and creates only adjacent pairs
    after sorting by their original position.

    The goal is to recover matches where the business name is in
    another script but the address is shared.
    """
    a = normalize_address(address)

    if not a:
        return []

    tokens = a.split()

    informative = []

    for tok in tokens:
        if tok.isdigit():
            continue

        if len(tok) < 4:
            continue

        if tok in GENERIC_ADDRESS_WORDS:
            continue

        informative.append(tok)

    if len(informative) < 2:
        return []

    # Keep at most 6 informative tokens per address.
    # Prefer longer tokens because they are generally more distinctive.
    informative = sorted(
        informative,
        key=lambda x: (-len(x), x)
    )[:6]

    keys = []
    seen = set()

    # Only 5-6 pairs, rather than O(n^2) over the whole address.
    for i in range(len(informative) - 1):
        w1 = informative[i][:8]
        w2 = informative[i + 1][:8]

        if w1 == w2:
            continue

        a1, a2 = sorted((w1, w2))
        key_value = a1 + "|" + a2

        if key_value not in seen:
            seen.add(key_value)
            keys.append(("AT2", key_value))

    return keys


'''

if marker not in text:
    raise SystemExit("A4 marker not found.")

if "def make_at2_keys" not in text:
    text = text.replace(marker, insert + marker)

# Add AT2 to combined key sets
text = text.replace(
    'ADDRESS_KEY_TYPES = {"AN", "A2", "AW2", "AL2", "NL", "A4W"}',
    'ADDRESS_KEY_TYPES = {"AN", "A2", "AW2", "AL2", "NL", "A4W", "AT2"}'
)

# Add AT2 cap
text = text.replace(
    '    "A4W": 10,\n',
    '    "A4W": 10,\n    "AT2": 20,\n'
)

p.write_text(text, encoding="utf-8")

print("AT2 blocker added successfully.")
