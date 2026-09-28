from pathlib import Path

p = Path("./src/indexer.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    "from blocking import make_name_keys, make_address_keys, make_a4_keys",
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys"
)

text = text.replace(
    "        for key_type, key_value in make_name_keys(name):",
    "        for key_type, key_value in make_name_keys(name) + make_unicode_name_keys(name):"
)

p.write_text(text, encoding="utf-8")


p = Path("./src/candidates.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    "from blocking import make_name_keys, make_address_keys, make_a4_keys, DEFAULT_FREQ_CAPS",
    "from blocking import make_name_keys, make_unicode_name_keys, make_address_keys, make_a4_keys, DEFAULT_FREQ_CAPS"
)

text = text.replace(
    "        make_name_keys(name)\n        + make_address_keys(address)",
    "        make_name_keys(name)\n        + make_unicode_name_keys(name)\n        + make_address_keys(address)"
)

p.write_text(text, encoding="utf-8")

print("indexer.py updated")
print("candidates.py updated")
