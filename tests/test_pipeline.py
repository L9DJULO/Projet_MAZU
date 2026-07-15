from __future__ import annotations

from types import SimpleNamespace

from app.agents import OrchestratorAgent
from app.computer_vision import detect_damages
from app.computer_vision import damage_detector
from app.machine_learning import estimate_market_value, estimate_repair_cost
from app.models.schemas import InspectionReport, VehicleInfo

VEHICLE = VehicleInfo(
    make="Renault", model="Clio", year=2017, mileage_km=98000, vin="VF1RFA00123456789"
)
IMAGES = [b"photo-avant", b"photo-arriere"]


def test_vision_is_deterministic():
    r1 = detect_damages(IMAGES)
    r2 = detect_damages(IMAGES)
    assert r1.model_dump() == r2.model_dump()
    assert r1.provider == "mock"
    assert r1.images_analyzed == 2


def test_repair_cost_positive():
    vision = detect_damages(IMAGES)
    cost = estimate_repair_cost(vision.damages, VEHICLE)
    assert cost.total_repair_cost >= 0
    assert len(cost.repair_lines) == len(vision.damages)


def test_market_value_within_bounds():
    vision = detect_damages(IMAGES)
    cost = estimate_repair_cost(vision.damages, VEHICLE)
    val = estimate_market_value(VEHICLE, condition_score=70, cost_estimate=cost)
    assert val.adjusted_value > 0
    assert 0.55 <= val.condition_factor <= 1.0


def test_full_orchestration():
    report, trace = OrchestratorAgent().run(VEHICLE, IMAGES)
    assert isinstance(report, InspectionReport)
    assert report.executive_summary
    assert report.negotiation.recommended_offer <= report.negotiation.fair_value
    assert report.mechanical.condition_score >= 0
    agents_seen = {step["agent"] for step in trace}
    assert {"orchestrateur", "evaluation", "negociation", "rapport"} <= agents_seen


def test_premium_make_costs_more():
    vision = detect_damages([b"identique"])
    bmw = VehicleInfo(make="BMW", model="X", year=2017, mileage_km=98000)
    renault = VehicleInfo(make="Renault", model="X", year=2017, mileage_km=98000)
    assert (
        estimate_repair_cost(vision.damages, bmw).total_repair_cost
        >= estimate_repair_cost(vision.damages, renault).total_repair_cost
    )


def test_custom_vision_classify_maps_condition(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "predictions": [
                    {"tagName": "Good", "probability": 0.18},
                    {"tagName": "Destroyed", "probability": 0.82},
                ]
            }

    def fake_post(url, headers, content, timeout):
        calls.append((url, headers, content, timeout))
        return FakeResponse()

    monkeypatch.setattr(
        damage_detector,
        "get_settings",
        lambda: SimpleNamespace(
            custom_vision_endpoint="https://example.cognitiveservices.azure.com/",
            custom_vision_key="prediction-key",
            custom_vision_project_id="project-id",
            custom_vision_iteration="Iteration1",
            custom_vision_mode="classify",
        ),
    )
    monkeypatch.setattr("httpx.post", fake_post)

    result = damage_detector._detect_with_custom_vision([b"image-bytes"])

    assert calls[0][0] == (
        "https://example.cognitiveservices.azure.com/customvision/v3.0/"
        "Prediction/project-id/classify/iterations/Iteration1/image"
    )
    assert calls[0][1]["Prediction-Key"] == "prediction-key"
    assert result.provider == "azure_custom_vision_classify"
    assert result.condition_score == 18
    assert result.total_loss is True
    assert len(result.damages) == 1
