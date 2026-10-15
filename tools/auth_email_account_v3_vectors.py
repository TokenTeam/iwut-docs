#!/usr/bin/env python3
"""Generate/check PUBLIC TEST email registration v3 fixtures, never send mail."""
import argparse
import json
import struct
import hmac
import hashlib
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import utils
from auth_email_protocol_vectors import normalize_email, build_vectors as build_v1
from auth_protocol_vectors import (ORDER, fixture_sign, frame, public_key, rejects,
                                   require, sha256, unframe, utf8, verify)

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-email-account-v3.json"
PROTOCOL = "iwut-email-registration-v3"
DOMAIN = "iwut-email-registration-proof-v3"
PURPOSE = "REGISTER_WITH_PASSWORD_EMAIL"
FIELDS = ["domainSeparator", "protocolVersion", "purpose", "serviceId", "applicationId",
          "operationId", "challenge", "expiresAtUnixMs", "publicKey65", "normalizedEmail"]


def payload_for(p):
    return frame(utf8(DOMAIN), utf8(PROTOCOL), utf8(PURPOSE), utf8(p["serviceId"]),
                 utf8(p["applicationId"]), utf8(p["operationId"]),
                 bytes.fromhex(p["challenge_hex"]), struct.pack(">Q", p["expiresAtUnixMs"]),
                 bytes.fromhex(p["publicKey65_hex"]), utf8(p["normalizedEmail"]))


def validate_context(payload, p, now):
    if len(payload) > 1024:
        raise ValueError("payload exceeds bound")
    fields = unframe(payload, 10)
    if payload != payload_for(p):
        raise ValueError("unexpected operation context")
    if len(fields[6]) != 32 or len(fields[7]) != 8:
        raise ValueError("invalid width")
    public_key(fields[8])
    if normalize_email(fields[9].decode("ascii")) != fields[9].decode("ascii"):
        raise ValueError("noncanonical email")
    if now >= p["expiresAtUnixMs"]:
        raise ValueError("expired")


def build_vectors():
    historical = build_v1()
    proofs = []
    for old in historical["proofs"]:
        p = {k: v for k, v in old.items() if k not in {
            "studentInput", "schemeVersion", "associationToken_hex", "associationDigestInput_hex",
            "associationDigest_hex", "signingPayload_hex", "sha256_hex", "signature_der_hex",
            "equivalentS_signature_der_hex"}}
        p["protocolVersion"] = PROTOCOL
        p["name"] = p["name"] + "_v3"
        payload = payload_for(p)
        sig = fixture_sign(payload)
        r, s = utils.decode_dss_signature(sig)
        p.update(signingPayload_hex=payload.hex(), sha256_hex=sha256(payload).hex(),
                 signature_der_hex=sig.hex(),
                 equivalentS_signature_der_hex=utils.encode_dss_signature(r, ORDER-s).hex())
        proofs.append(p)
    p = proofs[0]
    payload, sig, key = (bytes.fromhex(p[k]) for k in
                         ("signingPayload_hex", "signature_der_hex", "publicKey65_hex"))
    fields = unframe(payload, 10)
    negatives = []
    def add(name, kind, b, signature=sig):
        negatives.append(dict(name=name, kind=kind, referenceProof=p["name"],
                              publicKey65_hex=key.hex(), payload_hex=b.hex(),
                              signature_der_hex=signature.hex(), expected="REJECT"))
    replacements = [b"iwut-email-registration-proof-v1", b"iwut-email-registration-v1", b"LOGIN_WITH_EMAIL",
                    b"wrong-service", b"wrong-application", b"66666666-6666-4666-8666-666666666666",
                    b"\xff" * 32, struct.pack(">Q", p["expiresAtUnixMs"]+1), key[:-1]+b"\xff", b"wrong@example.test"]
    for i, replacement in enumerate(replacements):
        changed = fields.copy()
        changed[i] = replacement
        add("tamper_" + FIELDS[i], "SIGNATURE", frame(*changed))
    r, s = utils.decode_dss_signature(sig)
    for name, bad in (("double_hash", fixture_sign(sha256(payload))), ("der_trailing_byte", sig+b"\x00"),
                      ("der_zero_scalar", utils.encode_dss_signature(0, s)),
                      ("der_out_of_range", utils.encode_dss_signature(ORDER, s)),
                      ("der_nonminimal_length", b"\x30\x81" + sig[1:]),
                      ("raw_r_s_not_der", r.to_bytes(32, "big")+s.to_bytes(32, "big"))):
        add(name, "SIGNATURE", payload, bad)
    for name, bad in (("trailing_byte", payload+b"\x00"), ("truncated_field", payload[:-1]),
                      ("extra_field", payload+frame(b"extra")), ("missing_field", frame(*fields[:-1])),
                      ("oversized_frame", b"\x00"*1025),
                      ("association_digest_not_permitted", frame(*fields[:9], b"\x00"*32, fields[9]))):
        add(name, "FRAME", bad)
    old = historical["proofs"][0]
    add("v1_signature_not_v3", "SIGNATURE", payload, bytes.fromhex(old["signature_der_hex"]))
    add("v1_payload_not_v3", "CONTEXT", bytes.fromhex(old["signingPayload_hex"]), bytes.fromhex(old["signature_der_hex"]))
    return dict(warning="PUBLIC TEST KEYS, ADDRESSES AND NONCES. NEVER USE IN PRODUCTION.",
                contract="auth-email-account-v3", protocolVersion=PROTOCOL,
                credentialProposalProtocolVersion="iwut-device-v1", deviceKey=historical["deviceKey"],
                signatureFixtureGeneration=historical["signatureFixtureGeneration"], frameFields=FIELDS,
                emailNormalization=historical["emailNormalization"], invalidEmailInputs=historical["invalidEmailInputs"],
                proofs=proofs, negativeProofs=negatives,
                expiryChecks=[dict(referenceProof=p["name"], nowUnixMs=p["expiresAtUnixMs"]+d,
                                   expected="ACCEPT" if d < 0 else "REJECT") for d in (-1, 0, 1)])


