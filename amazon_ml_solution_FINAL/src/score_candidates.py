from candidate_generator import (
    build_name_index,
    find_candidates
)

from similarity import calculate_similarity


if __name__ == "__main__":

    # --------------------------------------------------
    # Build candidate index
    # --------------------------------------------------

    print("=" * 70)
    print("BUILDING CANDIDATE INDEX")
    print("=" * 70)

    index = build_name_index(
        r"dataset\train\train_source2.tsv",
        limit=100000
    )

    # --------------------------------------------------
    # Known S1 example
    # --------------------------------------------------

    s1 = {
        "entity_id": "S1-102811957",
        "business_name": "Payne Enterprises",
        "business_address": "3315 Fremont Street, Peoria, IL",
        "country": "US"
    }

    # --------------------------------------------------
    # Generate candidates
    # --------------------------------------------------

    candidates = find_candidates(
        s1,
        index
    )

    print("\nCandidates:", len(candidates))

    # --------------------------------------------------
    # Calculate similarity for every candidate
    # --------------------------------------------------

    results = []

    for candidate in candidates:

        features = calculate_similarity(
            s1,
            candidate
        )

        results.append({
            "entity_id": candidate["entity_id"],
            "business_name": candidate["business_name"],
            "business_address": candidate["business_address"],
            **features
        })

    # --------------------------------------------------
    # Sort by name similarity
    # --------------------------------------------------

    results.sort(
        key=lambda x: (
            x["name_similarity"],
            x["address_similarity"],
            x["address_number_match"]
        ),
        reverse=True
    )

    # --------------------------------------------------
    # Display top 20
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("TOP CANDIDATES")
    print("=" * 100)

    for result in results[:20]:

        print(
            f"\n{result['entity_id']}"
            f"\nName    : {result['business_name']}"
            f"\nAddress : {result['business_address']}"
            f"\nName sim: {result['name_similarity']:.4f}"
            f"\nAddr sim: {result['address_similarity']:.4f}"
            f"\nNum     : {result['address_number_match']:.1f}"
            f"\nCountry : {result['country_match']:.1f}"
        )