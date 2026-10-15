#!/usr/bin/env python3
"""PUBLIC TEST password v1 vectors. Requires cryptography and argon2-cffi.

The independent libargon2 binding produces the hash checked by Go's x/crypto.
No SMTP/network, production secrets, or password blocklist is used here.
"""
import argparse
import hashlib
import hmac
import json
import struct
import unicodedata
from pathlib import Path

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from auth_protocol_vectors import frame, unframe, fixture_sign, verify, require, rejects, ORDER

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-password-v1.json"


def u64(v):
    return struct.pack(">Q", v)


def build_vectors():
    private = ec.derive_private_key(1, ec.SECP256R1())
    key = private.public_key().public_bytes(serialization.Encoding.X962,
                                         serialization.PublicFormat.UncompressedPoint)
    secret = bytes(range(32))
    context = dict(authId="opaque-test-owner", requestId="11111111-1111-4111-8111-111111111111",
                   operationId="22222222-2222-4222-8222-222222222222",
                   sessionId="33333333-3333-4333-8333-333333333333",
                   serviceId="iwut-auth-center:test", accountRevision=7,
                   passwordRevision=3, loginRoleRevision=4,
                   expiresAtUnixMs=1791811200000, normalizedLoginEmail="a@whut.edu.cn",
                   code="00001234", currentPassword=" first test password é ",
                   newPassword=" second test password é ")
    c = context
    payload = frame(b"iwut-password-login-proof-v1", b"iwut-password-login-v1",
                    b"LOGIN_WITH_PASSWORD", c["serviceId"].encode(), b"iwut-client",
                    c["operationId"].encode(), bytes(range(32)), u64(c["expiresAtUnixMs"]),
                    key, c["normalizedLoginEmail"].encode())
    signature = fixture_sign(payload)
    r, s = utils.decode_dss_signature(signature)
    inputs = {}
    inputs["change"] = frame(b"iwut-password-change-request-v1", c["authId"].encode(),
                             c["requestId"].encode(), c["sessionId"].encode(),
                             u64(c["accountRevision"]), u64(c["passwordRevision"]),
                             c["currentPassword"].encode(), c["newPassword"].encode())
    inputs["resetRequest"] = frame(b"iwut-password-reset-request-v1", c["requestId"].encode(),
                                   c["normalizedLoginEmail"].encode(), c["serviceId"].encode(), b"iwut-client")
    request_mac = hmac.digest(secret, inputs["resetRequest"], "sha256")
    inputs["resetCode"] = frame(b"iwut-password-reset-code-v1", b"RESET_PASSWORD",
                                c["operationId"].encode(), c["authId"].encode(),
                                u64(c["loginRoleRevision"]), u64(c["passwordRevision"]),
                                u64(c["accountRevision"]), u64(c["expiresAtUnixMs"]),
                                request_mac, c["code"].encode())
    code_mac = hmac.digest(secret, inputs["resetCode"], "sha256")
    inputs["resetCompletion"] = frame(b"iwut-password-reset-completion-v1", c["operationId"].encode(),
                                      code_mac, c["newPassword"].encode())
    hash_vectors = []
    for raw in ("a test password é", "a test password e\u0301", "  a test password  "):
        normalized = unicodedata.normalize("NFC", raw)
        salt = bytes(range(16))
        output = hash_secret_raw(normalized.encode(), salt, time_cost=2,
                                 memory_cost=19456, parallelism=1, hash_len=32, type=Type.ID, version=19)
        hash_vectors.append(dict(input=raw, normalized=normalized, salt_hex=salt.hex(), hash_hex=output.hex()))
    fields = unframe(payload, 10)
    negatives = []
    for i in range(10):
        changed = fields.copy()
        changed[i] = changed[i] + b"x"
        bad = frame(*changed)
        negatives.append(dict(name="tamper_field_"+str(i), payload_hex=bad.hex(),
                              signature_der_hex=signature.hex(), expected="REJECT"))
    for name, bad in (("trailing_der", signature+b"\x00"),
                      ("double_hash", fixture_sign(hashlib.sha256(payload).digest())),
                      ("raw_rs", r.to_bytes(32,"big")+s.to_bytes(32,"big"))):
        negatives.append(dict(name=name, payload_hex=payload.hex(), signature_der_hex=bad.hex(), expected="REJECT"))
    return dict(warning="PUBLIC TEST SECRETS/SALTS/PASSWORDS/KEYS. NEVER USE IN PRODUCTION.",
                contract="auth-password-v1", context=context, operationKey_hex=secret.hex(),
                keyId_hex=hashlib.sha256(frame(b"iwut-password-operation-key-id-v1",secret)).hexdigest(),
                login=dict(publicKey65_hex=key.hex(), challenge_hex=bytes(range(32)).hex(),
                           signingPayload_hex=payload.hex(), signature_der_hex=signature.hex(),
                           equivalentS_signature_der_hex=utils.encode_dss_signature(r,ORDER-s).hex()),
                macs={name:dict(input_hex=raw.hex(),mac_hex=hmac.digest(secret,raw,"sha256").hex())
                      for name,raw in inputs.items()},
                argon2id=dict(version=19,memoryKiB=19456,iterations=2,parallelism=1,
                             normalizationVersion="nfc-unicode-15.0.0",vectors=hash_vectors),
                negativeProofs=negatives)


def validate(v):
    login = v["login"]
    payload = bytes.fromhex(login["signingPayload_hex"])
    key = bytes.fromhex(login["publicKey65_hex"])
    for field in ("signature_der_hex","equivalentS_signature_der_hex"):
        verify(key,payload,bytes.fromhex(login[field]))
    for negative in v["negativeProofs"]:
        rejects(lambda n=negative: verify(key,bytes.fromhex(n["payload_hex"]),bytes.fromhex(n["signature_der_hex"])),negative["name"])
    hashes = v["argon2id"]["vectors"]
    require(hashes[0]["hash_hex"]==hashes[1]["hash_hex"],"NFC equivalence")
    require(hashes[2]["normalized"].startswith("  "),"spaces lost")
    require(len(unframe(payload,10))==10,"field count")


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    vectors=build_vectors()
    validate(vectors)
    output=json.dumps(vectors,ensure_ascii=False,indent=2)+"\n"
    if args.write:
        OUTPUT.write_text(output,encoding="utf-8")
        print("wrote",OUTPUT)
    else:
        require(OUTPUT.read_text(encoding="utf-8")==output,"password vector drift")
        print("password v1 vectors verified (independent libargon2)")


if __name__ == "__main__":
    main()
