from src.core.profile_state import compute_profile_confidence


def test_compute_profile_confidence_is_zero_for_new_users() -> None:
    assert compute_profile_confidence(0) == 0.0


def test_compute_profile_confidence_matches_brain_formula_examples() -> None:
    confidence_14 = compute_profile_confidence(14)
    confidence_60 = compute_profile_confidence(60)
    confidence_200 = compute_profile_confidence(200)

    assert 0.50 < confidence_14 < 0.52
    assert 0.77 < confidence_60 < 0.78
    assert confidence_200 == 1.0


def test_compute_profile_confidence_clamps_negative_counts() -> None:
    assert compute_profile_confidence(-5) == 0.0
