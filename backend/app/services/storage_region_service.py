"""
=========================================================================
StorageRegionService — MinIO/S3 regional bucket routing (ADR-063)
SDLC Orchestrator — Sprint 186 (Multi-Region Data Residency)

Version: 1.0.0
Date: 2026-02-20
Status: ACTIVE — Sprint 186 P0
Authority: CTO Approved (ADR-063, Expert 5 de-scope)

Purpose:
- Map project.data_region → MinIO endpoint + bucket name
- Provide a boto3 S3 client pre-configured for the correct region
- Storage-level residency only (DB remains single-region Vietnam primary)

Architecture (Expert 5 de-scope):
  data_region = 'VN'  → minio-vn.internal:9000 / sdlc-evidence-vn
  data_region = 'EU'  → minio-eu.internal:9000 / sdlc-evidence-eu  (Frankfurt)
  data_region = 'US'  → minio-us.internal:9000 / sdlc-evidence-us  (future)

AGPL Containment:
  Uses boto3 (Apache 2.0) for S3-compatible MinIO access.
  Never imports the MinIO SDK (AGPL).

Zero Mock Policy: Real boto3 clients, real env-configured endpoints.
=========================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import boto3
from botocore.config import Config as BotocoreConfig

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Region type alias
# ---------------------------------------------------------------------------

DataRegion = Literal["VN", "EU", "US"]

_VALID_REGIONS: frozenset[str] = frozenset({"VN", "EU", "US"})


# ---------------------------------------------------------------------------
# Regional endpoint configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegionConfig:
    """Immutable configuration for a MinIO/S3 storage region."""

    region: str          # Canonical region code (VN | EU | US)
    endpoint_url: str    # MinIO endpoint URL
    bucket: str          # Evidence bucket name for this region
    aws_region: str      # boto3 region_name (cosmetic for S3 signing)


def _build_region_configs() -> dict[str, RegionConfig]:
    """Build region → config mapping from environment variables.

    Environment variables (all optional — fall back to defaults for local dev):
      MINIO_VN_ENDPOINT  (default: http://minio:9000)
      MINIO_EU_ENDPOINT  (default: http://minio-eu:9000)
      MINIO_US_ENDPOINT  (default: http://minio-us:9000)
      MINIO_VN_BUCKET    (default: sdlc-evidence-vn)
      MINIO_EU_BUCKET    (default: sdlc-evidence-eu)
      MINIO_US_BUCKET    (default: sdlc-evidence-us)
    """
    import os

    return {
        "VN": RegionConfig(
            region="VN",
            endpoint_url=os.getenv("MINIO_VN_ENDPOINT", "http://minio:9000"),
            bucket=os.getenv("MINIO_VN_BUCKET", "sdlc-evidence-vn"),
            aws_region="ap-southeast-1",
        ),
        "EU": RegionConfig(
            region="EU",
            endpoint_url=os.getenv("MINIO_EU_ENDPOINT", "http://minio-eu:9000"),
            bucket=os.getenv("MINIO_EU_BUCKET", "sdlc-evidence-eu"),
            aws_region="eu-central-1",
        ),
        "US": RegionConfig(
            region="US",
            endpoint_url=os.getenv("MINIO_US_ENDPOINT", "http://minio-us:9000"),
            bucket=os.getenv("MINIO_US_BUCKET", "sdlc-evidence-us"),
            aws_region="us-east-1",
        ),
    }


# Module-level cache — initialised once per process
_REGION_CONFIGS: dict[str, RegionConfig] = _build_region_configs()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class StorageRegionService:
    """
    Routes MinIO/S3 storage operations to the correct regional endpoint
    based on project.data_region.

    Usage:
        svc = StorageRegionService()
        config = svc.get_region_config("EU")
        client = svc.get_s3_client("EU")
        client.upload_fileobj(f, config.bucket, "evidence/key.txt")
    """

    def get_region_config(self, data_region: str) -> RegionConfig:
        """
        Return the RegionConfig for the given data_region code.

        Args:
            data_region: One of 'VN', 'EU', 'US' (case-sensitive).

        Returns:
            RegionConfig with endpoint, bucket, and aws_region.

        Raises:
            ValueError: If data_region is not a recognised value.
        """
        region = data_region.upper()
        config = _REGION_CONFIGS.get(region)
        if config is None:
            raise ValueError(
                f"Unknown data_region '{data_region}'. "
                f"Valid values: {sorted(_VALID_REGIONS)}"
            )
        return config

    def get_s3_client(self, data_region: str):  # type: ignore[return]
        """
        Return a boto3 S3 client pre-configured for the given region's
        MinIO endpoint.

        AGPL-safe: uses boto3 (Apache 2.0) with endpoint_url pointed at
        the MinIO S3-compatible API. Never imports the MinIO SDK.

        Args:
            data_region: One of 'VN', 'EU', 'US'.

        Returns:
            boto3 S3 client configured for regional MinIO endpoint.
        """
        config = self.get_region_config(data_region)

        client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=getattr(settings, "MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=getattr(settings, "MINIO_SECRET_KEY", "minioadmin"),
            region_name=config.aws_region,
            config=BotocoreConfig(
                # Disable SSL cert validation for self-signed MinIO certs in dev/staging
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )

        logger.debug(
            "StorageRegionService.get_s3_client: region=%s endpoint=%s bucket=%s",
            config.region,
            config.endpoint_url,
            config.bucket,
        )
        return client

    def resolve_bucket(self, data_region: str) -> str:
        """Return the bucket name for the given region (convenience wrapper)."""
        return self.get_region_config(data_region).bucket

    def resolve_endpoint(self, data_region: str) -> str:
        """Return the MinIO endpoint URL for the given region."""
        return self.get_region_config(data_region).endpoint_url

    def list_available_regions(self) -> list[dict]:
        """
        Return metadata for all configured storage regions.

        Used by the data residency API to advertise available regions.
        """
        return [
            {
                "region": cfg.region,
                "endpoint_url": cfg.endpoint_url,
                "bucket": cfg.bucket,
                "aws_region": cfg.aws_region,
            }
            for cfg in _REGION_CONFIGS.values()
        ]
