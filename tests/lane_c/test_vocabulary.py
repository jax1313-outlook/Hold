from dispatch.receipt.vocabulary import CLOSED_VOCABULARY, DEF_CATEGORY, FUEL_CATEGORY, REEFER_FUEL_CATEGORY


def test_vocabulary_matches_frozen_contract():
    assert CLOSED_VOCABULARY == frozenset(
        {
            "fuel", "reefer_fuel", "def", "meals", "oil_additives",
            "parts_maintenance", "truck_wash", "parking", "tolls",
            "scale_tickets", "permits_fees", "supplies", "misc",
        }
    )


def test_special_categories_are_in_the_vocabulary():
    assert FUEL_CATEGORY in CLOSED_VOCABULARY
    assert REEFER_FUEL_CATEGORY in CLOSED_VOCABULARY
    assert DEF_CATEGORY in CLOSED_VOCABULARY
