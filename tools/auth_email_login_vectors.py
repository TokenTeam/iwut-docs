#!/usr/bin/env python3
"""Generate/check PUBLIC TEST email-login interoperability fixtures.

Requires Python 3 and cryptography. All keys, addresses, challenges and signatures
are PUBLIC TEST DATA, never production configuration. Not an authentication SDK.
The device and email-registration vector generators are reused without mutation.
"""

import argparse
import json
import struct
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import utils

from auth_email_protocol_vectors import build_vectors as build_registration_vectors, normalize_email
from auth_protocol_vectors import (
    ORDER, build_vectors as build_device_vectors, fixture_sign, frame, public_key,
    rejects, require, sha256, unframe, utf8, verify,
)

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-email-login-v1.json"
PROTOCOL = "iwut-email-login-v1"
DOMAIN = "iwut-email-login-proof-v1"
PURPOSE = "LOGIN_WITH_EMAIL"
FIELD_NAMES = ["domainSeparator", "protocolVersion", "purpose", "serviceId", "applicationId", "operationId", "challenge", "expiresAtUnixMs", "publicKey65", "normalizedEmail"]


def payload_for(proof):
    return frame(
        utf8(DOMAIN), utf8(PROTOCOL), utf8(PURPOSE), utf8(proof["serviceId"]),
        utf8(proof["applicationId"]), utf8(proof["operationId"]),
        bytes.fromhex(proof["challenge_hex"]), struct.pack(">Q", proof["expiresAtUnixMs"]),
        bytes.fromhex(proof["publicKey65_hex"]), utf8(proof["normalizedEmail"]),
    )


def validate_context(payload, proof, now):
    fields = unframe(payload, 10)
    if payload != payload_for(proof):
        raise ValueError("unexpected operation context")
    if len(fields[6]) != 32 or len(fields[7]) != 8:
        raise ValueError("invalid fixed width")
    public_key(fields[8])
    if normalize_email(fields[9].decode("ascii")) != fields[9].decode("ascii"):
        raise ValueError("email is not canonical")
    if now >= proof["expiresAtUnixMs"]:
        raise ValueError("operation expired")


def build_vectors():
    device = build_device_vectors()
    registration = build_registration_vectors()
    key = device["deviceKey"]["publicKey65_hex"]
    proofs = []
    for index, email in enumerate(("  Student+LOGIN@EXAMPLE.TEST  ", "Graduate.Name+SECOND@EXAMPLE.TEST")):
        proof = {
            "name": "email_login_tagged" if index == 0 else "email_login_dotted_tagged",
            "credentialProposalProtocolVersion": "iwut-device-v1", "protocolVersion": PROTOCOL,
            "purpose": PURPOSE, "serviceId": "iwut-auth-center:test", "applicationId": "iwut-client",
            "operationId": f"77777777-7777-4777-8777-{index + 1:012d}",
            "challenge_hex": bytes(range(64 + index * 32, 96 + index * 32)).hex(),
            "issuedAtUnixMs": 1800000000000, "expiresAtUnixMs": 1800000600000,
            "publicKey65_hex": key, "emailInput": email, "normalizedEmail": normalize_email(email),
        }
        payload = payload_for(proof)
        signature = fixture_sign(payload)
        r, s = utils.decode_dss_signature(signature)
        proof.update({"signingPayload_hex": payload.hex(), "sha256_hex": sha256(payload).hex(),
                      "signature_der_hex": signature.hex(), "equivalentS_signature_der_hex": utils.encode_dss_signature(r, ORDER - s).hex()})
        proofs.append(proof)
    proof = proofs[0]
    payload = bytes.fromhex(proof["signingPayload_hex"])
    signature = bytes.fromhex(proof["signature_der_hex"])
    fields = unframe(payload, 10)
    negative = []

    def add(name, kind, value, sig=signature, **extra):
        negative.append({"name": name, "kind": kind, "referenceProof": proof["name"], "publicKey65_hex": key,
                         "payload_hex": value.hex(), "signature_der_hex": sig.hex(), "expected": "REJECT", **extra})

    replacements = [b"iwut-device-proof-v1", b"iwut-device-v1", b"LOGIN", b"iwut-auth-center:prod", b"other-client", b"88888888-8888-4888-8888-888888888888", b"\xff" * 32, struct.pack(">Q", proof["expiresAtUnixMs"] + 1), bytes.fromhex(key)[:-1] + b"\xff", b"student@example.test"]
    for index, replacement in enumerate(replacements):
        changed = fields.copy()
        changed[index] = replacement
        add("tamper_" + FIELD_NAMES[index], "SIGNATURE", frame(*changed))
    r, s = utils.decode_dss_signature(signature)
    for name, bad in (("double_hash", fixture_sign(sha256(payload))), ("der_trailing_byte", signature + b"\x00"), ("der_zero_scalar", utils.encode_dss_signature(0, s)), ("der_scalar_out_of_range", utils.encode_dss_signature(ORDER, s)), ("der_nonminimal_length", b"\x30\x81" + signature[1:]), ("raw_r_s_not_der", r.to_bytes(32, "big") + s.to_bytes(32, "big"))):
        add(name, "SIGNATURE", payload, bad)
    for name, bad in (("trailing_byte", payload + b"\x00"), ("truncated_field", payload[:-1]), ("extra_field", payload + frame(b"extra")), ("missing_field", frame(*fields[:-1])), ("truncated_length", frame(*fields[:-1]) + b"\x00\x00"), ("oversized_frame", b"\x00" * 1025)):
        add(name, "FRAME", bad)
    cross_protocol = []
    for name, other in (("legacy_login", device["proofs"][1]), ("email_registration", registration["proofs"][0])):
        other_payload = bytes.fromhex(other["signingPayload_hex"])
        other_sig = bytes.fromhex(other["signature_der_hex"])
        cross_protocol.append({"name": name, "publicKey65_hex": key, "payload_hex": other_payload.hex(), "signature_der_hex": other_sig.hex(), "expected": "VALID_ONLY_IN_OWN_PROTOCOL"})
        add(name + "_signature_cannot_login_email", "SIGNATURE", payload, other_sig)
        add("email_login_signature_cannot_authorize_" + name, "SIGNATURE", other_payload)
        add(name + "_payload_not_email_login_context", "CONTEXT", other_payload, other_sig)
    return {"warning": "PUBLIC TEST KEYS, ADDRESSES AND NONCES. NEVER USE IN PRODUCTION.", "contract": "auth-email-login-v1", "protocolVersion": PROTOCOL, "credentialProposalProtocolVersion": "iwut-device-v1", "signatureFixtureGeneration": device["signatureFixtureGeneration"], "deviceKey": device["deviceKey"], "frameFields": FIELD_NAMES, "proofs": proofs, "crossProtocolProofs": cross_protocol, "negativeProofs": negative, "expiryChecks": [{"referenceProof": proof["name"], "nowUnixMs": proof["expiresAtUnixMs"] + delta, "expected": "ACCEPT" if delta < 0 else "REJECT"} for delta in (-1, 0, 1)]}


