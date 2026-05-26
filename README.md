# Stripe Test App: The Best Online Shop

A small test harness for the assignment bonus question: mapping the
third-party APIs and SDKs that a Stripe integration depends on, by
capturing and categorizing network traffic.

## Setup

```bash
pip install -r requirements.txt
```

Get **test** API keys from the Stripe Dashboard (Developers → API keys,
with "test mode" on). Then set them in your shell (On cmd):

```bash
set STRIPE_SECRET_KEY=sk_test_51TYi6MDVVFNGeUG7FTjnSy68TxCDVs7GYfzPYH96KbD1BrVFL3I9rcbwsa0l8OsUVwkUyfyhTGqEWGGLY85RmYqD00AozsPSPP
set STRIPE_PUBLISHABLE_KEY=pk_test_51TYi6MDVVFNGeUG7BIAvyUT4ghHMcGN2R3boBsQJScSVmyxE3UbY7QiMK3tlA4yzXItewcviBqPzy427SLV4P51l00oazDik7L
```

On Windows (powershell):
```bash
$env:STRIPE_SECRET_KEY = "sk_test_51TYi6MDVVFNGeUG7FTjnSy68TxCDVs7GYfzPYH96KbD1BrVFL3I9rcbwsa0l8OsUVwkUyfyhTGqEWGGLY85RmYqD00AozsPSPP"
$env:STRIPE_PUBLISHABLE_KEY = "pk_test_51TYi6MDVVFNGeUG7BIAvyUT4ghHMcGN2R3boBsQJScSVmyxE3UbY7QiMK3tlA4yzXItewcviBqPzy427SLV4P51l00oazDik7L"
```

On Linux:
```bash
export STRIPE_SECRET_KEY=sk_test_51TYi6MDVVFNGeUG7FTjnSy68TxCDVs7GYfzPYH96KbD1BrVFL3I9rcbwsa0l8OsUVwkUyfyhTGqEWGGLY85RmYqD00AozsPSPP
export STRIPE_PUBLISHABLE_KEY=pk_test_51TYi6MDVVFNGeUG7BIAvyUT4ghHMcGN2R3boBsQJScSVmyxE3UbY7QiMK3tlA4yzXItewcviBqPzy427SLV4P51l00oazDik7L
```
## Run: three terminals

Ideally use a virtual environment to install all the packages in.

**Terminal 1: the Flask app**

```bash
python app/server.py
# serves http://127.0.0.1:5000
```

**Terminal 2: mitmproxy capture**

```bash
mitmdump -s analysis/capture_addon.py -w captures/stripe_flows.mitm
# proxy listens on 127.0.0.1:8080 by default
```

The addon prints a categorized one-line summary per flow and also writes
`captures/flows.jsonl` for the analysis step. The `.mitm` file holds the
full raw capture.

**Terminal 3 (or your browser): generate traffic**

1. Point your browser's proxy at `127.0.0.1:8080`.
   (Firefox has its own proxy setting, which is cleaner than touching
   system-wide settings.)
2. Install the mitmproxy CA certificate so HTTPS can be decrypted:
   with the proxy running, visit <http://mitm.it> in the proxied
   browser and follow the instructions for your OS/browser.
3. Visit <http://127.0.0.1:5000>.
4. Press the Pay button.

You should see `js.stripe.com`, `api.stripe.com`, `m.stripe.com` and
`r.stripe.com` appear in Terminal 2 as the page loads and you pay.

## Analyze

```bash
python analysis/analyze.py
```

This reads `captures/flows.jsonl` and prints a per-category and per-host
breakdown, plus a third-party surface map. It also writes
`captures/summary_by_host.csv` for inclusion in the report.

## Reading the results: what each host is

| Host             | Category   | Role                                            |
|------------------|------------|-------------------------------------------------|
| `js.stripe.com`  | sdk        | Delivers the Stripe.js SDK (a CDN dependency)    |
| `api.stripe.com` | api        | Core REST API — PaymentIntents, confirmation     |
| `m.stripe.com`   | telemetry  | Device fingerprinting / fraud-detection telemetry|
| `r.stripe.com`   | analytics  | Analytics, event and error reporting             |

The server-side call (Flask → `api.stripe.com`) and the client-side
calls (browser → the other hosts) together give you both halves of the
API-only vs. browser-based comparison.
