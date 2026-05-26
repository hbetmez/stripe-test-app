"""
Two jobs:
  1. Serve the checkout page (templates/checkout.html) with the publishable key injected.
  2. Expose /create-payment-intent, which makes a SERVER-SIDE call to api.stripe.com.
     This is the server-to-server half of the traffic comparison. It carries the
     SECRET key and is the call you will see if you proxy the whole machine.

All keys are read from environment variables so no secrets live in the repo.
Use Stripe TEST keys only (publishable: pk_test_..., secret: sk_test_...).
"""

import os
import stripe
from flask import Flask, render_template, jsonify, request

# -- Stripe configuration --
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

stripe.api_key = STRIPE_SECRET_KEY

app = Flask(__name__)

@app.route("/")
def index():
    """Serve the checkout page with the publishable key injected."""
    return render_template("checkout.html",
                           publishable_key=STRIPE_PUBLISHABLE_KEY)


@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    """
    Server-side call to api.stripe.com.

    This is the backend half of the traffic you are mapping. The browser never
    sees the secret key; it only receives the client_secret needed to confirm
    the payment from Stripe.js.
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=9999,
            currency="eur",
            automatic_payment_methods={"enabled": True},
            description="Test payment",
        )
        return jsonify({"clientSecret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # host=127.0.0.1 keeps it local; the browser is what you point at the proxy.
    app.run(host="127.0.0.1", port=5000, debug=True)
