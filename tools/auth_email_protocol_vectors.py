#!/usr/bin/env python3
"""Generate/check PUBLIC TEST email registration interoperability fixtures.

Requires Python 3 and cryptography. Reuses the existing device protocol fixture
helpers unchanged. All keys, nonces, student numbers, addresses and signatures
are PUBLIC TEST DATA, never production configuration. Not an authentication SDK.
"""

import argparse
import json
import re
import struct
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import utils

from auth_protocol_vectors import (
    ORDER, SCHEME, association_token, build_vectors as build_device_vectors,
    fixture_sign, frame, public_key, rejects, require, sha256, unframe, utf8, verify,
)

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-email-binding-v1.json"
PROTOCOL = "iwut-email-registration-v1"
DOMAIN = "iwut-email-registration-proof-v1"
PURPOSE = "REGISTER_WITH_EMAIL"
LOCAL = re.compile(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*", re.ASCII)
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
FIELD_NAMES = ["domainSeparator", "protocolVersion", "purpose", "serviceId", "applicationId", "operationId", "challenge", "expiresAtUnixMs", "publicKey65", "associationDigest", "normalizedEmail"]


def normalize_email(value):
    value = value.strip(" ")
    if not value.isascii():
        raise ValueError("ASCII address required")
    value = value.lower()
    if len(value) > 254 or value.count("@") != 1:
        raise ValueError("invalid address length or separator")
    local, domain = value.split("@")
    if len(local) > 64 or not LOCAL.fullmatch(local):
        raise ValueError("invalid dot-atom local part")
    labels = domain.split(".")
    if len(labels) < 2 or any(not LABEL.fullmatch(label) for label in labels):
        raise ValueError("invalid DNS domain")
    return value


def payload_for(proof):
    return frame(
        utf8(DOMAIN), utf8(PROTOCOL), utf8(PURPOSE), utf8(proof["serviceId"]),
        utf8(proof["applicationId"]), utf8(proof["operationId"]),
        bytes.fromhex(proof["challenge_hex"]), struct.pack(">Q", proof["expiresAtUnixMs"]),
        bytes.fromhex(proof["publicKey65_hex"]), bytes.fromhex(proof["associationDigest_hex"]),
        utf8(proof["normalizedEmail"]),
    )


def validate_context(payload, proof, now):
    fields = unframe(payload, 11)
    if payload != payload_for(proof):
        raise ValueError("unexpected operation context")
    if len(fields[6]) != 32 or len(fields[7]) != 8 or len(fields[9]) != 32:
        raise ValueError("invalid fixed width")
    public_key(fields[8])
    if normalize_email(fields[10].decode("ascii")) != fields[10].decode("ascii"):
        raise ValueError("email is not canonical")
    if now >= proof["expiresAtUnixMs"]:
        raise ValueError("operation expired")


def build_vectors():
    device = build_device_vectors()
    key = device["deviceKey"]["publicKey65_hex"]
    # example.test is fixture input only; this script never sends mail.
    valid_emails = ["  Student+TAG@EXAMPLE.TEST  ", "student.name@example.test", "studentname@example.test", "a!#$%&'*+-/=?^_`{|}~@example.test", "A@X.Y", "a" * 64 + "@example.test", "a@" + "b" * 63 + ".test", "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 61])]
    invalid_emails = ["", "   ", "student", "a@@example.test", "@example.test", "a@example", ".a@example.test", "a.@example.test", "a..b@example.test", '"a"@example.test', "Name <a@example.test>", "a(comment)@example.test", "a@[127.0.0.1]", "a@-example.test", "a@example-.test", "a@example..test", "a@example.test.", "a@exam_ple.test", "a@" + "b" * 64 + ".test", "a" * 65 + "@example.test", "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 62]), "用户@example.test", "a@例子.test", "\u00a0a@example.test", "\ta@example.test", "a@example.test\r\n", "a b@example.test", "a\x00@example.test"]
    proofs = []
    for index, (student, email) in enumerate((("0122256789101", valid_emails[0]), ("2026123456", " Graduate@EXAMPLE.TEST "))):
        token = association_token(student)
        digest_input = frame(utf8(SCHEME), token)
        proof = {
            "name": "email_registration_leading_zero" if index == 0 else "email_registration_graduate",
            "credentialProposalProtocolVersion": "iwut-device-v1", "protocolVersion": PROTOCOL,
            "purpose": PURPOSE, "serviceId": "iwut-auth-center:test", "applicationId": "iwut-client",
            "operationId": f"55555555-5555-4555-8555-{index + 1:012d}",
            "challenge_hex": bytes(range(index * 32, (index + 1) * 32)).hex(),
            "issuedAtUnixMs": 1800000000000, "expiresAtUnixMs": 1800000600000,
            "publicKey65_hex": key, "studentInput": student, "schemeVersion": SCHEME,
            "associationToken_hex": token.hex(), "associationDigestInput_hex": digest_input.hex(),
            "associationDigest_hex": sha256(digest_input).hex(), "emailInput": email,
            "normalizedEmail": normalize_email(email),
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
    fields = unframe(payload, 11)
    negative = []
    replacements = [b"iwut-device-proof-v1", b"iwut-device-v1", b"REGISTER", b"iwut-auth-center:prod", b"other-client", b"66666666-6666-4666-8666-666666666666", b"\xff" * 32, struct.pack(">Q", proof["expiresAtUnixMs"] + 1), bytes.fromhex(key)[:-1] + b"\xff", b"\xff" * 32, b"other@example.test"]
    def add(name, kind, value, sig=signature, **extra):
        negative.append({"name": name, "kind": kind, "referenceProof": proof["name"], "publicKey65_hex": key, "payload_hex": value.hex(), "signature_der_hex": sig.hex(), "expected": "REJECT", **extra})
    for index, replacement in enumerate(replacements):
        changed = fields.copy()
        changed[index] = replacement
        add("tamper_" + FIELD_NAMES[index], "SIGNATURE", frame(*changed))
    r, s = utils.decode_dss_signature(signature)
    for name, bad in (("double_hash", fixture_sign(sha256(payload))), ("der_trailing_byte", signature + b"\x00"), ("der_zero_scalar", utils.encode_dss_signature(0, s)), ("der_scalar_out_of_range", utils.encode_dss_signature(ORDER, s)), ("der_nonminimal_length", b"\x30\x81" + signature[1:]), ("raw_r_s_not_der", r.to_bytes(32, "big") + s.to_bytes(32, "big"))):
        add(name, "SIGNATURE", payload, bad)
    for name, bad in (("trailing_byte", payload + b"\x00"), ("truncated_field", payload[:-1]), ("extra_field", payload + frame(b"extra")), ("missing_field", frame(*fields[:-1])), ("truncated_length", frame(*fields[:-1]) + b"\x00\x00"), ("oversized_frame", b"\x00" * 1025)):
        add(name, "FRAME", bad)
    legacy = device["proofs"][0]
    add("legacy_signature_cannot_register_email", "SIGNATURE", payload, bytes.fromhex(legacy["signature_der_hex"]))
    add("email_signature_cannot_register_legacy", "SIGNATURE", bytes.fromhex(legacy["signingPayload_hex"]))
    # A valid legacy signature is still rejected by an email endpoint's context parser.
    add("legacy_payload_not_email_context", "CONTEXT", bytes.fromhex(legacy["signingPayload_hex"]), bytes.fromhex(legacy["signature_der_hex"]))
    return {"warning": "PUBLIC TEST KEYS, STUDENT NUMBERS, ADDRESSES AND NONCES. NEVER USE IN PRODUCTION.", "contract": "auth-email-binding-v1", "protocolVersion": PROTOCOL, "credentialProposalProtocolVersion": "iwut-device-v1", "signatureFixtureGeneration": device["signatureFixtureGeneration"], "deviceKey": device["deviceKey"], "frameFields": FIELD_NAMES, "emailNormalization": [{"input": value, "normalized": normalize_email(value)} for value in valid_emails], "invalidEmailInputs": [{"input": value, "expected": "REJECT"} for value in invalid_emails], "proofs": proofs, "negativeProofs": negative, "expiryChecks": [{"referenceProof": proof["name"], "nowUnixMs": proof["expiresAtUnixMs"] + delta, "expected": "ACCEPT" if delta < 0 else "REJECT"} for delta in (-1, 0, 1)]}


def validate(vectors):
    for item in vectors["emailNormalization"]:
        require(normalize_email(item["input"]) == item["normalized"], "email normalization")
    for item in vectors["invalidEmailInputs"]:
        rejects(lambda item=item: normalize_email(item["input"]), "invalid email")
    by_name = {proof["name"]: proof for proof in vectors["proofs"]}
    for proof in by_name.values():
        require(proof["expiresAtUnixMs"] - proof["issuedAtUnixMs"] == 600000, "ten minute lifetime")
        require(proof["normalizedEmail"] == normalize_email(proof["emailInput"]), "proof email")
        token = association_token(proof["studentInput"])
        require(token.hex() == proof["associationToken_hex"], "student token")
        digest_input = frame(utf8(SCHEME), token)
        require(digest_input.hex() == proof["associationDigestInput_hex"], "association digest frame")
        require(sha256(digest_input).hex() == proof["associationDigest_hex"], "association digest")
        key, payload, sig = (bytes.fromhex(proof[field]) for field in ("publicKey65_hex", "signingPayload_hex", "signature_der_hex"))
        require(payload == payload_for(proof), "signing payload")
        require(sha256(payload).hex() == proof["sha256_hex"], "SHA256 exactly once")
        validate_context(payload, proof, proof["issuedAtUnixMs"])
        verify(key, payload, sig)
        verify(key, payload, bytes.fromhex(proof["equivalentS_signature_der_hex"]))
    require(association_token("0122256789101") != association_token("122256789101"), "leading zero retained")
    for item in vectors["negativeProofs"]:
        payload, sig, key = (bytes.fromhex(item[field]) for field in ("payload_hex", "signature_der_hex", "publicKey65_hex"))
        proof = by_name[item["referenceProof"]]
        if item["kind"] == "FRAME":
            rejects(lambda payload=payload: unframe(payload, 11), item["name"])
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
        require(actual == serialized, "fixture drift: run python3 tools/auth_email_protocol_vectors.py --write")
        validate(json.loads(actual))
        print("Email vectors match; normalization, framing, context, P-256 signatures and expiry checks passed.")


if __name__ == "__main__":
    main()
