import json
import os
import py_vapid

vapid: py_vapid.Vapid02 = None
claims: dict = None

def load_vapid():
    global vapid, claims

    webpush_dir = os.path.join("data", "vapid")
    os.makedirs(webpush_dir, exist_ok=True)

    private_path = os.path.join(webpush_dir, "vapid_private_key.pem")
    public_path = os.path.join(webpush_dir, "vapid_public_key.pem")
    claims_path = os.path.join(webpush_dir, "vapid_claims.json")

    if not os.path.isfile(private_path):
        vapid = py_vapid.Vapid02()
        vapid.generate_keys()
        vapid.save_key(private_path)
        vapid.save_public_key(public_path)
    else:
        vapid = py_vapid.Vapid02.from_file(private_path)

    if not os.path.isfile(claims_path):
        claims = {
            "sub": f"mailto:test@example.com",  # TODO
        }
        with open(claims_path, "wt", encoding="utf-8") as fh:
            json.dump(claims, fh)
    else:
        with open(claims_path, "rt", encoding="utf-8") as fh:
            claims = json.load(fh)
