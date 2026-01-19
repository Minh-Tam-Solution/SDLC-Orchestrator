"""
=========================================================================
Evidence Manifest Service - Ed25519 Signed Hash Chain (Sprint 79)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 79 (Pre-Launch Hardening)
Authority: CTO + Security Lead Approved
Foundation: Expert Feedback (Expert 6), SPRINT-79-PRE-LAUNCH-HARDENING.md
Framework: SDLC 5.1.3 (7-Pillar Architecture)

Purpose:
- Tamper-evident manifest for Evidence Vault
- Ed25519 asymmetric signing for non-repudiation
- Hash chain linking for sequential integrity
- GDPR-compliant anonymization support

Why Ed25519 (not HMAC-SHA256):
- Asymmetric: Public key for verification, private key for signing
- Non-repudiation: Only server with private key can sign
- Auditable: Anyone with public key can verify
- Industry standard: Used by SSH, TLS 1.3, cryptocurrency

Expert 6 Feedback (Jan 19, 2026):
"HMAC with shared secret = anyone with secret can forge signatures.
 Ed25519 = only server signs, anyone can verify = TRUE non-repudiation."

Zero Mock Policy: 100% real implementation (cryptography library)
=========================================================================
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Models
# ============================================================================


class ArtifactEntry(BaseModel):
    """Single artifact entry in manifest."""
    artifact_id: UUID
    file_path: str
    sha256_hash: str
    size_bytes: int
    content_type: str
    uploaded_at: datetime
    uploaded_by: UUID
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceManifest(BaseModel):
    """
    Tamper-evident manifest for Evidence Vault.

    Design:
    1. Each artifact gets SHA256 hash stored in manifest
    2. Manifest includes previous_manifest_hash (chain linking)
    3. Manifest is signed with Ed25519 private key
    4. Anyone can verify with public key (non-repudiation)
    """
    manifest_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    sequence_number: int  # Monotonically increasing
    artifacts: list[ArtifactEntry]
    previous_manifest_hash: Optional[str] = None  # Hash chain linking
    manifest_hash: Optional[str] = None  # SHA256 of manifest content
    signature: Optional[str] = None  # Ed25519 signature
    signer_key_id: Optional[str] = None  # Public key ID for verification
    signing_algorithm: str = "Ed25519"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        """Compute SHA256 hash of manifest content (excluding signature fields)."""
        content = {
            "manifest_id": str(self.manifest_id),
            "project_id": str(self.project_id),
            "sequence_number": self.sequence_number,
            "artifacts": [
                {
                    "artifact_id": str(a.artifact_id),
                    "file_path": a.file_path,
                    "sha256_hash": a.sha256_hash,
                    "size_bytes": a.size_bytes,
                    "content_type": a.content_type,
                    "uploaded_at": a.uploaded_at.isoformat(),
                    "uploaded_by": str(a.uploaded_by),
                    "metadata": a.metadata,
                }
                for a in self.artifacts
            ],
            "previous_manifest_hash": self.previous_manifest_hash,
            "created_at": self.created_at.isoformat(),
        }
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content_json.encode("utf-8")).hexdigest()


class ManifestVerificationResult(BaseModel):
    """Result of manifest verification."""
    is_valid: bool
    manifest_id: UUID
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Custom Exceptions
# ============================================================================


class EvidenceManifestError(Exception):
    """Base exception for Evidence Manifest errors."""
    pass


class ManifestSigningError(EvidenceManifestError):
    """Exception raised when manifest signing fails."""
    pass


class ManifestVerificationError(EvidenceManifestError):
    """Exception raised when manifest verification fails."""
    pass


class HashChainBrokenError(EvidenceManifestError):
    """Exception raised when hash chain integrity is broken."""
    pass


# ============================================================================
# Key Storage Service
# ============================================================================


class KeyStorageService:
    """
    Manage Ed25519 key pairs for manifest signing.

    In production:
    - Private keys stored in HSM or HashiCorp Vault
    - Public keys stored in database for verification
    - Key rotation policy: Annual rotation with 90-day overlap

    For development:
    - Keys stored in environment variables or files
    - Self-signed keys acceptable
    """

    def __init__(self):
        """Initialize key storage."""
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._key_id: Optional[str] = None

    def load_keys_from_env(self) -> None:
        """
        Load Ed25519 keys from environment variables.

        Expected format:
        - EVIDENCE_SIGNING_PRIVATE_KEY: Base64-encoded Ed25519 private key
        - EVIDENCE_SIGNING_PUBLIC_KEY: Base64-encoded Ed25519 public key
        - EVIDENCE_SIGNING_KEY_ID: Unique identifier for this key pair
        """
        import base64
        import os

        private_key_b64 = os.getenv("EVIDENCE_SIGNING_PRIVATE_KEY")
        public_key_b64 = os.getenv("EVIDENCE_SIGNING_PUBLIC_KEY")
        key_id = os.getenv("EVIDENCE_SIGNING_KEY_ID", "default-key-v1")

        if private_key_b64:
            self._private_key = base64.b64decode(private_key_b64)
        if public_key_b64:
            self._public_key = base64.b64decode(public_key_b64)
        self._key_id = key_id

        if self._private_key:
            logger.info(f"Loaded signing keys: key_id={key_id}")
        else:
            logger.warning("No signing keys configured. Manifests will be unsigned.")

    def generate_key_pair(self) -> tuple[bytes, bytes, str]:
        """
        Generate new Ed25519 key pair.

        Returns:
            Tuple of (private_key_bytes, public_key_bytes, key_id)

        Note: In production, use HSM or Vault for key generation.
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey,
            )
            from cryptography.hazmat.primitives import serialization

            private_key = Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            key_id = f"key-{uuid4().hex[:8]}"

            return private_bytes, public_bytes, key_id

        except ImportError:
            raise EvidenceManifestError(
                "cryptography library not installed. Run: pip install cryptography"
            )

    def get_private_key(self) -> Optional[bytes]:
        """Get private key for signing."""
        return self._private_key

    def get_public_key(self) -> Optional[bytes]:
        """Get public key for verification."""
        return self._public_key

    def get_key_id(self) -> Optional[str]:
        """Get current key ID."""
        return self._key_id


