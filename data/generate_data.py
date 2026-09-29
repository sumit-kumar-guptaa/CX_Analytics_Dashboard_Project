"""
Generate the SIMULATED customer-support dataset for the CX Analytics Dashboard.

Output
------
raw_support_tickets.csv    10,300 rows x 11 columns  (what lands in PostgreSQL staging)
    = 9,870 clean unique tickets
    + 130 incomplete records (missing csat / resolution / agent / etc.)
    + 300 exact duplicate rows

clean_* CSVs are produced by the SQL pipeline; they are also written here so the
Excel / Power BI steps can be run without a database.

All data is synthetic. Seeded for reproducibility.
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)
OUT = Path(__file__).parent

# ---- targets (kept identical to the resume bullets) -------------------------
N_CLEAN, N_INCOMPLETE, N_DUP = 9_870, 130, 300
N_UNIQUE = N_CLEAN + N_INCOMPLETE          # 10,000
N_RAW = N_UNIQUE + N_DUP                   # 10,300
N_CHAT = 3_385                             # 3385 / 9870 = 34.3 %
N_LATE = 2_170                             # tickets resolved after 24h
LATE_MEAN, FAST_MEAN_SUM = 2.900, 31_062   # late mean = 6293/2170 ; fast sum -> 4.034

CHANNELS = ["Chat", "Email", "Phone", "Social Media", "Web Form"]
OTHER_CH_P = [0.42, 0.27, 0.13, 0.18]      # split of the non-chat tickets
CATEGORIES = ["Technical Issue", "Billing", "Account Access", "Delivery", "Refund", "Product Inquiry"]
CAT_P = [0.27, 0.20, 0.14, 0.17, 0.11, 0.11]
REGIONS = ["North", "South", "East", "West", "Central"]
REGION_P = [0.22, 0.27, 0.18, 0.21, 0.12]

# ---- dimension data ---------------------------------------------------------
N_CUST, N_AGENT = 4_000, 40
first = ["Aarav", "Vivaan", "Aditya", "Diya", "Ananya", "Ishaan", "Kavya", "Rohan", "Meera", "Arjun",
         "Sneha", "Kabir", "Riya", "Neha", "Rahul", "Priya", "Vikram", "Pooja", "Aman", "Tara"]
last = ["Sharma", "Verma", "Gupta", "Iyer", "Nair", "Reddy", "Patel", "Singh", "Das", "Rao"]
agent_names = [f"{first[i % 20]} {last[(i * 3 + (i // 20) * 5) % 10]}" for i in range(N_AGENT)]
agents = pd.DataFrame({"agent_id": [f"AG{str(i+1).zfill(3)}" for i in range(N_AGENT)],
                       "agent_name": agent_names})
customers = pd.DataFrame({
    "customer_id": [f"CU{str(i+1).zfill(5)}" for i in range(N_CUST)],
    "customer_region": rng.choice(REGIONS, N_CUST, p=REGION_P),
})

# ---- ticket base (10,000 unique) -------------------------------------------
ids = [f"TKT{str(i+1).zfill(6)}" for i in range(N_UNIQUE)]
t = pd.DataFrame({"ticket_id": ids})
t["customer_id"] = rng.choice(customers.customer_id, N_UNIQUE)
t["agent_id"] = rng.choice(agents.agent_id, N_UNIQUE)

# Channel: exactly N_CHAT chat tickets inside the 9,870 clean ones
clean_idx = np.arange(N_CLEAN)
inc_idx = np.arange(N_CLEAN, N_UNIQUE)
ch = np.empty(N_UNIQUE, dtype=object)
chat_pos = rng.choice(clean_idx, N_CHAT, replace=False)
mask = np.zeros(N_CLEAN, bool); mask[chat_pos] = True
ch[:N_CLEAN][mask] = "Chat"
ch[:N_CLEAN][~mask] = rng.choice(CHANNELS[1:], (~mask).sum(), p=OTHER_CH_P)
ch[N_CLEAN:] = rng.choice(CHANNELS, N_INCOMPLETE)
t["channel"] = ch
t["category"] = rng.choice(CATEGORIES, N_UNIQUE, p=CAT_P)

# Created timestamp: calendar year 2025, mild weekday / business-hour skew
days = rng.integers(0, 365, N_UNIQUE)
_hw = np.array([1, 1, 1, 1, 1, 2, 3, 5, 8, 9, 9, 8, 7, 8, 9, 9, 8, 7, 6, 5, 4, 3, 2, 1], dtype=float)
hours = rng.choice(np.arange(24), N_UNIQUE, p=_hw / _hw.sum())
mins = rng.integers(0, 60, N_UNIQUE)
t["created_at"] = (pd.Timestamp("2025-01-01") + pd.to_timedelta(days, "D")
                   + pd.to_timedelta(hours, "h") + pd.to_timedelta(mins, "m"))

# First response time (minutes) - depends on channel
fr_med = {"Chat": 2, "Phone": 4, "Web Form": 55, "Email": 140, "Social Media": 90}
t["first_response_minutes"] = [
    round(float(np.clip(rng.lognormal(np.log(fr_med[c]), 0.55), 1, 900)), 1) for c in t.channel]

# Resolution: exactly N_LATE clean tickets resolved after 24h (weighted by channel/category)
w = np.where(t.channel[:N_CLEAN] == "Email", 1.4, np.where(t.channel[:N_CLEAN] == "Chat", 0.7, 1.0)) \
    * np.where(t.category[:N_CLEAN].isin(["Technical Issue", "Refund"]), 1.5, 1.0)
late_pos = rng.choice(clean_idx, N_LATE, replace=False, p=w / w.sum())
late = np.zeros(N_UNIQUE, bool); late[late_pos] = True
late[N_CLEAN:] = rng.random(N_INCOMPLETE) < 0.22
res = np.where(late,
               np.round(rng.uniform(24.5, 72, N_UNIQUE), 1),
               np.round(np.clip(rng.gamma(2.2, 3.2, N_UNIQUE), 0.3, 23.9), 1))
t["resolution_hours"] = res

# CSAT: exact group means (late = 2.900, fast sum = 31,062 -> 4.034)
def draw_scores(n, target_sum, probs):
    s = rng.choice([1, 2, 3, 4, 5], n, p=probs)
    diff = int(target_sum - s.sum())
    while diff != 0:
        step = 1 if diff > 0 else -1
        cand = np.where(s < 5)[0] if step > 0 else np.where(s > 1)[0]
        k = min(abs(diff), 200)
        s[rng.choice(cand, k, replace=False)] += step
        diff -= step * k
    return s

csat = np.zeros(N_UNIQUE, int)
cl = np.zeros(N_UNIQUE, bool); cl[:N_CLEAN] = True
lm, fm = cl & late, cl & ~late
csat[lm] = draw_scores(lm.sum(), round(LATE_MEAN * lm.sum()), [.18, .27, .28, .17, .10])
csat[fm] = draw_scores(fm.sum(), FAST_MEAN_SUM, [.02, .04, .14, .38, .42])
csat[N_CLEAN:] = rng.integers(1, 6, N_INCOMPLETE)
t["csat_score"] = csat

# ---- lookup columns that make the raw file 11 columns wide ------------------
t = t.merge(customers, on="customer_id", how="left").merge(agents, on="agent_id", how="left")
cols = ["ticket_id", "customer_id", "customer_region", "agent_id", "agent_name", "channel",
        "category", "created_at", "first_response_minutes", "resolution_hours", "csat_score"]
t = t[cols]
assert t.shape[1] == 11

# ---- 130 incomplete records: blank out required fields ----------------------
inc = t.index[N_CLEAN:]
fields = ["csat_score", "resolution_hours", "agent_id", "first_response_minutes", "channel"]
t[["csat_score", "resolution_hours", "first_response_minutes"]] = \
    t[["csat_score", "resolution_hours", "first_response_minutes"]].astype(float)
for i in inc:
    for f in rng.choice(fields, rng.integers(1, 3), replace=False):
        t.loc[i, f] = np.nan
        if f == "agent_id":
            t.loc[i, "agent_name"] = np.nan

# ---- 300 exact duplicates of clean rows, then shuffle -----------------------
dups = t.iloc[rng.choice(clean_idx, N_DUP, replace=False)]
raw = pd.concat([t, dups], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
assert len(raw) == N_RAW

raw.to_csv(OUT / "raw_support_tickets.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

# ---- clean outputs (same logic the SQL pipeline applies) --------------------
clean = raw.drop_duplicates().dropna().sort_values("ticket_id").reset_index(drop=True)
assert len(clean) == N_CLEAN, len(clean)
clean["csat_score"] = clean.csat_score.astype(int)
clean.to_csv(OUT / "clean_support_tickets.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
clean[["customer_id", "customer_region"]].drop_duplicates().sort_values("customer_id") \
    .to_csv(OUT / "dim_customers.csv", index=False)
clean[["agent_id", "agent_name"]].drop_duplicates().sort_values("agent_id") \
    .to_csv(OUT / "dim_agents.csv", index=False)
clean[["ticket_id", "customer_id", "agent_id", "channel", "category", "created_at",
       "first_response_minutes", "resolution_hours", "csat_score"]] \
    .to_csv(OUT / "fact_tickets.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

# ---- verification printout --------------------------------------------------
late_m, fast_m = clean[clean.resolution_hours > 24].csat_score.mean(), \
    clean[clean.resolution_hours <= 24].csat_score.mean()
print("raw rows       :", len(raw), "| duplicates:", raw.duplicated().sum(),
      "| incomplete (unique):", raw.drop_duplicates().isna().any(axis=1).sum())
print("clean rows     :", len(clean))
print("chat share     : %.2f%%" % (100 * (clean.channel == "Chat").mean()))
print("CSAT >24h      : %.4f | <=24h: %.4f | drop: %.2f%%" % (late_m, fast_m, 100 * (1 - late_m / fast_m)))
