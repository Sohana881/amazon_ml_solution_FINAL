from pathlib import Path

p = Path("./src/blocking.py")
text = p.read_text(encoding="utf-8")

marker = "# ============================================================\n# NAME BLOCKING\n# ============================================================\n"

insert = r'''
# ============================================================
# UNICODE NAME BLOCKING
# ============================================================

def make_unicode_name_keys(name):
    """
    Unicode-preserving name keys.

    Keeps Hindi, Kannada, Gujarati, etc. instead of deleting
    non-ASCII characters.
    """
    if not name:
        return []

    import unicodedata

    n = unicodedata.normalize("NFKC", str(name)).casefold()
    n = " ".join(n.split())

    if not n:
        return []

    keys = []

    compact = "".join(ch for ch in n if not ch.isspace())

    if len(compact) >= 4:
        keys.append(("UNP4", compact[:4]))

    if len(compact) >= 6:
        keys.append(("UNP6", compact[:6]))

    words = n.split()

    if len(words) >= 2:
        first = words[0]
        last = words[-1]

        if len(first) >= 2 and len(last) >= 2:
            keys.append(("UFL", first[:3] + "|" + last[:3]))

    return keys


'''

if marker not in text:
    raise SystemExit("Could not find NAME BLOCKING marker.")

if "def make_unicode_name_keys" not in text:
    text = text.replace(marker, insert + marker)

old = '    return make_name_keys(name) + make_address_keys(address) + make_a4_keys(address)'
new = '    return make_name_keys(name) + make_unicode_name_keys(name) + make_address_keys(address) + make_a4_keys(address)'

if old in text:
    text = text.replace(old, new)

text = text.replace(
    'NAME_KEY_TYPES = {"NP6", "NP8", "NS6", "FL", "FL3", "F2", "FML"}',
    'NAME_KEY_TYPES = {"NP6", "NP8", "NS6", "FL", "FL3", "F2", "FML", "UNP4", "UNP6", "UFL"}'
)

text = text.replace(
    '"A4W": 10,',
    '"A4W": 10,\n    "UNP4": 300,\n    "UNP6": 300,\n    "UFL": 300,'
)

p.write_text(text, encoding="utf-8")

print("Unicode blocker added successfully.")
