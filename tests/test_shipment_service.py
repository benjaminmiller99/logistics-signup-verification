from src.shipment_service import LogisticsSignup


def test_exception_event_is_visible_and_keeps_proof_record():
    service = LogisticsSignup(client=None)
    shipment = service.record_event("S-42", "ops@example.com", "exception", "Leipzig")
    service.attach_proof("S-42", "pod.jpg")
    assert shipment.exception == "delivery exception at Leipzig"
    assert shipment.proof_files == ["pod.jpg"]
