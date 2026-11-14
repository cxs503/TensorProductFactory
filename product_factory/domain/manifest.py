from dataclasses import dataclass
from enum import StrEnum


class RightsStatus(StrEnum):
    UNKNOWN = "unknown"
    PENDING = "pending"
    CLEARED = "cleared"
    RESTRICTED = "restricted"
    EXPIRED = "expired"


@dataclass(frozen=True)
class AssetEntry:
    asset_id: str
    version: str
    role: str
    uri: str
    sha256: str
    source_ref: str
    rights_status: RightsStatus
    required: bool = True

    def __post_init__(self) -> None:
        for key in ("asset_id", "version", "role", "uri", "source_ref"):
            if not getattr(self, key).strip():
                raise ValueError(f"{key} must not be empty")
        digest = self.sha256.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")


@dataclass(frozen=True)
class ProductManifest:
    manifest_id: str
    product_id: str
    product_version: str
    assets: tuple[AssetEntry, ...]

    def __post_init__(self) -> None:
        if not all((self.manifest_id, self.product_id, self.product_version)):
            raise ValueError("manifest and product identifiers are required")
        ids = [asset.asset_id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("asset_id values must be unique within a manifest")

    def release_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.assets:
            blockers.append("manifest has no assets")
        for asset in self.assets:
            if asset.required and asset.rights_status is not RightsStatus.CLEARED:
                blockers.append(f"required asset {asset.asset_id} rights are {asset.rights_status.value}")
        return tuple(blockers)
