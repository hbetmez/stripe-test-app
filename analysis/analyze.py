"""
Analysis script for the Stripe CI-probe.

Reads captures/flows.jsonl (produced by the mitmproxy addon) and produces:
  - A per-category summary (count, total bytes).
  - A per-host breakdown with descriptions.
  - A simple text "map" of the third-party surface for the write-up.

Run with:
    python analysis/analyze.py

Requires: pandas  (pip install pandas)
"""

import json
import os
import sys
import pandas as pd

JSONL_PATH = os.path.join(os.path.dirname(__file__), "..", "captures", "flows.jsonl")


def load_flows(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        sys.exit(f"No capture file found at {path}. "
                 f"Run a capture first (see README).")
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        sys.exit("Capture file is empty.")
    return pd.DataFrame(rows)


def main():
    df = load_flows(JSONL_PATH)

    print("=" * 64)
    print(f"Loaded {len(df)} flows from capture.")
    print("=" * 64)

    # --- Per-category summary --------------------------------------------
    print("\n--- Traffic by category ---")
    cat = (df.groupby("category")
             .agg(requests=("host", "size"),
                  total_bytes=("resp_size", "sum"))
             .sort_values("requests", ascending=False))
    print(cat.to_string())

    # --- Per-host breakdown ----------------------------------------------
    print("\n--- Traffic by host ---")
    host = (df.groupby(["category", "host", "description"])
              .agg(requests=("method", "size"),
                   methods=("method", lambda s: ",".join(sorted(set(s)))),
                   bytes=("resp_size", "sum"))
              .sort_values("requests", ascending=False))
    print(host.to_string())

    # --- Per-endpoint breakdown (path + content type) --------------------
    # Groups by the individual path so you can see exactly what was fetched
    # and what kind of resource it was (JS, JSON, CSS, image, telemetry...).
    print("\n--- Traffic by endpoint (path + content type) ---")

    def short_path(p, limit=55):
        """Trim long paths (and drop query strings) for readable output."""
        p = str(p).split("?")[0]
        return p if len(p) <= limit else p[:limit - 3] + "..."

    ep_df = df.copy()
    ep_df["endpoint"] = ep_df["path"].apply(short_path)
    # Prefer the response content type; fall back to request content type.
    ep_df["content_type"] = (ep_df["resp_content_type"]
                             .replace("", pd.NA)
                             .fillna(ep_df["req_content_type"])
                             .fillna("")
                             .apply(lambda c: str(c).split(";")[0]))  # strip charset

    endpoint = (ep_df.groupby(["category", "host", "endpoint", "content_type"])
                     .agg(requests=("method", "size"),
                          methods=("method", lambda s: ",".join(sorted(set(s)))),
                          bytes=("resp_size", "sum"))
                     .sort_values(["category", "bytes"], ascending=[True, False]))
    print(endpoint.to_string())

    # --- Three-way surface map -------------------------------------------
    print("\n--- Surface map (for the write-up) ---")

    STRIPE_CATS = {"sdk", "telemetry", "analytics", "api", "stripe-other"}

    stripe_df = df[df["category"].isin(STRIPE_CATS)]
    noise_df = df[df["category"] == "browser-noise"]
    other_df = df[df["category"] == "third-party"]

    stripe_hosts = stripe_df["host"].unique()
    noise_hosts = noise_df["host"].unique()
    other_hosts = other_df["host"].unique()

    # 1. The part that matters: Stripe's own infrastructure.
    print(f"\n[1] Stripe infrastructure observed ({len(stripe_hosts)} hosts):")
    for h in sorted(stripe_hosts):
        row = df[df["host"] == h].iloc[0]
        n = (df["host"] == h).sum()
        print(f"  - {h}  ({row['category']}, {n} requests): {row['description']}")

    # 2. Genuine non-Stripe third parties (should be ~none for this harness).
    print(f"\n[2] Genuine non-Stripe third parties ({len(other_hosts)} hosts):")
    if len(other_hosts) == 0:
        print("  (none -- expected for an isolated test harness; see README note)")
    else:
        for h in sorted(other_hosts):
            print(f"  - {h}")

    # 3. Browser noise -- filtered out, reported only for transparency.
    print(f"\n[3] Browser background noise -- excluded from analysis "
          f"({len(noise_hosts)} hosts, {len(noise_df)} requests):")
    for h in sorted(noise_hosts):
        print(f"  - {h}")
    print("  ^ Firefox's own traffic (telemetry, captive-portal checks, "
          "new-tab tiles, search suggestions). Not part of the Stripe story.")

    # --- Save CSVs for inclusion in the report ---------------------------
    captures_dir = os.path.join(os.path.dirname(__file__), "..", "captures")
    host_csv = os.path.join(captures_dir, "summary_by_host.csv")
    endpoint_csv = os.path.join(captures_dir, "summary_by_endpoint.csv")
    host.reset_index().to_csv(host_csv, index=False)
    endpoint.reset_index().to_csv(endpoint_csv, index=False)
    print(f"\nSaved per-host summary to     {host_csv}")
    print(f"Saved per-endpoint summary to {endpoint_csv}")


if __name__ == "__main__":
    main()