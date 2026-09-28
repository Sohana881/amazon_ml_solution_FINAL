from collections import defaultdict

from normalize import normalize_business_name, normalize_address
from data_loader import read_tsv


# ============================================================
# KEY GENERATION
# ============================================================

def make_name_keys(name):
    """
    Generate selective blocking keys.

    IMPORTANT:
    We avoid generic single-word keys because they create
    enormous candidate buckets.
    """

    n = normalize_business_name(name)

    if not n:
        return []

    keys = []

    compact = n.replace(" ", "")

    # --------------------------------------------------------
    # Prefixes
    # --------------------------------------------------------

    if len(compact) >= 6:
        keys.append(("NP6", compact[:6]))

    if len(compact) >= 8:
        keys.append(("NP8", compact[:8]))

    # --------------------------------------------------------
    # Suffix
    # --------------------------------------------------------

    if len(compact) >= 6:
        keys.append(("NS6", compact[-6:]))

    # --------------------------------------------------------
    # Token-based composite keys
    # --------------------------------------------------------

    words = n.split()

    if len(words) >= 2:

        first = words[0]
        last = words[-1]

        if len(first) >= 3 and len(last) >= 3:

            keys.append(
                (
                    "FL",
                    first[:4] + "|" + last[:4]
                )
            )

            keys.append(
                (
                    "FL3",
                    first[:3] + "|" + last[:5]
                )
            )

    # --------------------------------------------------------
    # First two words together
    # --------------------------------------------------------

    if len(words) >= 2:

        w1 = words[0]
        w2 = words[1]

        if len(w1) >= 3 and len(w2) >= 3:

            keys.append(
                (
                    "F2",
                    w1[:5] + "|" + w2[:5]
                )
            )

    # --------------------------------------------------------
    # First word + middle + last
    # --------------------------------------------------------

    if len(words) >= 3:

        first = words[0]
        middle = words[-2]
        last = words[-1]

        if len(first) >= 3 and len(last) >= 3:

            keys.append(
                (
                    "FML",
                    first[:3]
                    + "|"
                    + middle[:3]
                    + "|"
                    + last[:3]
                )
            )

    return keys


# ============================================================
# ADDRESS BLOCKING
# ============================================================

def make_address_keys(address):
    """
    Generate selective address blocking keys.

    We deliberately DO NOT use a number alone as a key.
    """

    a = normalize_address(address)

    if not a:
        return []

    keys = []

    words = a.split()

    if not words:
        return []

    # --------------------------------------------------------
    # Find numeric tokens
    # --------------------------------------------------------

    numbers = []

    for word in words:

        if word.isdigit():
            numbers.append(word)

    # --------------------------------------------------------
    # Number + nearby street token
    # --------------------------------------------------------

    if numbers:

        number = numbers[0]

        # Number + first non-numeric word
        for word in words:

            if not word.isdigit() and len(word) >= 3:

                keys.append(
                    (
                        "AN",
                        number + "|" + word[:6]
                    )
                )

                break

        # Number + second non-numeric word
        non_numeric = [
            w for w in words
            if not w.isdigit()
        ]

        if len(non_numeric) >= 2:

            keys.append(
                (
                    "A2",
                    number
                    + "|"
                    + non_numeric[0][:4]
                    + "|"
                    + non_numeric[1][:4]
                )
            )

    # --------------------------------------------------------
    # First two address words
    # --------------------------------------------------------

    non_numeric = [
        w for w in words
        if not w.isdigit()
    ]

    if len(non_numeric) >= 2:

        w1 = non_numeric[0]
        w2 = non_numeric[1]

        if len(w1) >= 3 and len(w2) >= 3:

            keys.append(
                (
                    "AW2",
                    w1[:5] + "|" + w2[:5]
                )
            )

    # --------------------------------------------------------
    # Last two address words
    # --------------------------------------------------------

    if len(non_numeric) >= 2:

        w1 = non_numeric[-2]
        w2 = non_numeric[-1]

        if len(w1) >= 3 and len(w2) >= 3:

            keys.append(
                (
                    "AL2",
                    w1[:5] + "|" + w2[:5]
                )
            )

    # --------------------------------------------------------
    # Number + last address token
    # --------------------------------------------------------

    if numbers and non_numeric:

        number = numbers[0]
        last_word = non_numeric[-1]

        if len(last_word) >= 3:

            keys.append(
                (
                    "NL",
                    number + "|" + last_word[:6]
                )
            )

    return keys


# ============================================================
# RARE ADDRESS TOKEN BLOCKING
# ============================================================

GENERIC_ADDRESS_WORDS = {
    "street",
    "st",
    "road",
    "rd",
    "avenue",
    "ave",
    "lane",
    "ln",
    "drive",
    "dr",
    "boulevard",
    "blvd",
    "highway",
    "hwy",
    "near",
    "opposite",
    "opp",
    "building",
    "bldg",
    "floor",
    "fl",
    "block",
    "district",
    "city",
    "state",
    "india",
    "private",
    "limited",
    "ltd",
    "pvt",
}