# ============================================================================
# Evidence Manifest Service
# ============================================================================


class EvidenceManifestService:
    """
    Service for creating and verifying tamper-evident evidence manifests.

    Features:
    1. SHA256 hash per artifact
    2. Hash chain linking manifests
    3. Ed25519 asymmetric signing
    4. Verification with public key only

    Usage:
        manifest_service = EvidenceManifestService()

        # Create new manifest
        manifest = manifest_service.create_manifest(
            project_id=project_id,
            artifacts=artifacts,
            previous_manifest=prev_manifest,
        )

        # Verify manifest
        result = manifest_service.verify_manifest(manifest)
        if not result.is_valid:
            raise TamperDetectedError(result.errors)

        # Verify hash chain
        chain_valid = manifest_service.verify_chain(manifests)
    """

    def __init__(self, key_storage: Optional[KeyStorageService] = None):
        """
        Initialize Evidence Manifest service.

        Args:
            key_storage: Optional key storage service (default: create new)
        """
        self.key_storage = key_storage or KeyStorageService()
        self.key_storage.load_keys_from_env()
        logger.info("Evidence Manifest service initialized")

    def create_manifest(
        self,
        project_id: UUID,
        artifacts: list[ArtifactEntry],
        sequence_number: int,
        previous_manifest: Optional[EvidenceManifest] = None,
    ) -> EvidenceManifest:
        """
        Create new signed manifest.

        Args:
            project_id: Project UUID
            artifacts: List of artifact entries to include
            sequence_number: Monotonically increasing sequence number
            previous_manifest: Previous manifest for chain linking

        Returns:
            Signed EvidenceManifest

        Raises:
            ManifestSigningError: If signing fails
        """
        # Determine previous manifest hash for chain linking
        previous_hash = None
        if previous_manifest:
            previous_hash = previous_manifest.manifest_hash

        # Create manifest
        manifest = EvidenceManifest(
            project_id=project_id,
            sequence_number=sequence_number,
            artifacts=artifacts,
            previous_manifest_hash=previous_hash,
        )

        # Compute manifest hash
        manifest.manifest_hash = manifest.compute_hash()

        # Sign with Ed25519
        self._sign_manifest(manifest)

        logger.info(
            f"Created manifest {manifest.manifest_id} with {len(artifacts)} artifacts, "
            f"seq={sequence_number}, signed={manifest.signature is not None}"
        )

        return manifest

    def verify_manifest(self, manifest: EvidenceManifest) -> ManifestVerificationResult:
        """
        Verify manifest integrity and signature.

        Checks:
        1. Manifest hash matches computed hash (content integrity)
        2. Signature is valid (Ed25519 verification)
        3. Signing key ID is known

        Args:
            manifest: Manifest to verify

        Returns:
            ManifestVerificationResult with is_valid and any errors
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check 1: Hash integrity
        computed_hash = manifest.compute_hash()
        if manifest.manifest_hash != computed_hash:
            errors.append(
                f"Hash mismatch: stored={manifest.manifest_hash}, "
                f"computed={computed_hash}"
            )

        # Check 2: Signature verification
        if manifest.signature:
            try:
                self._verify_signature(manifest)
            except ManifestVerificationError as e:
                errors.append(f"Signature verification failed: {e}")
        else:
            warnings.append("Manifest is unsigned (acceptable for legacy manifests)")

        # Check 3: Key ID validation
        if manifest.signer_key_id:
            known_key_id = self.key_storage.get_key_id()
            if known_key_id and manifest.signer_key_id != known_key_id:
                warnings.append(
                    f"Signed with different key: {manifest.signer_key_id} "
                    f"(current: {known_key_id})"
                )

        is_valid = len(errors) == 0

        return ManifestVerificationResult(
            is_valid=is_valid,
            manifest_id=manifest.manifest_id,
            errors=errors,
            warnings=warnings,
        )

    def verify_chain(
        self,
        manifests: list[EvidenceManifest],
    ) -> ManifestVerificationResult:
        """
        Verify hash chain integrity across manifests.

        Ensures:
        1. Sequence numbers are monotonically increasing
        2. Each manifest's previous_hash matches prior manifest's hash
        3. No gaps in sequence

        Args:
            manifests: List of manifests in order (oldest first)

        Returns:
            ManifestVerificationResult for chain verification
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not manifests:
            return ManifestVerificationResult(
                is_valid=True,
                manifest_id=uuid4(),  # Placeholder
                warnings=["Empty manifest chain"],
            )

        # Sort by sequence number
        sorted_manifests = sorted(manifests, key=lambda m: m.sequence_number)

        for i, manifest in enumerate(sorted_manifests):
            # Check individual manifest
            individual_result = self.verify_manifest(manifest)
            errors.extend(individual_result.errors)
            warnings.extend(individual_result.warnings)

            # Check chain linking
            if i > 0:
                prev_manifest = sorted_manifests[i - 1]

                # Check sequence continuity
                expected_seq = prev_manifest.sequence_number + 1
                if manifest.sequence_number != expected_seq:
                    errors.append(
                        f"Sequence gap at manifest {manifest.manifest_id}: "
                        f"expected {expected_seq}, got {manifest.sequence_number}"
                    )

                # Check hash chain
                if manifest.previous_manifest_hash != prev_manifest.manifest_hash:
                    errors.append(
                        f"Hash chain broken at manifest {manifest.manifest_id}: "
                        f"previous_hash={manifest.previous_manifest_hash}, "
                        f"expected={prev_manifest.manifest_hash}"
                    )
            else:
                # First manifest should have no previous
                if manifest.previous_manifest_hash is not None:
                    warnings.append(
                        f"First manifest {manifest.manifest_id} has previous_hash "
                        "(expected None)"
                    )

        is_valid = len(errors) == 0

        return ManifestVerificationResult(
            is_valid=is_valid,
            manifest_id=sorted_manifests[-1].manifest_id if sorted_manifests else uuid4(),
            errors=errors,
            warnings=warnings,
        )

    def anonymize_manifest(
        self,
        manifest: EvidenceManifest,
        user_id_mapping: dict[UUID, str],
    ) -> EvidenceManifest:
        """
        Anonymize user IDs in manifest for GDPR compliance.

        Per GDPR Right to Erasure: We anonymize rather than delete
        to preserve audit trail integrity.

        Args:
            manifest: Manifest to anonymize
            user_id_mapping: Map of user_id -> anonymized_id

        Returns:
            Anonymized manifest (new instance, original unchanged)
        """
        anonymized_artifacts = []
        for artifact in manifest.artifacts:
            anon_user_id = user_id_mapping.get(
                artifact.uploaded_by,
                UUID("00000000-0000-0000-0000-000000000000"),  # Fallback
            )
            anonymized_artifacts.append(
                ArtifactEntry(
                    artifact_id=artifact.artifact_id,
                    file_path=artifact.file_path,
                    sha256_hash=artifact.sha256_hash,
                    size_bytes=artifact.size_bytes,
                    content_type=artifact.content_type,
                    uploaded_at=artifact.uploaded_at,
                    uploaded_by=anon_user_id if isinstance(anon_user_id, UUID) else UUID(anon_user_id),
                    metadata={
                        k: v for k, v in artifact.metadata.items()
                        if k not in ["user_email", "user_name", "ip_address"]
                    },
                )
            )

        # Create new manifest with anonymized data
        # Note: We preserve the hash and signature for integrity
        anonymized = EvidenceManifest(
            manifest_id=manifest.manifest_id,
            project_id=manifest.project_id,
            sequence_number=manifest.sequence_number,
            artifacts=anonymized_artifacts,
            previous_manifest_hash=manifest.previous_manifest_hash,
            manifest_hash=manifest.manifest_hash,  # Keep original hash
            signature=manifest.signature,  # Keep original signature
            signer_key_id=manifest.signer_key_id,
            signing_algorithm=manifest.signing_algorithm,
            created_at=manifest.created_at,
        )

        logger.info(
            f"Anonymized manifest {manifest.manifest_id} "
            f"({len(user_id_mapping)} users anonymized)"
        )

        return anonymized

    # ============================================================================
    # Private Methods
    # ============================================================================

    def _sign_manifest(self, manifest: EvidenceManifest) -> None:
        """
        Sign manifest with Ed25519 private key.

        Args:
            manifest: Manifest to sign (modified in-place)

        Raises:
            ManifestSigningError: If signing fails
        """
        private_key_bytes = self.key_storage.get_private_key()
        if not private_key_bytes:
            logger.warning("No private key available, manifest will be unsigned")
            return

        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey,
            )
            import base64

            private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)

            # Sign the manifest hash
            message = manifest.manifest_hash.encode("utf-8")
            signature = private_key.sign(message)

            manifest.signature = base64.b64encode(signature).decode("utf-8")
            manifest.signer_key_id = self.key_storage.get_key_id()

        except ImportError:
            raise ManifestSigningError(
                "cryptography library not installed. Run: pip install cryptography"
            )
        except Exception as e:
            raise ManifestSigningError(f"Signing failed: {e}")

    def _verify_signature(self, manifest: EvidenceManifest) -> None:
        """
        Verify Ed25519 signature on manifest.

        Args:
            manifest: Manifest to verify

        Raises:
            ManifestVerificationError: If verification fails
        """
        public_key_bytes = self.key_storage.get_public_key()
        if not public_key_bytes:
            raise ManifestVerificationError("No public key available for verification")

        if not manifest.signature:
            raise ManifestVerificationError("Manifest has no signature")

        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
            from cryptography.exceptions import InvalidSignature
            import base64

            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

            message = manifest.manifest_hash.encode("utf-8")
            signature = base64.b64decode(manifest.signature)

            public_key.verify(signature, message)

        except InvalidSignature:
            raise ManifestVerificationError("Invalid signature")
        except ImportError:
            raise ManifestVerificationError(
                "cryptography library not installed. Run: pip install cryptography"
            )
        except Exception as e:
            raise ManifestVerificationError(f"Verification failed: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

evidence_manifest_service = EvidenceManifestService()
