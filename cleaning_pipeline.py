"""Reusable agent-network cleaning with auditable, data-driven rules."""
import numpy as np
import pandas as pd


def clean_agent_data(txns, agents):
    """Return (clean_df, log) without mutating inputs.

    Keep one record per txn_id. Where duplicate records differ only in agent_id,
    prefer the ID present in the register, then the first occurrence. Reject
    conflicting financial/date/type fields for source reconciliation. Normalise
    types, impute missing/invalid/nonpositive amounts with the valid median,
    flag both IQR tails on observed valid amounts, and preserve unknown agents
    in a validated left join. The log is a list of structured event dictionaries.
    """
    required = {"txn_id", "agent_id", "txn_type", "amount", "txn_date"}
    if not required.issubset(txns.columns):
        raise ValueError("Transactions are missing required columns.")
    if not {"agent_id", "county", "onboarded"}.issubset(agents.columns):
        raise ValueError("Agent register is missing required columns.")
    if agents["agent_id"].isna().any() or agents["agent_id"].duplicated().any():
        raise ValueError("Agent register keys must be nonmissing and unique.")
    if txns["txn_id"].isna().any():
        raise ValueError("Missing txn_id requires source reconciliation.")
    out = txns.copy(deep=True)
    register = agents.copy(deep=True)
    log = []

    def record(rule, rows, detail):
        log.append({"rule": rule, "rows_affected": int(rows), "detail": detail})

    record("Input rows", len(out), "Raw transaction extract")
    duplicates = out.loc[out["txn_id"].duplicated(keep=False)]
    # Only an agent-ID disagreement is resolvable with the provided register.
    conflict_fields = ["txn_type", "amount", "txn_date"]
    if not duplicates.empty:
        conflicts = duplicates.groupby("txn_id")[conflict_fields].nunique(dropna=False)
        if conflicts.gt(1).any(axis=None):
            raise ValueError("Duplicate txn_id has conflicting financial/type/date values.")
    conflicts_agent = duplicates.groupby("txn_id")["agent_id"].nunique().gt(1).sum()
    record("Duplicate IDs with conflicting agents", conflicts_agent,
           "Prefer registered ID only when all other fields agree")
    out["_known_agent"] = out["agent_id"].isin(register["agent_id"])
    before = len(out)
    out = (out.sort_values("_known_agent", ascending=False, kind="stable")
           .drop_duplicates("txn_id", keep="first")
           .sort_index().drop(columns="_known_agent").copy())
    record("Duplicate transactions removed", before - len(out), "One record per txn_id")

    canonical_type = out["txn_type"].astype("string").str.strip().str.title()
    if not canonical_type.isin(["Deposit", "Withdrawal"]).all():
        raise ValueError("Unexpected or missing transaction type requires source review.")
    record("Transaction labels standardised", out["txn_type"].ne(canonical_type).sum(),
           "Trimmed whitespace and normalised case")
    out["txn_type"] = canonical_type

    raw_amount = out["amount"]
    numeric = pd.to_numeric(raw_amount, errors="coerce").astype(float)
    invalid = numeric.isna() | ~np.isfinite(numeric) | numeric.le(0)
    observed = numeric.mask(invalid)
    median = observed.median()
    if pd.isna(median):
        raise ValueError("No valid positive amounts available for imputation.")
    q1, q3 = observed.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    out["amount_imputed"] = invalid
    out["is_outlier"] = observed.lt(lower) | observed.gt(upper)
    out["amount"] = observed.fillna(median)
    record("Amounts imputed", invalid.sum(), f"Median of observed valid amounts = KES {median:,.2f}")
    record("IQR outliers retained", out["is_outlier"].sum(),
           f"Observed-value fences [{lower:.2f}, {upper:.2f}]; no automatic deletion")
    record("KES 250,000 records retained", observed.eq(250000).sum(),
           "Check source receipts/ledger and authorisation; no unsupported correction")

    date_text = out["txn_date"].astype("string").str.strip()
    slash_dates = date_text.str.contains("/", na=False)
    parsed_dates = pd.to_datetime(date_text.str.replace("/", "-", regex=False),
                                  format="%Y-%m-%d", errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError("Unparseable transaction date requires source reconciliation.")
    out["txn_date"] = parsed_dates
    record("Date separators normalised", slash_dates.sum(), "YYYY/MM/DD converted to datetime")
    register["onboarded"] = pd.to_datetime(register["onboarded"], format="%Y-%m-%d", errors="raise")
    premerge = len(out)
    out = out.merge(register, on="agent_id", how="left", validate="many_to_one", indicator=True)
    if len(out) != premerge:
        raise AssertionError("Merge changed transaction count.")
    out["unknown_agent"] = out["_merge"].eq("left_only")
    if out.loc[~out["unknown_agent"], "county"].isna().any():
        raise ValueError("Registered agent has missing county.")
    out["county"] = out["county"].fillna("Unknown")
    out = out.drop(columns="_merge")
    record("Transactions with unknown agents", out["unknown_agent"].sum(),
           "Preserved under county Unknown; no guessed county")
    record("Transactions before agent onboarding", out["txn_date"].lt(out["onboarded"]).sum(),
           "Temporal plausibility check; NaT for unknown agents excluded")
    record("Post-merge rows", len(out), "Left join validated many_to_one")
    assert out["txn_id"].is_unique
    assert out["amount"].notna().all()
    assert out["txn_type"].isin(["Deposit", "Withdrawal"]).all()
    return out.reset_index(drop=True), log