def mac_vectors(v):
    p = v["proofs"][0]
    key = bytes(range(32))
    password_key = bytes(range(32, 64))
    request_id = "11111111-1111-4111-8111-111111111111"
    binding_id = "22222222-2222-4222-8222-222222222222"
    u64 = lambda n: struct.pack(">Q", n)
    rows = []
    def add(name, fields, k=key):
        encoded = frame(*fields)
        rows.append(dict(name=name, fields_hex=[f.hex() for f in fields], frame_hex=encoded.hex(),
                         key_hex=k.hex(), mac_hex=hmac.new(k, encoded, hashlib.sha256).hexdigest()))
        return bytes.fromhex(rows[-1]["mac_hex"])
    request_mac = add("register_request", [utf8("iwut-email-request-v3"), utf8(PURPOSE), utf8(request_id),
             utf8(p["normalizedEmail"]), utf8(p["serviceId"]), utf8("iwut-client"),
             utf8("iwut-device-v1"), bytes.fromhex(p["publicKey65_hex"])])
    add("registration_code", [utf8("iwut-email-code-v3"), utf8(PURPOSE), utf8(p["operationId"]),
             u64(p["expiresAtUnixMs"]), request_mac, b"00001234"])
    add_mac = add("add_request", [utf8("iwut-email-request-v3"), b"ADD_VERIFIED_EMAIL", utf8(request_id),
             utf8(p["normalizedEmail"]), utf8(p["serviceId"]), b"iwut-client", b"fixture-owner", u64(7), u64(3)])
    add("add_code", [b"iwut-email-code-v3", b"ADD_VERIFIED_EMAIL", utf8(p["operationId"]),
             u64(p["expiresAtUnixMs"]), add_mac, b"00001234"])
    add("switch_request", [b"iwut-email-mutation-request-v3", b"SWITCH_LOGIN_EMAIL", b"fixture-owner",
             utf8(request_id), utf8(binding_id), u64(3), u64(2), u64(4), u64(7), utf8("a unique first password")], password_key)
    add("remove_request", [b"iwut-email-mutation-request-v3", b"REMOVE_VERIFIED_EMAIL", b"fixture-owner",
             utf8(request_id), utf8(binding_id), u64(3), u64(0), u64(0), u64(7)])
    return dict(emailKey_hex=key.hex(), passwordKey_hex=password_key.hex(), requestId=request_id,
                bindingId=binding_id, password="a unique first password", entries=rows)


def validate(v):
    for e in v["emailNormalization"]:
        require(normalize_email(e["input"]) == e["normalized"], "normalization")
    for e in v["invalidEmailInputs"]:
        rejects(lambda e=e: normalize_email(e["input"]), "invalid email")
    by_name = {p["name"]: p for p in v["proofs"]}
    for p in by_name.values():
        payload, sig, key = (bytes.fromhex(p[k]) for k in ("signingPayload_hex", "signature_der_hex", "publicKey65_hex"))
        require(payload == payload_for(p), "exact payload")
        require(sha256(payload).hex() == p["sha256_hex"], "hash exactly once")
        require(p["expiresAtUnixMs"]-p["issuedAtUnixMs"] == 600000, "lifetime")
        validate_context(payload, p, p["issuedAtUnixMs"])
        verify(key, payload, sig)
        verify(key, payload, bytes.fromhex(p["equivalentS_signature_der_hex"]))
    for n in v["negativeProofs"]:
        p = by_name[n["referenceProof"]]
        payload, sig, key = (bytes.fromhex(n[k]) for k in ("payload_hex", "signature_der_hex", "publicKey65_hex"))
        if n["kind"] == "FRAME":
            rejects(lambda payload=payload: unframe(payload, 10), n["name"])
        elif n["kind"] == "CONTEXT":
            rejects(lambda: validate_context(payload, p, p["issuedAtUnixMs"]), n["name"])
        else:
            rejects(lambda: verify(key, payload, sig), n["name"])
    for e in v["expiryChecks"]:
        p = by_name[e["referenceProof"]]
        action = lambda: validate_context(bytes.fromhex(p["signingPayload_hex"]), p, e["nowUnixMs"])
        action() if e["expected"] == "ACCEPT" else rejects(action, "expiry")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    v = build_vectors()
    v["macVectors"] = mac_vectors(v)
    validate(v)
    for row in v["macVectors"]["entries"]:
        require(frame(*(bytes.fromhex(f) for f in row["fields_hex"])).hex() == row["frame_hex"], "MAC frame")
        require(hmac.new(bytes.fromhex(row["key_hex"]), bytes.fromhex(row["frame_hex"]), hashlib.sha256).hexdigest() == row["mac_hex"], "independent HMAC")
    serialized = json.dumps(v, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUTPUT.write_text(serialized, encoding="utf-8")
        print("Wrote validated PUBLIC TEST v3 vectors: " + str(OUTPUT))
    else:
        require(OUTPUT.read_text(encoding="utf-8") == serialized, "fixture drift: regenerate v3 vectors")
        validate(json.loads(serialized))
        print("Email v3 vectors match; normalization, framing, signatures and expiry passed.")


if __name__ == "__main__":
    main()
