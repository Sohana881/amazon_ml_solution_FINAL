from similarity import calculate_similarity


# --------------------------------------------------
# S1 RECORD
# --------------------------------------------------

s1 = {
    "entity_id": "S1-102811957",
    "business_name": "Payne Enterprises",
    "business_address": "3315 Fremont Street, Peoria, IL",
    "country": "US"
}


# --------------------------------------------------
# KNOWN MATCH 1
# --------------------------------------------------

known_match = {
    "entity_id": "S2-478959098",
    "business_name": "Payne Énterprises",
    "business_address": "3315 FREMONT ST, PEORIA, IL",
    "country": "US"
}


# --------------------------------------------------
# KNOWN MATCH 2
# --------------------------------------------------

known_match_2 = {
    "entity_id": "S2-625774905",
    "business_name": "PAYNE-ENRTPRMISES",
    "business_address": "3315 FREMONT SAINT, PEORIA, IL",
    "country": "US"
}


# --------------------------------------------------
# KNOWN MATCH 3
# --------------------------------------------------

known_match_3 = {
    "entity_id": "S3-449308785",
    "business_name": "Payne Enterprises LLC",
    "business_address": "Fremont St, Peoria, Illinois",
    "country": "US"
}


# --------------------------------------------------
# KNOWN NO-MATCH 1
# --------------------------------------------------

known_no_match = {
    "entity_id": "S2-521228093",
    "business_name": "International Automation Consultants Group",
    "business_address": "338-342 REV WALTON DR, LOCKPORT, IL",
    "country": "US"
}


# --------------------------------------------------
# KNOWN NO-MATCH 2
# --------------------------------------------------

known_no_match_2 = {
    "entity_id": "S3-765861618",
    "business_name": "International Automation Consultants Corp",
    "business_address": "338 Rev Walton Dr, Lockport, Illinois",
    "country": "US"
}


# --------------------------------------------------
# FUNCTION TO PRINT FEATURES
# --------------------------------------------------

def print_features(label, row):

    features = calculate_similarity(
        s1,
        row
    )

    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)

    print("Entity :", row["entity_id"])
    print("Name   :", row["business_name"])
    print("Address:", row["business_address"])
    print("Country:", row["country"])

    print("\nFeatures:")

    for key, value in features.items():

        print(
            f"{key:25s}: {value:.4f}"
        )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 70)
    print("FEATURE EXPERIMENT")
    print("=" * 70)

    print("\nREFERENCE S1")
    print("-" * 70)

    print("Entity :", s1["entity_id"])
    print("Name   :", s1["business_name"])
    print("Address:", s1["business_address"])
    print("Country:", s1["country"])


    # --------------------------------------------------
    # MATCHES
    # --------------------------------------------------

    print_features(
        "KNOWN MATCH 1",
        known_match
    )

    print_features(
        "KNOWN MATCH 2",
        known_match_2
    )

    print_features(
        "KNOWN MATCH 3",
        known_match_3
    )


    # --------------------------------------------------
    # NO MATCHES
    # --------------------------------------------------

    print_features(
        "KNOWN NO-MATCH 1",
        known_no_match
    )

    print_features(
        "KNOWN NO-MATCH 2",
        known_no_match_2
    )