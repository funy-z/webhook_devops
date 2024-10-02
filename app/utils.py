import hmac
import hashlib
import os

def verify_signature(payload, signature):
    secret = os.getenv("GITHUB_SECRET", "your_secret_here")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)