def make_rare_address_token_keys(address):
    """
    Generate individual informative address-token keys.

    The frequency cap is applied when the index is built.

    RAT20:
        maximum 20 records per country + token bucket.
    """

    a = normalize_address(address)

    if not a:
        return []

    tokens = a.split()

    keys = []

    seen = set()

    for token in tokens:

        # Never use a number alone.
        if token.isdigit():
            continue

        # Very short tokens are usually weak.
        if len(token) < 4:
            continue

        # Remove generic address words.
        if token in GENERIC_ADDRESS_WORDS:
            continue

        token = token[:12]

        if token in seen:
            continue

        seen.add(token)

        keys.append(
            (
                "RAT20",
                token
            )
        )

    return keys


# ============================================================
# INDEX BUILDING
# ============================================================

RAT20_MAX_BUCKET = 20


def build_index(path, limit=None):

    name_index = defaultdict(list)
    address_index = defaultdict(list)

    # Separate frequency tracking for RAT20.
    rare_address_frequency = defaultdict(int)

    count = 0

    print(
        f"Building index from: {path}"
    )

    for row in read_tsv(path):

        if limit is not None and count >= limit:
            break

        entity_id = row.get(
            "entity_id",
            ""
        )

        name = row.get(
            "business_name",
            ""
        )

        address = row.get(
            "business_address",
            ""
        )

        country = row.get(
            "country",
            ""
        ).strip().upper()

        # ----------------------------------------------------
        # Name index
        # ----------------------------------------------------

        for key_type, key_value in make_name_keys(name):

            full_key = (
                country,
                key_type,
                key_value
            )

            name_index[full_key].append(row)

        # ----------------------------------------------------
        # Original address index
        # ----------------------------------------------------

        for key_type, key_value in make_address_keys(address):

            full_key = (
                country,
                key_type,
                key_value
            )

            address_index[full_key].append(row)

        # ----------------------------------------------------
        # RAT20 ADDRESS INDEX
        # ----------------------------------------------------

        for key_type, key_value in make_rare_address_token_keys(
            address
        ):

            full_key = (
                country,
                key_type,
                key_value
            )

            # Only allow the first 20 records into a RAT20
            # bucket.
            if rare_address_frequency[full_key] < RAT20_MAX_BUCKET:

                address_index[full_key].append(row)

                rare_address_frequency[full_key] += 1

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        count += 1

        if count % 500000 == 0:

            print(
                f"Indexed {count:,} records..."
            )

    print(
        f"Finished indexing {count:,} records."
    )

    print(
        f"Name index keys    : {len(name_index):,}"
    )

    print(
        f"Address index keys : {len(address_index):,}"
    )

    print(
        f"RAT20 max bucket   : {RAT20_MAX_BUCKET}"
    )

    return name_index, address_index


# ============================================================
# CANDIDATE SEARCH
# ============================================================

def find_candidates(
    source1_row,
    name_index,
    address_index
):

    candidates = {}

    country = (
        source1_row
        .get("country", "")
        .strip()
        .upper()
    )

    name = source1_row.get(
        "business_name",
        ""
    )

    address = source1_row.get(
        "business_address",
        ""
    )

    # --------------------------------------------------------
    # Name candidates
    # --------------------------------------------------------

    for key_type, key_value in make_name_keys(name):

        full_key = (
            country,
            key_type,
            key_value
        )

        for row in name_index.get(
            full_key,
            []
        ):

            entity_id = row.get(
                "entity_id",
                ""
            )

            if entity_id:

                candidates[entity_id] = row

    # --------------------------------------------------------
    # Original address candidates
    # --------------------------------------------------------

    for key_type, key_value in make_address_keys(address):

        full_key = (
            country,
            key_type,
            key_value
        )

        for row in address_index.get(
            full_key,
            []
        ):

            entity_id = row.get(
                "entity_id",
                ""
            )

            if entity_id:

                candidates[entity_id] = row

    # --------------------------------------------------------
    # RAT20 address-token candidates
    # --------------------------------------------------------

    for key_type, key_value in make_rare_address_token_keys(
        address
    ):

        full_key = (
            country,
            key_type,
            key_value
        )

        for row in address_index.get(
            full_key,
            []
        ):

            entity_id = row.get(
                "entity_id",
                ""
            )

            if entity_id:

                candidates[entity_id] = row

    return list(
        candidates.values()
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    S2_FILE = r"dataset\train\train_source2.tsv"

    print(
        "\n========================================"
    )

    print(
        "BUILDING S2 CANDIDATE INDEX"
    )

    print(
        "========================================\n"
    )

    name_index, address_index = build_index(
        S2_FILE,
        limit=None
    )

    test_row = {
        "entity_id": "S1-TEST",
        "business_name": "Payne Enterprises",
        "business_address": "3315 Fremont Street, Peoria, IL",
        "country": "US"
    }

    candidates = find_candidates(
        test_row,
        name_index,
        address_index
    )

    print(
        "\n========================================"
    )

    print(
        "TEST RESULT"
    )

    print(
        "========================================"
    )

    print(
        "Candidates found:",
        len(candidates)
    )

    print(
        "\nFirst 20 candidates:"
    )

    for row in candidates[:20]:

        print(
            row.get("entity_id"),
            "|",
            row.get("business_name"),
            "|",
            row.get("business_address"),
            "|",
            row.get("country")
        )