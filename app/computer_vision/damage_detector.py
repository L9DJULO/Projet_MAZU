from __future__ import annotations

import hashlib
import random

from app.config import get_settings
from app.models.schemas import Damage, DamageType, Severity, VisionResult

_ZONES = [
    "pare-chocs avant", "pare-chocs arriere", "porte avant gauche",
    "porte avant droite", "porte arriere gauche", "porte arriere droite",
    "capot", "toit", "aile avant gauche", "aile arriere droite",
    "pneu avant gauche", "pneu arriere droit", "pare-brise",
]

_ZONE_DAMAGES = {
    "pneu": [DamageType.TIRE_WEAR],
    "pare-brise": [DamageType.CRACK, DamageType.BROKEN_GLASS],
    "_default": [DamageType.SCRATCH, DamageType.DENT, DamageType.RUST],
}


def detect_damages(image_bytes_list: list[bytes]) -> VisionResult:
    settings = get_settings()
    if settings.vision_is_local_http:
        return _detect_with_local_http(image_bytes_list)
    if settings.vision_is_real:
        if settings.vision_provider == "custom_vision":
            return _detect_with_custom_vision(image_bytes_list)
        return _detect_with_azure(image_bytes_list)
    return _detect_mock(image_bytes_list)


_GOOD_TAGS = {"good", "intact", "clean", "ok", "sain", "bon", "none"}
_BAD_HINTS = {
    "destroyed", "damaged", "damage", "bad", "poor", "accident", "broken",
    "dent", "scratch", "rust", "endommage", "abime", "casse", "epave",
}


def _detect_with_local_http(image_bytes_list: list[bytes]) -> VisionResult:
    import httpx

    settings = get_settings()
    base = settings.azure_vision_endpoint.rstrip("/")
    url = f"{base}/image"
    is_local = "localhost" in base or "127.0.0.1" in base

    damages: list[Damage] = []
    successes = 0
    damage_ratios: list[float] = []
    with httpx.Client(verify=not is_local, timeout=30) as client:
        for image_bytes in image_bytes_list:
            try:
                resp = client.post(
                    url,
                    content=image_bytes,
                    headers={"Content-Type": "application/octet-stream"},
                )
                resp.raise_for_status()
                predictions = resp.json().get("predictions", [])
            except Exception:
                continue
            successes += 1
            damage, ratio = _map_condition_prediction(predictions)
            damage_ratios.append(ratio)
            if damage is not None:
                damages.append(damage)

    if successes == 0:
        return _detect_mock(image_bytes_list)

    # Verdict d'etat global : on retient l'image la plus degradee (pire cas),
    # car une seule photo d'epave suffit a qualifier le vehicule.
    worst_ratio = max(damage_ratios) if damage_ratios else 0.0
    condition_score = int(round(100 * (1 - worst_ratio)))
    total_loss = worst_ratio >= 0.75

    return VisionResult(
        damages=damages,
        images_analyzed=len(image_bytes_list),
        provider="local_http",
        condition_score=condition_score,
        total_loss=total_loss,
    )


def _map_condition_prediction(predictions: list[dict]) -> tuple[Damage | None, float]:
    """Retourne (dommage representatif | None, ratio de degradation 0..1)."""
    if not predictions:
        return None, 0.0

    top = max(predictions, key=lambda p: p.get("probability", 0.0))
    top_tag = str(top.get("tagName", "")).strip() or "inconnu"

    good_prob = max(
        (p.get("probability", 0.0) for p in predictions
         if str(p.get("tagName", "")).lower() in _GOOD_TAGS),
        default=0.0,
    )
    bad_prob = max(
        (p.get("probability", 0.0) for p in predictions
         if any(h in str(p.get("tagName", "")).lower() for h in _BAD_HINTS)),
        default=0.0,
    )

    if bad_prob > 0:
        score = bad_prob
    elif good_prob > 0:
        score = 1.0 - good_prob
    else:
        score = top.get("probability", 0.0)

    ratio = round(float(min(max(score, 0.0), 1.0)), 4)

    if score < 0.35:
        return None, ratio
    if score < 0.6:
        severity = Severity.MINOR
    elif score < 0.8:
        severity = Severity.MODERATE
    else:
        severity = Severity.SEVERE

    damage = Damage(
        type=DamageType.DENT,
        severity=severity,
        location=f"etat carrosserie (classe '{top_tag}')",
        confidence=round(float(score), 2),
        bounding_box=None,
    )
    return damage, ratio


def _seed_from_images(image_bytes_list: list[bytes]) -> int:
    h = hashlib.sha256()
    for b in image_bytes_list:
        h.update(b)
    if not image_bytes_list:
        h.update(b"empty")
    return int.from_bytes(h.digest()[:8], "big")


