"""Anomaly detection + confidence scoring for Fare Enough deal prices.

Implements PROMPT.md pipeline steps 1-2 and 4:
  Baseline: per-route observed prices -> median + lowest normal price.
  Detect:   flag a price that is >=40% below the median, below the lowest
            normal price by a clear margin, or matching a known error-fare
            pattern (extreme outliers are usually wrong currency or a
            missing surcharge).
  Classify: mistake (<35% of median) | flash (<60% of median) | verified.
  Confidence 1-5, with bootstrap caps:
    <7 days observed  -> base 1   (90-day baselines can't exist on day one;
    7-29 days         -> base 2    early deals carry lower confidence until
    30-89 days        -> base 3    the window fills - prompt review note)
    90+ days          -> base 4
    +1 if re-verified live on the source
    mistake fares cap at 3 (may be cancelled; never promise the price)
"""
from statistics import median

MIN_OBS = 5                  # min history observations before we flag at all
BELOW_MEDIAN_RATIO = 0.65    # >=35% below median
BELOW_MIN_NORMAL_RATIO = 0.95  # below lowest-normal by >5%
EXTREME_OUTLIER_RATIO = 0.05   # below 5% of median -> likely error fare


def compute_baseline(history):
    """Return (median, lowest_normal) from observed prices.

    lowest_normal = cheapest price that is not itself already an anomaly
    candidate (> 60% of the median).
    """
    m = median(history)
    normal = [p for p in history if p > BELOW_MEDIAN_RATIO * m]
    ln = min(normal) if normal else None
    return m, ln


def detect_anomaly(candidate, history, currency=None, currency_modal=None):
    """Compare one candidate price against a route's history.

    Returns (reasons, is_extreme). reasons is None when the baseline is
    insufficient or nothing is flagged.
    """
    if len(history) < MIN_OBS:
        return None, False
    m, ln = compute_baseline(history)
    reasons = []
    extreme = False
    if candidate <= BELOW_MEDIAN_RATIO * m:
        reasons.append(
            f"{(1 - candidate / m) * 100:.0f}% below route median "
            f"({candidate:g} vs {m:g})"
        )
    if ln is not None and candidate < BELOW_MIN_NORMAL_RATIO * ln:
        reasons.append(
            f"{(1 - candidate / ln) * 100:.0f}% below lowest normal price "
            f"({candidate:g} vs {ln:g})"
        )
    if candidate < EXTREME_OUTLIER_RATIO * m:
        extreme = True
        reasons.append("extreme outlier (likely wrong currency or missing surcharge)")
    if currency and currency_modal and currency.lower() != currency_modal.lower():
        reasons.append(
            f"currency mismatch: {currency} vs route modal {currency_modal} "
            "(check wrong-currency error pattern)"
        )
    if not reasons:
        return None, False
    return reasons, extreme


def classify(candidate, history, extreme=False):
    """Label a flagged price: mistake | flash (flagged means <60% of median)."""
    m, _ = compute_baseline(history)
    if extreme or candidate < 0.40 * m:
        return "mistake"
    return "flash"


def confidence(observed_days, label, reverified):
    """Confidence score 1-5 (see module docstring for the ladder)."""
    if observed_days < 7:
        base = 1
    elif observed_days < 30:
        base = 2
    elif observed_days < 90:
        base = 3
    else:
        base = 4
    if reverified:
        base += 1
    if label == "mistake":
        base = min(base, 3)
    return max(1, min(5, base))
