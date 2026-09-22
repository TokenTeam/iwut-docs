#!/usr/bin/env python3
"""Generate/check auth-device-session-v1 interoperability fixtures.

Requires Python 3 and cryptography. RFC6979 fixture signing below avoids relying
on deterministic-signing support in the linked OpenSSL version.
All private keys, server keys, nonces and tokens below are PUBLIC TEST DATA.
NEVER use these constants, deterministic nonces, or this script in production.
This is an executable fixture checker, not a production authentication library.
"""

import argparse
import base64
import hashlib
import hmac
import json
import re
import struct
from pathlib import Path

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-device-session-v1.json"
PROTOCOL = "iwut-device-v1"
SCHEME = "iwut-student-association-v1"
ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
PRIVATE_SCALAR = 1  # Public test secret. Never a production key.


def utf8(value):
    return value.encode("utf-8")


def frame(*fields):
    return b"".join(struct.pack(">I", len(field)) + field for field in fields)


def unframe(payload, count):
    if len(payload) > 1024:
        raise ValueError("payload exceeds 1024 bytes")
    fields, cursor = [], 0
    for _ in range(count):
        if cursor + 4 > len(payload):
            raise ValueError("truncated length")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        cursor += 4
        if cursor + length > len(payload):
            raise ValueError("truncated field")
        fields.append(payload[cursor:cursor + length])
        cursor += length
    if cursor != len(payload):
        raise ValueError("trailing fields or bytes")
    return fields


def sha256(data):
    return hashlib.sha256(data).digest()


def fixture_sign(payload):
    """RFC6979 section 3.2, P-256/SHA-256. PUBLIC TEST fixture use only."""
    digest = sha256(payload)
    reduced = (int.from_bytes(digest, "big") % ORDER).to_bytes(32, "big")
    seed = PRIVATE_SCALAR.to_bytes(32, "big") + reduced
    value, secret = b"\x01" * 32, b"\x00" * 32
    secret = hmac.digest(secret, value + b"\x00" + seed, "sha256")
    value = hmac.digest(secret, value, "sha256")
    secret = hmac.digest(secret, value + b"\x01" + seed, "sha256")
    value = hmac.digest(secret, value, "sha256")
    while True:
        value = hmac.digest(secret, value, "sha256")
        nonce = int.from_bytes(value, "big")
        if 1 <= nonce < ORDER:
            point = ec.derive_private_key(nonce, ec.SECP256R1()).public_key().public_numbers()
            r = point.x % ORDER
            s = (pow(nonce, -1, ORDER) * (int.from_bytes(digest, "big") + r * PRIVATE_SCALAR)) % ORDER
            if r and s:
                return utils.encode_dss_signature(r, s)
        secret = hmac.digest(secret, value + b"\x00", "sha256")
        value = hmac.digest(secret, value, "sha256")


def b64u(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def decode_token(text):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", text, flags=re.ASCII):
        raise ValueError("invalid token alphabet or length")
    raw = base64.b64decode(text + "=", altchars=b"-_", validate=True)
    if len(raw) != 32 or b64u(raw) != text:
        raise ValueError("noncanonical token")
    return raw


def normalize_student(value):
    normalized = value.strip(" \t\r\n")
    if not re.fullmatch(r"[0-9]{1,64}", normalized, flags=re.ASCII):
        raise ValueError("student number must contain 1-64 ASCII digits")
    return normalized


def association_token(student):
    return sha256(frame(utf8(SCHEME), utf8(normalize_student(student))))


def public_key(data):
    if len(data) != 65 or data[0] != 4:
        raise ValueError("expected uncompressed 65-byte P-256 key")
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), data)


def verify(key_bytes, payload, signature):
    if len(signature) > 72:
        raise ValueError("oversized DER")
    r, s = utils.decode_dss_signature(signature)
    if not (1 <= r < ORDER and 1 <= s < ORDER):
        raise ValueError("ECDSA scalar out of range")
    if utils.encode_dss_signature(r, s) != signature:
        raise ValueError("noncanonical DER")
    public_key(key_bytes).verify(signature, payload, ec.ECDSA(hashes.SHA256()))


