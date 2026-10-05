#!/usr/bin/env python3
"""Generate/check PUBLIC TEST UC025 account-closure proof and token fixtures.

All keys, challenges and tokens are public fixtures, never production secrets.
Uses the device protocol's P-256/SHA-256, DER and Frame implementation.
"""

import argparse
import json
import struct
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import utils

from auth_protocol_vectors import (
    ORDER, build_vectors as device_vectors, decode_token, fixture_sign, frame,
    rejects, require, sha256, unframe, utf8, verify,
)

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-account-closure-v1.json"
DOMAIN = "iwut-account-closure-proof-v1"
PURPOSE = "PREPARE_ACCOUNT_CLOSURE"
POLICY = "account-closure-v1"
FIELDS = ["domainSeparator", "purpose", "serviceId", "applicationId", "operationId",
          "challenge", "expiresAtUnixMs", "locatorKind", "locatorValue", "policyVersion"]


def payload_for(proof):
    return frame(utf8(DOMAIN), utf8(PURPOSE), utf8(proof["serviceId"]),
                 utf8(proof["applicationId"]), utf8(proof["operationId"]),
                 bytes.fromhex(proof["challenge_hex"]), struct.pack(">Q", proof["expiresAtUnixMs"]),
                 utf8(proof["locatorKind"]), bytes.fromhex(proof["locatorValue_hex"]), utf8(POLICY))


def validate_context(payload, proof, now):
    unframe(payload, 10)
    if payload != payload_for(proof):
        raise ValueError("unexpected account-closure operation context")
    if now >= proof["expiresAtUnixMs"]:
        raise ValueError("operation expired")


def build_vectors():
    device = device_vectors()
    key = device["deviceKey"]["publicKey65_hex"]
    proofs = []
    for index, locator in enumerate(device["proofs"][1:]):
        proof = {"name": "closure_by_" + locator["locatorKind"].lower(),
                 "purpose": PURPOSE, "policyVersion": POLICY, "serviceId": "iwut-auth-center:test",
                 "applicationId": "iwut-client", "operationId": f"99999999-9999-4999-8999-{index + 1:012d}",
                 "challenge_hex": bytes(range(128 + index * 32, 160 + index * 32)).hex(),
                 "issuedAtUnixMs": 1800000000000, "expiresAtUnixMs": 1800000300000,
                 "locatorKind": locator["locatorKind"], "locatorValue_hex": locator["locatorValue_hex"],
                 "publicKey65_hex": key}
        payload = payload_for(proof)
        signature = fixture_sign(payload)
        r, s = utils.decode_dss_signature(signature)
        proof.update({"signingPayload_hex": payload.hex(), "sha256_hex": sha256(payload).hex(),
                      "signature_der_hex": signature.hex(),
                      "equivalentS_signature_der_hex": utils.encode_dss_signature(r, ORDER - s).hex()})
        proofs.append(proof)
    proof = proofs[0]
    payload = bytes.fromhex(proof["signingPayload_hex"])
    signature = bytes.fromhex(proof["signature_der_hex"])
    fields = unframe(payload, 10)
    negative = []

    def add(name, kind, value, sig=signature):
        negative.append({"name": name, "kind": kind, "referenceProof": proof["name"],
                         "payload_hex": value.hex(), "signature_der_hex": sig.hex(), "expected": "REJECT"})

    for index, name in enumerate(FIELDS):
        changed = fields.copy()
        changed[index] = changed[index][:-1] + bytes([changed[index][-1] ^ 1])
        add("tamper_" + name, "SIGNATURE", frame(*changed))
    r, s = utils.decode_dss_signature(signature)
    for name, bad in (("double_hash", fixture_sign(sha256(payload))),
                      ("der_trailing_byte", signature + b"\x00"),
                      ("der_zero_scalar", utils.encode_dss_signature(0, s)),
                      ("der_scalar_out_of_range", utils.encode_dss_signature(ORDER, s)),
                      ("der_nonminimal_length", b"\x30\x81" + signature[1:]),
                      ("raw_r_s_not_der", r.to_bytes(32, "big") + s.to_bytes(32, "big"))):
        add(name, "SIGNATURE", payload, bad)
    for name, bad in (("trailing_byte", payload + b"\x00"), ("truncated_field", payload[:-1]),
                      ("extra_protocol_version", frame(fields[0], b"iwut-device-v1", *fields[1:])),
                      ("missing_field", frame(*fields[:-1])), ("oversized_frame", b"\x00" * 1025)):
        add(name, "FRAME", bad)
    cross = []
    for other in device["proofs"]:
        other_payload = bytes.fromhex(other["signingPayload_hex"])
        other_sig = bytes.fromhex(other["signature_der_hex"])
        cross.append(other)
        add(other["name"] + "_signature_cannot_close", "SIGNATURE", payload, other_sig)
        add("closure_cannot_" + other["name"], "SIGNATURE", other_payload)
        add(other["name"] + "_context_cannot_close", "CONTEXT", other_payload, other_sig)
    tokens = []
    for purpose in ("confirmation", "receipt"):
        domain = "iwut-closure-" + purpose + "-v1"
        raw = bytes.fromhex(device["session"]["rawToken_hex"])
        digest_input = frame(utf8(domain), raw)
        tokens.append({"purpose": purpose, "domainSeparator": domain,
                       "token": device["session"]["token"], "rawToken_hex": raw.hex(),
                       "digestInput_hex": digest_input.hex(), "tokenDigest_hex": sha256(digest_input).hex()})
    return {"warning": "PUBLIC TEST KEYS AND TOKENS. NEVER USE IN PRODUCTION.",
            "contract": "UC-AUTH-025/BR-ACC-014", "signatureFixtureGeneration": device["signatureFixtureGeneration"],
            "deviceKey": device["deviceKey"], "frameFields": FIELDS, "proofs": proofs,
            "crossProtocolProofs": cross, "negativeProofs": negative, "tokens": tokens,
            "invalidTokens": device["session"]["invalidTokens"],
            "expiryChecks": [{"referenceProof": proof["name"], "nowUnixMs": proof["expiresAtUnixMs"] + delta,
                              "expected": "ACCEPT" if delta < 0 else "REJECT"} for delta in (-1, 0, 1)]}


