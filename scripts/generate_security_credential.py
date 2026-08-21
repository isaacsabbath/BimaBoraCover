#!/usr/bin/env python3
"""
Generate a Daraja B2C SecurityCredential.

=================================================
WHAT THIS IS
=================================================
Daraja's B2C endpoint doesn't accept your initiator password directly.
It wants that password RSA-encrypted against Safaricom's public
certificate (PKCS1v1.5 padding), then base64-encoded. That output is
the "SecurityCredential" you set as DARAJA_SECURITY_CREDENTIAL.

It's a one-time (well, "until the password changes") value — you run
this script, get a string, and paste it into your .env. Nothing here
talks to the network; it's pure local RSA encryption.

=================================================
BEFORE YOU RUN THIS
=================================================
You need two things:

1. Safaricom's public certificate (a .cer/.pem file), matching your
   environment:
     - Sandbox:    log in at https://developer.safaricom.co.ke,
                    open your app, go to the "Test Credentials" /
                    "Generate Security Credential" page — it links a
                    current sandbox certificate download.
     - Production: available from your M-Pesa Org / Business portal
                    once you're approved to go live (Go Live tab on
                    Daraja links to it), NOT the sandbox one.
   Save whichever one you need as, e.g., certs/sandbox-cert.cer or
   certs/production-cert.cer in this repo (that folder is already
   .gitignore'd — see note at the bottom of this file — never commit
   real certs or credentials).

   NOTE: this machine's network access couldn't reach
   developer.safaricom.co.ke to fetch the cert for you directly, so
   you'll need to download it yourself via the portal in a browser
   and drop the file in place before running this script.

2. The initiator password for DARAJA_INITIATOR_NAME (config/settings
   /base.py). For sandbox this is almost always "testapi" with the
   password shown on the same Test Credentials page as the cert. For
   production it's the password for your real API operator account
   (set/reset from the Daraja portal — Go Live -> API operator).

=================================================
USAGE
=================================================
    python scripts/generate_security_credential.py \\
        --cert certs/sandbox-cert.cer \\
        --password "your-initiator-password"

    # or omit --password to be prompted (won't echo to terminal):
    python scripts/generate_security_credential.py --cert certs/sandbox-cert.cer

    # write straight into .env instead of just printing:
    python scripts/generate_security_credential.py \\
        --cert certs/sandbox-cert.cer --write-env

The script prints the base64 SecurityCredential. Set that as
DARAJA_SECURITY_CREDENTIAL in your .env (--write-env does this for
you, updating the existing line or appending a new one), then restart
runserver AND qcluster — both only read .env at startup.

Re-run this any time the initiator password changes or you switch
between sandbox and production certs.
"""

import argparse
import base64
import getpass
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography import x509
except ImportError:
    print(
        "The 'cryptography' package is required. Install it with:\n"
        "    pip install cryptography --break-system-packages\n"
        "(it's also now pinned in requirements.txt)",
        file=sys.stderr,
    )
    sys.exit(1)


def load_public_key(cert_path: Path):
    """Load an RSA public key out of a .cer/.pem/.crt file.

    Safaricom's certs are usually plain PEM (readable text starting
    with '-----BEGIN CERTIFICATE-----') even when the extension is
    .cer, so we try parsing as an X.509 certificate first and fall
    back to a bare PEM public key.
    """
    raw = cert_path.read_bytes()

    try:
        cert = x509.load_pem_x509_certificate(raw)
        return cert.public_key()
    except ValueError:
        pass

    try:
        return load_pem_public_key(raw)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse '{cert_path}' as an X.509 certificate or a "
            f"PEM public key. Make sure you downloaded the correct cert "
            f"file from the Daraja portal and it wasn't corrupted/HTML "
            f"(a common failure mode is accidentally saving a login page "
            f"instead of the actual .cer file)."
        ) from exc


def generate_security_credential(password: str, cert_path: Path) -> str:
    public_key = load_public_key(cert_path)

    # Safaricom's documented/observed behaviour (and every working
    # community implementation) uses PKCS1v1.5 padding, NOT OAEP.
    encrypted = public_key.encrypt(
        password.encode("utf-8"),
        padding.PKCS1v15(),
    )
    return base64.b64encode(encrypted).decode("ascii")


def write_to_env(security_credential: str, env_path: Path):
    key = "DARAJA_SECURITY_CREDENTIAL"
    line = f"{key}={security_credential}\n"

    if not env_path.exists():
        env_path.write_text(line)
        print(f"Created {env_path} with {key}.")
        return

    lines = env_path.read_text().splitlines(keepends=True)
    for i, existing in enumerate(lines):
        if existing.split("=", 1)[0].strip() == key:
            lines[i] = line
            env_path.write_text("".join(lines))
            print(f"Updated existing {key} line in {env_path}.")
            return

    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(line)
    env_path.write_text("".join(lines))
    print(f"Appended {key} to {env_path}.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Daraja B2C SecurityCredential (RSA-encrypted initiator password)."
    )
    parser.add_argument(
        "--cert",
        required=True,
        type=Path,
        help="Path to Safaricom's public certificate (.cer/.pem) for your environment.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Initiator password to encrypt. Omit to be prompted (recommended — avoids shell history).",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write/update DARAJA_SECURITY_CREDENTIAL in .env instead of only printing it.",
    )
    parser.add_argument(
        "--env-path",
        default=Path(__file__).resolve().parent.parent / ".env",
        type=Path,
        help="Path to .env (default: repo root .env).",
    )
    args = parser.parse_args()

    if not args.cert.exists():
        print(f"Certificate file not found: {args.cert}", file=sys.stderr)
        sys.exit(1)

    password = args.password or getpass.getpass("Initiator password: ")
    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    try:
        credential = generate_security_credential(password, args.cert)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nSecurityCredential:")
    print(credential)

    if args.write_env:
        write_to_env(credential, args.env_path)
        print(
            "\nRestart both `manage.py runserver` and `manage.py qcluster` — "
            "they only read .env at startup."
        )
    else:
        print(
            f"\nSet this as DARAJA_SECURITY_CREDENTIAL in {args.env_path}, "
            "then restart both `manage.py runserver` and `manage.py qcluster`."
        )


if __name__ == "__main__":
    main()
