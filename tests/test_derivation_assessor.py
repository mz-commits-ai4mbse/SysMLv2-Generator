from modules.mapping.derivation_assessor import detect_evidence_types


def test_detect_evidence_types_for_example_streaming_text():
    text = "The microscope operator starts a session. The system shall prevent two users from controlling it."
    evidence = detect_evidence_types(text)
    assert "EV_USER_ROLE" in evidence
    assert "EV_REQUIREMENT_STATEMENT" in evidence
    assert "EV_FUNCTION_OR_CAPABILITY" in evidence