def validate(vectors):
    key = bytes.fromhex(vectors["deviceKey"]["publicKey65_hex"])
    by_name = {proof["name"]: proof for proof in vectors["proofs"]}
    for proof in by_name.values():
        payload = bytes.fromhex(proof["signingPayload_hex"])
        require(proof["expiresAtUnixMs"] - proof["issuedAtUnixMs"] == 300000, "five minute lifetime")
        require(payload == payload_for(proof), "canonical ten-field payload")
        require(sha256(payload).hex() == proof["sha256_hex"], "one SHA256")
        validate_context(payload, proof, proof["issuedAtUnixMs"])
        for field in ("signature_der_hex", "equivalentS_signature_der_hex"):
            verify(key, payload, bytes.fromhex(proof[field]))
    for proof in vectors["crossProtocolProofs"]:
        verify(key, bytes.fromhex(proof["signingPayload_hex"]), bytes.fromhex(proof["signature_der_hex"]))
    for item in vectors["negativeProofs"]:
        payload, sig = bytes.fromhex(item["payload_hex"]), bytes.fromhex(item["signature_der_hex"])
        proof = by_name[item["referenceProof"]]
        if item["kind"] == "FRAME":
            rejects(lambda: unframe(payload, 10), item["name"])
        elif item["kind"] == "CONTEXT":
            rejects(lambda: validate_context(payload, proof, proof["issuedAtUnixMs"]), item["name"])
        else:
            require(item["kind"] == "SIGNATURE", "known negative kind")
            rejects(lambda: verify(key, payload, sig), item["name"])
    for item in vectors["expiryChecks"]:
        proof = by_name[item["referenceProof"]]
        action = lambda: validate_context(bytes.fromhex(proof["signingPayload_hex"]), proof, item["nowUnixMs"])
        if item["expected"] == "ACCEPT":
            action()
        else:
            rejects(action, "expiry boundary")
    for item in vectors["tokens"]:
        raw = decode_token(item["token"])
        require(raw.hex() == item["rawToken_hex"], "canonical token bytes")
        framed = frame(utf8(item["domainSeparator"]), raw)
        require(framed.hex() == item["digestInput_hex"], "domain-separated digest input")
        require(sha256(framed).hex() == item["tokenDigest_hex"], "token digest")
        require(sha256(raw).hex() != item["tokenDigest_hex"], "not session digest")
    require(vectors["tokens"][0]["tokenDigest_hex"] != vectors["tokens"][1]["tokenDigest_hex"], "isolated token purposes")
    for token in vectors["invalidTokens"]:
        rejects(lambda: decode_token(token), "canonical token encoding")


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
        OUTPUT.write_text(serialized, encoding="utf-8")
        print("Wrote validated PUBLIC TEST closure vectors: " + str(OUTPUT))
    else:
        actual = OUTPUT.read_text(encoding="utf-8")
        require(actual == serialized, "fixture drift: run python3 tools/auth_account_closure_vectors.py --write")
        validate(json.loads(actual))
        print("Closure proof, DER, context, expiry and token isolation vectors passed.")


if __name__ == "__main__":
    main()
