"""Plugin signing and verification utilities.

This module provides tools for signing and verifying plugin packages
to ensure their authenticity and integrity.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage


@dataclass
class SigningKey:
    """Key pair for signing and verifying plugins.

    Attributes:
        name: Name of the key
        private_key: Private key (used for signing)
        public_key: Public key (used for verification)
        created_at: When the key was created
        fingerprint: Key fingerprint
    """

    name: str
    private_key: Optional[bytes]
    public_key: bytes
    created_at: datetime.datetime
    fingerprint: str


class SigningError(Exception):
    """Exception raised for errors in plugin signing."""

    pass


class VerificationError(Exception):
    """Exception raised for errors in plugin verification."""

    pass


class PluginSigner:
    """Tool for signing plugin packages.

    This class provides methods for generating signing keys
    and signing plugin packages.

    Attributes:
        key: Signing key
    """

    def __init__(self, key: Optional[SigningKey] = None) -> None:
        """Initialize a plugin signer.

        Args:
            key: Signing key to use (if None, a new key will be generated)
        """
        self.key = key or self.generate_key("qorzen-plugin-signer")

    @staticmethod
    def generate_key(name: str) -> SigningKey:
        """Generate a new signing key.

        Args:
            name: Name for the key

        Returns:
            Generated signing key

        Raises:
            SigningError: If key generation fails
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa, padding
            from cryptography.hazmat.primitives import hashes, serialization

            # Generate a private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Get the public key
            public_key = private_key.public_key()

            # Serialize keys
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Calculate fingerprint
            fingerprint = hashlib.sha256(public_bytes).hexdigest()

            return SigningKey(
                name=name,
                private_key=private_bytes,
                public_key=public_bytes,
                created_at=datetime.datetime.now(),
                fingerprint=fingerprint
            )

        except ImportError:
            raise SigningError("Required dependencies not installed. Install with 'pip install cryptography'")
        except Exception as e:
            raise SigningError(f"Failed to generate signing key: {e}")

    @staticmethod
    def load_key(path: Union[str, Path]) -> SigningKey:
        """Load a signing key from a file.

        Args:
            path: Path to the key file

        Returns:
            Loaded signing key

        Raises:
            SigningError: If key loading fails
        """
        path = Path(path)
        if not path.exists():
            raise SigningError(f"Key file not found: {path}")

        try:
            with open(path, "r") as f:
                key_data = json.load(f)

            if "private_key" in key_data and key_data["private_key"]:
                private_key = base64.b64decode(key_data["private_key"])
            else:
                private_key = None

            public_key = base64.b64decode(key_data["public_key"])

            return SigningKey(
                name=key_data["name"],
                private_key=private_key,
                public_key=public_key,
                created_at=datetime.datetime.fromisoformat(key_data["created_at"]),
                fingerprint=key_data["fingerprint"]
            )

        except Exception as e:
            raise SigningError(f"Failed to load signing key: {e}")

    def save_key(self, path: Union[str, Path], include_private: bool = False) -> None:
        """Save the signing key to a file.

        Args:
            path: Path where the key will be saved
            include_private: Whether to include the private key

        Raises:
            SigningError: If key saving fails
        """
        if not self.key:
            raise SigningError("No signing key available")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            key_data = {
                "name": self.key.name,
                "public_key": base64.b64encode(self.key.public_key).decode("ascii"),
                "created_at": self.key.created_at.isoformat(),
                "fingerprint": self.key.fingerprint
            }

            if include_private and self.key.private_key:
                key_data["private_key"] = base64.b64encode(self.key.private_key).decode("ascii")
            else:
                key_data["private_key"] = None

            with open(path, "w") as f:
                json.dump(key_data, f, indent=2)

        except Exception as e:
            raise SigningError(f"Failed to save signing key: {e}")

    def sign_manifest(self, manifest: PluginManifest) -> None:
        """Sign a plugin manifest.

        This adds a signature to the manifest that can be verified later.

        Args:
            manifest: Plugin manifest to sign

        Raises:
            SigningError: If signing fails
        """
        if not self.key or not self.key.private_key:
            raise SigningError("No private key available for signing")

        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes, serialization

            # Load the private key
            private_key = serialization.load_pem_private_key(
                self.key.private_key,
                password=None
            )

            # Create a copy of the manifest without the signature
            manifest_data = manifest.to_dict()
            manifest_data.pop("signature", None)

            # Serialize the manifest data
            manifest_bytes = json.dumps(manifest_data, sort_keys=True).encode("utf-8")

            # Sign the manifest
            signature = private_key.sign(
                manifest_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Add the signature to the manifest
            manifest.signature = base64.b64encode(signature).decode("ascii")

        except ImportError:
            raise SigningError("Required dependencies not installed. Install with 'pip install cryptography'")
        except Exception as e:
            raise SigningError(f"Failed to sign manifest: {e}")

    def sign_package(self, package: PluginPackage) -> None:
        """Sign a plugin package.

        This signs the package manifest and updates the package.

        Args:
            package: Plugin package to sign

        Raises:
            SigningError: If signing fails
        """
        if not package.manifest:
            raise SigningError("Package has no manifest")

        # Sign the manifest
        self.sign_manifest(package.manifest)

        # If the package is already extracted, update the manifest file
        if package._extracted_path and package._extracted_path.exists():
            manifest_path = package._extracted_path / PluginPackage.MANIFEST_PATH
            package.manifest.save(manifest_path)


class PluginVerifier:
    """Tool for verifying signed plugin packages.

    This class provides methods for verifying plugin signatures
    and managing trusted keys.

    Attributes:
        trusted_keys: List of trusted public keys for verification
    """

    def __init__(self, trusted_keys: Optional[List[SigningKey]] = None) -> None:
        """Initialize a plugin verifier.

        Args:
            trusted_keys: List of trusted keys for verification
        """
        self.trusted_keys = trusted_keys or []

    def add_trusted_key(self, key: SigningKey) -> None:
        """Add a trusted key for verification.

        Args:
            key: Key to add to the trusted keys list
        """
        # Check if the key is already trusted
        for existing_key in self.trusted_keys:
            if existing_key.fingerprint == key.fingerprint:
                return

        self.trusted_keys.append(key)

    def remove_trusted_key(self, fingerprint: str) -> bool:
        """Remove a trusted key.

        Args:
            fingerprint: Fingerprint of the key to remove

        Returns:
            True if the key was removed, False if not found
        """
        for i, key in enumerate(self.trusted_keys):
            if key.fingerprint == fingerprint:
                del self.trusted_keys[i]
                return True

        return False

    def load_trusted_keys(self, directory: Union[str, Path]) -> int:
        """Load trusted keys from a directory.

        Args:
            directory: Directory containing key files

        Returns:
            Number of keys loaded

        Raises:
            VerificationError: If key loading fails
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise VerificationError(f"Directory not found: {directory}")

        count = 0
        for file_path in directory.glob("*.json"):
            try:
                key = PluginSigner.load_key(file_path)
                self.add_trusted_key(key)
                count += 1
            except Exception as e:
                # Log the error but continue with other keys
                print(f"Failed to load key from {file_path}: {e}")

        return count

    def verify_manifest(self, manifest: PluginManifest) -> bool:
        """Verify a signed plugin manifest.

        Args:
            manifest: Plugin manifest to verify

        Returns:
            True if the manifest signature is valid, False otherwise

        Raises:
            VerificationError: If verification fails due to an error
        """
        if not manifest.signature:
            return False

        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.exceptions import InvalidSignature

            # Extract the signature
            signature = base64.b64decode(manifest.signature)

            # Create a copy of the manifest without the signature
            manifest_data = manifest.to_dict()
            manifest_data.pop("signature", None)

            # Serialize the manifest data
            manifest_bytes = json.dumps(manifest_data, sort_keys=True).encode("utf-8")

            # Try to verify with each trusted key
            for key in self.trusted_keys:
                try:
                    # Load the public key
                    public_key = serialization.load_pem_public_key(key.public_key)

                    # Verify the signature
                    public_key.verify(
                        signature,
                        manifest_bytes,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )

                    # If we get here, the signature is valid
                    return True

                except InvalidSignature:
                    # Try the next key
                    continue

            # If we get here, no key verified the signature
            return False

        except ImportError:
            raise VerificationError("Required dependencies not installed. Install with 'pip install cryptography'")
        except Exception as e:
            if isinstance(e, InvalidSignature):
                return False
            raise VerificationError(f"Failed to verify manifest: {e}")

    def verify_package(self, package: PluginPackage) -> bool:
        """Verify a signed plugin package.

        This verifies both the manifest signature and file integrity.

        Args:
            package: Plugin package to verify

        Returns:
            True if the package is valid, False otherwise

        Raises:
            VerificationError: If verification fails due to an error
        """
        if not package.manifest:
            return False

        # First, verify the manifest signature
        if not self.verify_manifest(package.manifest):
            return False

        # Then, verify package integrity
        return package.verify_integrity()