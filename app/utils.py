import hmac
import hashlib
import os
import logging

def verify_signature(payload, signature):
    secret = os.getenv("GITHUB_SECRET", "your_secret_here")
    logging.info(f"verify_signature secret:{secret}")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)
