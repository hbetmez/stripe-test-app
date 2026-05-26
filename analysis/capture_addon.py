import json
import os
from datetime import datetime, timezone

# Map known Stripe hosts to a category + short description.
STRIPE_HOSTS = {
    "js.stripe.com":  ("sdk",       "Stripe.js SDK delivery (CDN)"),
    "m.stripe.com":   ("telemetry", "Device fingerprinting / fraud telemetry"),
    "m.stripe.network": ("telemetry", "Fraud telemetry (alt host)"),
    "r.stripe.com":   ("analytics", "Analytics / event + error reporting"),
    "api.stripe.com": ("api",       "Core REST API (PaymentIntents etc.)"),
    "q.stripe.com":   ("analytics", "Pixel / metrics beacon"),
    "b.stripecdn.com": ("sdk",      "Stripe CDN asset host"),
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "captures")
JSONL_PATH = os.path.join(OUT_DIR, "flows.jsonl")


def classify(host: str):
    """Return (category, description) for a host."""
    if host in STRIPE_HOSTS:
        return STRIPE_HOSTS[host]
    if "stripe" in host:
        return ("stripe-other", f"Unrecognized Stripe-related host: {host}")
    return ("third-party", f"Non-Stripe host: {host}")


def response(flow):
    """Called by mitmproxy once a response is received for a flow."""
    host = flow.request.pretty_host
    category, description = classify(host)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "category": category,
        "description": description,
        "method": flow.request.method,
        "path": flow.request.path,
        "status": flow.response.status_code if flow.response else None,
        "req_content_type": flow.request.headers.get("content-type", ""),
        "resp_content_type": (flow.response.headers.get("content-type", "")
                              if flow.response else ""),
        "req_size": len(flow.request.raw_content or b""),
        "resp_size": len(flow.response.raw_content or b"") if flow.response else 0,
    }

    # Live one-line summary
    print(f"[{category:>12}] {flow.request.method:>4} {host}{flow.request.path[:60]}")

    # Append to JSONL for pandas
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(JSONL_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
