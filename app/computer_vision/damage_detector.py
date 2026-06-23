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
    if settings.vision_is_real:
        return _detect_with_azure(image_bytes_list)
    return _detect_mock(image_bytes_list)


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
