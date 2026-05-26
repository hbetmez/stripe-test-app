/*
 * Client-side Stripe.js logic.
 *
 * This is where the CLIENT-SIDE traffic originates. When this code runs you
 * will see, in the mitmproxy capture:
 *   - js.stripe.com   -> the SDK itself (loaded by the <script> tag in HTML)
 *   - m.stripe.com    -> device fingerprinting / fraud telemetry, fired
 *                        automatically by Stripe.js on initialization
 *   - r.stripe.com    -> analytics / error + event reporting
 *   - api.stripe.com  -> confirmCardPayment / confirmPayment calls
 *
 * The flow:
 *   1. Initialize Stripe with the publishable key.
 *   2. Ask our Flask backend for a PaymentIntent (backend calls api.stripe.com).
 *   3. Mount the Payment Element using the returned client_secret.
 *   4. On submit, confirm the payment directly with Stripe from the browser.
 */

const stripe = Stripe(window.STRIPE_PUBLISHABLE_KEY);

let elements;

initialize();

document.querySelector("#submit").addEventListener("click", handleSubmit);

async function initialize() {
  // Step 2: backend creates the PaymentIntent (server -> api.stripe.com)
  const res = await fetch("/create-payment-intent", { method: "POST" });
  const data = await res.json();

  if (data.error) {
    showMessage("Backend error: " + data.error);
    return;
  }

  // Step 3: mount the Payment Element with the client secret
  elements = stripe.elements({ clientSecret: data.clientSecret });
  const paymentElement = elements.create("payment");
  paymentElement.mount("#payment-element");
}

async function handleSubmit(e) {
  e.preventDefault();
  setLoading(true);

  // Step 4: confirm the payment (browser -> api.stripe.com, plus telemetry)
  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      // return_url is required; it just reloads this page in test mode
      return_url: window.location.href,
    },
    redirect: "if_required",
  });

  if (error) {
    showMessage(error.message);
  } else {
    showMessage("Test payment succeeded. Check the mitmproxy capture.");
  }

  setLoading(false);
}

function showMessage(text) {
  const el = document.querySelector("#message");
  el.textContent = text;
}

function setLoading(isLoading) {
  document.querySelector("#submit").disabled = isLoading;
  document.querySelector("#button-text").textContent =
    isLoading ? "Processing..." : "Pay \u20AC99.99";
}
