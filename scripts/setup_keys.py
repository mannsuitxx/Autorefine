#!/usr/bin/env python3
"""
Setup script to generate fresh Ed25519 keypairs for AutoRefine security components.
Generates:
  - security/.keys/ed25519_pack_signing.pem & .pub (for Knowledge Pack signing)
  - data/security/ed25519_private.key & security/ed25519_public.pem (for Audit Ledger signing)
"""

import os
import stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_pack_keys(base_dir: Path):
    keys_dir = base_dir / "security" / ".keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    priv_path = keys_dir / "ed25519_pack_signing.pem"
    pub_path = keys_dir / "ed25519_pack_signing.pub"

    print(f"Generating knowledge pack signing keypair in {keys_dir}...")
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()

    with open(priv_path, "wb") as f:
        f.write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    os.chmod(priv_path, stat.S_IRUSR | stat.S_IWUSR)

    with open(pub_path, "wb") as f:
        f.write(pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print("  [OK] Created ed25519_pack_signing.pem and ed25519_pack_signing.pub")
 
def generate_ledger_keys(base_dir: Path):
    sec_dir = base_dir / "data" / "security"
    sec_dir.mkdir(parents=True, exist_ok=True)
    pub_dir = base_dir / "security"
    pub_dir.mkdir(parents=True, exist_ok=True)

    priv_path = sec_dir / "ed25519_private.key"
    pub_path = pub_dir / "ed25519_public.pem"

    print(f"Generating audit ledger keypair...")
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()

    with open(priv_path, "wb") as f:
        f.write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    os.chmod(priv_path, stat.S_IRUSR | stat.S_IWUSR)

    with open(pub_path, "wb") as f:
        f.write(pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print("  [OK] Created data/security/ed25519_private.key and security/ed25519_public.pem")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    generate_pack_keys(base_dir)
    generate_ledger_keys(base_dir)
    print("All fresh security keys successfully generated!")

if __name__ == "__main__":
    main()