def payload_for(vector):
    return frame(
        b"iwut-device-proof-v1", utf8(PROTOCOL), utf8(vector["purpose"]),
        utf8(vector["serviceId"]), utf8(vector["applicationId"]),
        utf8(vector["operationId"]), bytes.fromhex(vector["challenge_hex"]),
        struct.pack(">Q", vector["expiresAtUnixMs"]), utf8(vector["locatorKind"]),
        bytes.fromhex(vector["locatorValue_hex"]),
        bytes.fromhex(vector["associationDigest_hex"]),
    )


def build_vectors():
    private = ec.derive_private_key(PRIVATE_SCALAR, ec.SECP256R1())
    key = private.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    fingerprint_input = frame(b"iwut-device-public-key-v1", key)
    fingerprint = sha256(fingerprint_input)
    students = []
    for number in ("0122256789101", "2026123456", " \t0122256789101\r\n ", "0", "9" * 64):
        normalized = normalize_student(number)
        encoded = frame(utf8(SCHEME), utf8(normalized))
        token = sha256(encoded)
        students.append({"input": number, "normalized": normalized,
                         "hashInput_hex": encoded.hex(), "associationToken_hex": token.hex()})
    invalid_students = ["", " \t\r\n", "0122 256789101", "2026\t123456",
                        "+2026123456", "-1", "１２００", "2026a", "9" * 65,
                        "\u00a02026123456", "2026123456\x0b", "2026123456\x00"]
    association = bytes.fromhex(students[0]["associationToken_hex"])
    association_digest = sha256(frame(utf8(SCHEME), association))
    proofs = []
    for index, (name, purpose, kind, locator) in enumerate((
        ("register", "REGISTER", "PUBLIC_KEY_FINGERPRINT", fingerprint),
        ("login_by_credential_id", "LOGIN", "CREDENTIAL_ID",
         b"44444444-4444-4444-8444-444444444444"),
        ("login_by_public_key_fingerprint", "LOGIN", "PUBLIC_KEY_FINGERPRINT", fingerprint),
    )):
        item = {"name": name, "purpose": purpose, "serviceId": "iwut-auth-center:test",
                "applicationId": "iwut-client",
                "operationId": f"11111111-1111-4111-8111-{index + 1:012d}",
                "challenge_hex": bytes(range(index * 32, (index + 1) * 32)).hex(),
                "expiresAtUnixMs": 1800000300000, "locatorKind": kind,
                "locatorValue_hex": locator.hex(),
                "associationDigest_hex": association_digest.hex() if purpose == "REGISTER" else ""}
        payload = payload_for(item)
        signature = fixture_sign(payload)
        item.update({"signingPayload_hex": payload.hex(), "sha256_hex": sha256(payload).hex(),
                     "signature_der_hex": signature.hex(),
                     "doubleHash_signature_der_hex": fixture_sign(sha256(payload)).hex()})
        proofs.append(item)
    token_raw = bytes(range(32))
    token_text = b64u(token_raw)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    alias = token_text[:-1] + alphabet[alphabet.index(token_text[-1]) + 1]
    session = {"rawToken_hex": token_raw.hex(), "token": token_text,
               "tokenDigest_hex": sha256(token_raw).hex(),
               "incorrectTextDigest_hex": sha256(utf8(token_text)).hex(),
               "invalidTokens": ["", token_text + "=", " " + token_text, token_text + "\n",
                                 token_text[:-1], "A" * 44, "+" + token_text[1:],
                                 "/" + token_text[1:], alias, token_text + "," + token_text]}
    lookup_secret, encryption_secret = bytes(range(32)), bytes(range(32, 64))
    lookup_input = frame(b"iwut-association-lookup-v1", utf8(SCHEME), association)
    encryption = []
    for index, (kind, identifier) in enumerate((
        ("group", "22222222-2222-4222-8222-222222222222"),
        ("operation", proofs[0]["operationId"]),
    )):
        aad = frame(utf8(f"iwut-association-{kind}-v1"), utf8(identifier), utf8(SCHEME), b"test-k1")
        nonce = bytes(range(index * 12, (index + 1) * 12))
        ciphertext = AESGCM(encryption_secret).encrypt(nonce, association, aad)
        encryption.append({"kind": kind, "identifier": identifier, "keyVersion": "test-k1",
                           "nonce_hex": nonce.hex(), "aad_hex": aad.hex(),
                           "plaintext_hex": association.hex(), "ciphertextAndTag_hex": ciphertext.hex()})
    return {
        "warning": "PUBLIC TEST KEYS, PRIVATE SCALAR, NONCES AND TOKENS. NEVER USE IN PRODUCTION.",
        "contract": "auth-device-session-v1", "protocolVersion": PROTOCOL, "schemeVersion": SCHEME,
        "signatureFixtureGeneration": "RFC6979 deterministic ECDSA P-256/SHA-256; production signatures may differ",
        "deviceKey": {"privateScalar_hex": PRIVATE_SCALAR.to_bytes(32, "big").hex(),
                      "publicKey65_hex": key.hex(), "fingerprintInput_hex": fingerprint_input.hex(),
                      "fingerprint_hex": fingerprint.hex()},
        "students": students, "invalidStudentInputs": invalid_students,
        "leadingZeroLoss": {"input": "0122256789101", "incorrectInput": "122256789101",
                            "incorrectAssociationToken_hex": association_token("122256789101").hex()},
        "proofs": proofs, "session": session,
        "associationStorage": {"lookupKeySecret_hex": lookup_secret.hex(),
                               "encryptionKeySecret_hex": encryption_secret.hex(),
                               "lookupInput_hex": lookup_input.hex(),
                               "lookupKey_hex": hmac.digest(lookup_secret, lookup_input, "sha256").hex(),
                               "encryption": encryption},
    }


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def rejects(action, message, exceptions=(ValueError, InvalidSignature, InvalidTag)):
    try:
        action()
    except exceptions:
        return
    raise AssertionError("accepted negative vector: " + message)


