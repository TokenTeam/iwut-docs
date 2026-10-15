#!/usr/bin/env python3
"""Public UC032 interoperability fixtures. Never production key material."""
import argparse
import json
import struct
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from auth_protocol_vectors import frame, sha256, fixture_sign, verify, ORDER

OUTPUT = Path(__file__).resolve().parents[1] / "platform/contracts/test-vectors/auth-credential-management-v1.json"

def payload(item):
    return frame(b"iwut-credential-revocation-proof-v1", b"REVOKE_OTHER_CREDENTIAL",
                 item["serviceId"].encode(), b"iwut-client", item["operationId"].encode(),
                 item["sessionId"].encode(), item["callerCredentialId"].encode(),
                 item["targetCredentialId"].encode(), bytes.fromhex(item["challenge_hex"]),
                 struct.pack(">Q", item["expiresAtUnixMs"]))

def build():
    key = ec.derive_private_key(1, ec.SECP256R1()).public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    base = dict(serviceId="iwut-auth-center:test", operationId="11111111-1111-4111-8111-111111111111",
                sessionId="22222222-2222-4222-8222-222222222222",
                callerCredentialId="33333333-3333-4333-8333-333333333333",
                targetCredentialId="44444444-4444-4444-8444-444444444444",
                challenge_hex=bytes(range(32)).hex(), expiresAtUnixMs=1800000300000)
    positives=[]
    variants=[("base",{}),("deployment",{"serviceId":"iwut-auth-center:prod"}),
              ("target",{"targetCredentialId":"55555555-5555-4555-8555-555555555555"}),
              ("session",{"sessionId":"66666666-6666-4666-8666-666666666666"}),
              ("challenge",{"challenge_hex":bytes(range(32,64)).hex()}),
              ("expiry",{"expiresAtUnixMs":1800000300001})]
    for name,changes in variants:
        item=dict(base,**changes);raw=payload(item);sig=fixture_sign(raw);r,s=utils.decode_dss_signature(sig)
        item.update(name=name,signingPayload_hex=raw.hex(),sha256_hex=sha256(raw).hex(),
                    signature_der_hex=sig.hex(),alternateS_signature_der_hex=utils.encode_dss_signature(r,ORDER-s).hex())
        positives.append(item)
    first=positives[0];good=bytes.fromhex(first["signature_der_hex"]);original=payload(base)
    negatives=[dict(name="wrong_"+p["name"],signingPayload_hex=p["signingPayload_hex"],signature_der_hex=good.hex()) for p in positives[1:]]
    for name,raw,sig in [("trailing_payload",original+b"\0",good),("truncated_payload",original[:-1],good),
                         ("double_hash",original,fixture_sign(sha256(original))),
                         ("trailing_der",original,good+b"\0"),
                         ("zero_scalar",original,utils.encode_dss_signature(0,1)),
                         ("out_of_range",original,utils.encode_dss_signature(ORDER,1))]:
        negatives.append(dict(name=name,signingPayload_hex=raw.hex(),signature_der_hex=sig.hex()))
    return dict(warning="PUBLIC TEST DATA ONLY: private scalar=1, never a runtime default",publicKey_hex=key.hex(),positive=positives,negative=negatives)

def check(v):
    key=bytes.fromhex(v["publicKey_hex"])
    for item in v["positive"]:
        raw=payload(item);assert raw.hex()==item["signingPayload_hex"]
        for field in ["signature_der_hex","alternateS_signature_der_hex"]:
            verify(key,raw,bytes.fromhex(item[field]))
    for item in v["negative"]:
        try: verify(key,bytes.fromhex(item["signingPayload_hex"]),bytes.fromhex(item["signature_der_hex"]))
        except Exception: continue
        raise AssertionError("negative accepted: "+item["name"])

def main():
    p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");p.add_argument("--check",action="store_true");args=p.parse_args()
    v=build();check(v);encoded=json.dumps(v,ensure_ascii=False,indent=2)+"\n"
    if args.write: OUTPUT.write_text(encoded)
    if args.check: assert OUTPUT.read_text()==encoded,"credential vectors drifted"
    print("UC032 Frame/DER/negative vectors verified")
if __name__=="__main__": main()