def _damage_for_zone(zone: str, rng: random.Random) -> Damage:
    if "pneu" in zone:
        candidates = _ZONE_DAMAGES["pneu"]
    elif "pare-brise" in zone:
        candidates = _ZONE_DAMAGES["pare-brise"]
    else:
        candidates = _ZONE_DAMAGES["_default"]

    dtype = rng.choice(candidates)
    severity = rng.choices(
        [Severity.MINOR, Severity.MODERATE, Severity.SEVERE],
        weights=[0.5, 0.35, 0.15],
    )[0]
    confidence = round(rng.uniform(0.62, 0.97), 2)
    x, y = rng.randint(0, 400), rng.randint(0, 300)
    w, h = rng.randint(40, 200), rng.randint(40, 200)
    return Damage(
        type=dtype,
        severity=severity,
        location=zone,
        confidence=confidence,
        bounding_box=[x, y, w, h],
    )


def _detect_mock(image_bytes_list: list[bytes]) -> VisionResult:
    rng = random.Random(_seed_from_images(image_bytes_list))
    n_images = max(1, len(image_bytes_list))

    n_damages = min(len(_ZONES), rng.randint(n_images, n_images * 3))
    zones = rng.sample(_ZONES, k=n_damages)
    damages = [_damage_for_zone(z, rng) for z in zones]

    return VisionResult(
        damages=damages,
        images_analyzed=n_images,
        provider="mock",
    )


def _detect_with_azure(image_bytes_list: list[bytes]) -> VisionResult:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential

    settings = get_settings()
    client = ImageAnalysisClient(
        endpoint=settings.azure_vision_endpoint,
        credential=AzureKeyCredential(settings.azure_vision_key),
    )

    damages: list[Damage] = []
    for image_bytes in image_bytes_list:
        result = client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.OBJECTS, VisualFeatures.TAGS],
        )
        damages.extend(_map_azure_objects(result))

    return VisionResult(
        damages=damages,
        images_analyzed=len(image_bytes_list),
        provider="azure",
    )


def _detect_with_custom_vision(image_bytes_list: list[bytes]) -> VisionResult:
    import httpx

    settings = get_settings()
    url = (
        f"{settings.custom_vision_endpoint}/customvision/v3.0/Prediction/"
        f"{settings.custom_vision_project_id}/detect/iterations/"
        f"{settings.custom_vision_iteration}/image"
    )
    headers = {
        "Prediction-Key": settings.custom_vision_key,
        "Content-Type": "application/octet-stream",
    }

    damages: list[Damage] = []
    for image_bytes in image_bytes_list:
        resp = httpx.post(url, headers=headers, content=image_bytes, timeout=30)
        resp.raise_for_status()
        for pred in resp.json().get("predictions", []):
            if pred.get("probability", 0) < 0.5:
                continue
            damages.append(_map_custom_vision_prediction(pred))

    return VisionResult(
        damages=damages,
        images_analyzed=len(image_bytes_list),
        provider="azure_custom_vision",
    )


def _map_custom_vision_prediction(pred: dict) -> Damage:
    name = pred.get("tagName", "").lower()
    type_map = {
        "scratch": DamageType.SCRATCH, "rayure": DamageType.SCRATCH,
        "dent": DamageType.DENT, "bosse": DamageType.DENT,
        "crack": DamageType.CRACK, "fissure": DamageType.CRACK,
        "rust": DamageType.RUST, "corrosion": DamageType.RUST,
        "tire": DamageType.TIRE_WEAR, "pneu": DamageType.TIRE_WEAR,
        "glass": DamageType.BROKEN_GLASS, "vitre": DamageType.BROKEN_GLASS,
    }
    dtype = DamageType.SCRATCH
    for key, value in type_map.items():
        if key in name:
            dtype = value
            break

    prob = pred.get("probability", 0.0)
    severity = Severity.SEVERE if prob > 0.85 else Severity.MODERATE if prob > 0.65 else Severity.MINOR

    box = pred.get("boundingBox", {})
    bbox = None
    if box:
        bbox = [
            int(box.get("left", 0) * 1000),
            int(box.get("top", 0) * 1000),
            int(box.get("width", 0) * 1000),
            int(box.get("height", 0) * 1000),
        ]

    return Damage(
        type=dtype,
        severity=severity,
        location=pred.get("tagName", "zone detectee"),
        confidence=round(prob, 2),
        bounding_box=bbox,
    )


def _map_azure_objects(result) -> list[Damage]:
    keyword_map = {
        "scratch": DamageType.SCRATCH,
        "dent": DamageType.DENT,
        "crack": DamageType.CRACK,
        "rust": DamageType.RUST,
        "tire": DamageType.TIRE_WEAR,
        "glass": DamageType.BROKEN_GLASS,
    }
    out: list[Damage] = []
    objects = getattr(result, "objects", None)
    if not objects or not getattr(objects, "list", None):
        return out
    for obj in objects.list:
        for tag in obj.tags:
            name = tag.name.lower()
            for key, dtype in keyword_map.items():
                if key in name:
                    box = obj.bounding_box
                    out.append(
                        Damage(
                            type=dtype,
                            severity=Severity.MODERATE,
                            location="zone detectee",
                            confidence=round(tag.confidence, 2),
                            bounding_box=[box.x, box.y, box.width, box.height],
                        )
                    )
                    break
    return out