def validate(vectors):
    key = bytes.fromhex(vectors["deviceKey"]["publicKey65_hex"])
    public_key(key)
    for student in vectors["students"]:
        require(normalize_student(student["input"]) == student["normalized"], "normalization")
        require(association_token(student["input"]).hex() == student["associationToken_hex"], "association token")
    for student in vectors["invalidStudentInputs"]:
        rejects(lambda student=student: normalize_student(student), "student input")
    require(vectors["students"][0]["associationToken_hex"] == vectors["students"][2]["associationToken_hex"], "ASCII trim")
    require(vectors["students"][0]["associationToken_hex"] != vectors["leadingZeroLoss"]["incorrectAssociationToken_hex"], "leading zero retained")
    fingerprint = sha256(frame(b"iwut-device-public-key-v1", key))
    require(fingerprint.hex() == vectors["deviceKey"]["fingerprint_hex"], "fingerprint")
    rejects(lambda: public_key(b"\x02" + key[1:33]), "compressed public key")
    rejects(lambda: public_key(b"\x04" + b"\x00" * 64), "off-curve public key")
    rejects(lambda: public_key(key + b"\x00"), "trailing public key bytes")
    rejects(lambda: public_key(b"\x00"), "point at infinity")
    spki = public_key(key).public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    rejects(lambda: public_key(spki), "SPKI is not publicKey65")
    for proof in vectors["proofs"]:
        payload = bytes.fromhex(proof["signingPayload_hex"])
        signature = bytes.fromhex(proof["signature_der_hex"])
        require(payload == payload_for(proof), "payload encoding")
        require(sha256(payload).hex() == proof["sha256_hex"], "payload hash")
        require(frame(*unframe(payload, 11)) == payload, "frame round trip")
        verify(key, payload, signature)
        # Both equivalent s forms must verify; the protocol does not mandate low-S.
        r, s = utils.decode_dss_signature(signature)
        verify(key, payload, utils.encode_dss_signature(r, ORDER - s))
        for field, wrong in (("purpose", "LOGIN" if proof["purpose"] == "REGISTER" else "REGISTER"),
                             ("serviceId", "iwut-auth-center:prod"),
                             ("applicationId", "other-client"),
                             ("locatorKind", "CREDENTIAL_ID" if proof["locatorKind"] != "CREDENTIAL_ID" else "PUBLIC_KEY_FINGERPRINT"),
                             ("locatorValue_hex", "ff" * 32),
                             ("associationDigest_hex", "ff" * 32)):
            changed = dict(proof, **{field: wrong})
            rejects(lambda changed=changed: verify(key, payload_for(changed), signature), "wrong " + field)
        rejects(lambda: verify(key, payload, bytes.fromhex(proof["doubleHash_signature_der_hex"])), "double hashing")
        rejects(lambda: verify(key, payload, signature + b"\x00"), "DER trailing bytes")
        rejects(lambda: verify(key, payload, utils.encode_dss_signature(0, s)), "DER zero scalar")
        rejects(lambda: verify(key, payload, utils.encode_dss_signature(ORDER, s)), "DER out-of-range scalar")
        rejects(lambda: verify(key, payload, b"\x30\x81" + signature[1:]), "nonminimal DER length")
        rejects(lambda: unframe(payload + b"\x00", 11), "trailing frame data")
        rejects(lambda: unframe(payload[:-1], 11), "truncated frame")
        rejects(lambda: unframe(payload + frame(b"extra"), 11), "extra frame field")
        rejects(lambda: unframe(b"\x00" * 1025, 11), "oversized payload")
    session = vectors["session"]
    raw = decode_token(session["token"])
    require(raw.hex() == session["rawToken_hex"], "token decoding")
    require(sha256(raw).hex() == session["tokenDigest_hex"], "token digest")
    require(session["tokenDigest_hex"] != session["incorrectTextDigest_hex"], "raw-token hashing")
    for token in session["invalidTokens"]:
        rejects(lambda token=token: decode_token(token), "token encoding")
    storage = vectors["associationStorage"]
    lookup_secret = bytes.fromhex(storage["lookupKeySecret_hex"])
    lookup_input = bytes.fromhex(storage["lookupInput_hex"])
    require(hmac.digest(lookup_secret, lookup_input, "sha256").hex() == storage["lookupKey_hex"], "lookup HMAC")
    encryption_secret = bytes.fromhex(storage["encryptionKeySecret_hex"])
    for record in storage["encryption"]:
        nonce, aad, ciphertext = (bytes.fromhex(record[name]) for name in ("nonce_hex", "aad_hex", "ciphertextAndTag_hex"))
        aes = AESGCM(encryption_secret)
        require(aes.decrypt(nonce, ciphertext, aad).hex() == record["plaintext_hex"], "AES-GCM decrypt")
        wrong_key = bytes([encryption_secret[0] ^ 1]) + encryption_secret[1:]
        rejects(lambda: AESGCM(wrong_key).decrypt(nonce, ciphertext, aad), "wrong encryption key")
        rejects(lambda: aes.decrypt(nonce, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]), aad), "tampered tag")
        rejects(lambda: aes.decrypt(nonce, bytes([ciphertext[0] ^ 1]) + ciphertext[1:], aad), "tampered ciphertext")
        rejects(lambda: aes.decrypt(nonce, ciphertext, aad + b"\x00"), "tampered AAD")
        other_kind = "operation" if record["kind"] == "group" else "group"
        wrong_aad = frame(utf8(f"iwut-association-{other_kind}-v1"), utf8(record["identifier"]), utf8(SCHEME), utf8(record["keyVersion"]))
        rejects(lambda: aes.decrypt(nonce, ciphertext, wrong_aad), "wrong encryption purpose")
        other = storage["encryption"][1 if record["kind"] == "group" else 0]
        rejects(lambda: aes.decrypt(nonce, ciphertext, bytes.fromhex(other["aad_hex"])), "cross-record ciphertext transplant")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write deterministic PUBLIC TEST fixtures")
    mode.add_argument("--check", action="store_true", help="check fixture drift and positive/negative protocol cases")
    args = parser.parse_args()
    expected = build_vectors()
    serialized = json.dumps(expected, indent=2, ensure_ascii=False) + "\n"
    validate(expected)
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(serialized, encoding="utf-8")
        print("Wrote validated PUBLIC TEST vectors: " + str(OUTPUT))
    else:
        actual = OUTPUT.read_text(encoding="utf-8")
        require(actual == serialized, "fixture drift: run python3 tools/auth_protocol_vectors.py --write")
        validate(json.loads(actual))
        print("Auth v1 vectors match; signature, encoding, association, Session and AEAD positive/negative checks passed.")


if __name__ == "__main__":
    main()
