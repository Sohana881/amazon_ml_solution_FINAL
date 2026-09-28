from pathlib import Path

# =========================
# FIX indexer.py
# =========================
p = Path("./src/indexer.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys",
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys, make_at2_keys"
)

text = text.replace(
    "make_a4_keys(address):",
    "make_a4_keys(address) + make_at2_keys(address):"
)

p.write_text(text, encoding="utf-8")


# =========================
# FIX candidates.py
# =========================
p = Path("./src/candidates.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys, DEFAULT_FREQ_CAPS",
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys, make_at2_keys, DEFAULT_FREQ_CAPS"
)

text = text.replace(
    "+ make_a4_keys(address)",
    "+ make_a4_keys(address)\n        + make_at2_keys(address)"
)

p.write_text(text, encoding="utf-8")

print("AT2 FULLY INTEGRATED")