def validate(vectors):
    by_name = {proof["name"]: proof for proof in vectors["proofs"]}
    for proof in by_name.values():
        require(proof["expiresAtUnixMs"] - proof["issuedAtUnixMs"] == 600000, "ten minute lifetime")
        require(proof["normalizedEmail"] == normalize_email(proof["emailInput"]), "proof email")
        require("+" in proof["normalizedEmail"], "email tag retained")
        key, payload, sig = (bytes.fromhex(proof[field]) for field in ("publicKey65_hex", "signingPayload_hex", "signature_der_hex"))
        require(payload == payload_for(proof), "signing payload")
        require(sha256(payload).hex() == proof["sha256_hex"], "SHA256 exactly once")
        validate_context(payload, proof, proof["issuedAtUnixMs"])
        verify(key, payload, sig)
        verify(key, payload, bytes.fromhex(proof["equivalentS_signature_der_hex"]))
        require(not any(name in proof for name in ("authId", "revision", "associationToken_hex", "associationDigest_hex")), "login has no registration-only fields")
    # Demonstrate that rejected cross-purpose signatures are valid signatures,
    # not merely malformed bytes accidentally accepted by the fixture generator.
    for item in vectors["crossProtocolProofs"]:
        verify(bytes.fromhex(item["publicKey65_hex"]), bytes.fromhex(item["payload_hex"]), bytes.fromhex(item["signature_der_hex"]))
    for item in vectors["negativeProofs"]:
        payload, sig, key = (bytes.fromhex(item[field]) for field in ("payload_hex", "signature_der_hex", "publicKey65_hex"))
        proof = by_name[item["referenceProof"]]
        if item["kind"] == "FRAME":
            rejects(lambda payload=payload: unframe(payload, 10), item["name"])
        elif item["kind"] == "CONTEXT":
            rejects(lambda payload=payload, proof=proof: validate_context(payload, proof, proof["issuedAtUnixMs"]), item["name"])
        else:
            require(item["kind"] == "SIGNATURE", "known negative kind")
            rejects(lambda key=key, payload=payload, sig=sig: verify(key, payload, sig), item["name"])
    for item in vectors["expiryChecks"]:
        proof = by_name[item["referenceProof"]]
        payload = bytes.fromhex(proof["signingPayload_hex"])
        action = lambda item=item, proof=proof, payload=payload: validate_context(payload, proof, item["nowUnixMs"])
        if item["expected"] == "ACCEPT":
            action()
        else:
            rejects(action, "expiry boundary")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build_vectors()
    validate(expected)
    serialized = json.dumps(expected, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(serialized, encoding="utf-8")
        print("Wrote validated PUBLIC TEST vectors: " + str(OUTPUT))
    else:
        actual = OUTPUT.read_text(encoding="utf-8")
        require(actual == serialized, "fixture drift: run python3 tools/auth_email_login_vectors.py --write")
        validate(json.loads(actual))
        print("Email-login vectors match; encoding, signatures, protocol isolation and expiry checks passed.")


if __name__ == "__main__":
    main()
