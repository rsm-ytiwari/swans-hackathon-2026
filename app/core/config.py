"""Firm configuration: how this firm's Clio account names things.

Nothing here is specific to one matter. A different firm edits this file (custom field names, stage
labels, how contact roles are described) and the app works on its matters unchanged.
"""

# Our concept -> the custom field name this firm uses in Clio.
FIELDS = {
    "incident_date": "Date of Incident",
    "location": "Accident Location",
    "summary": "Case Summary",
    "carrier": "Insurance Carrier",
    "claim_number": "Claim Number",
    "policy_limits": "Policy Limits",
    "policy_limits_confirmed": "Policy Limits Confirmed",
    "case_value": "Estimated Case Value",
    "case_value_rationale": "Case Value Rationale",
    "specials": "Medical Specials To Date",
    "wage_loss": "Wage Loss Claimed",
    "liability": "Liability Assessment",
    "treatment_status": "Treatment Status",
    "liens": "Health Insurance or Lien Holder",
    "prior_injuries": "Prior Related Injuries",
    "hipaa_received": "HIPAA Authorization Received",
}

# Custom fields that are case strategy. They never reach a provider, whatever the sharing policy says.
STRATEGY_FIELDS = {"case_value", "case_value_rationale", "liability", "prior_injuries", "wage_loss"}

# Contact role, decided from the relationship description in Clio (first match wins, lowercase).
ROLE_KEYWORDS = [
    ("provider", ("treating provider", "medical provider", "hospital", "surgeon", "chiropract",
                  "physical therapy", "radiology", "imaging", "neurolog")),
    ("insurer", ("carrier", "insurance", "claims administrator", "adjuster")),
    ("adverse", ("adverse", "defendant", "tortfeasor")),
]

# Provider-facing wording for each matter stage. Unknown stages fall back to the stage name.
STAGE_PLAIN = {
    "Intake": "The firm has just taken the case on.",
    "Treatment": "The client is still treating. The case waits until treatment settles.",
    "Demand": "The firm has sent, or is preparing, a settlement demand.",
    "Negotiation": "The firm is negotiating with the insurer.",
    "Litigation": "A lawsuit has been filed and the case is in the court process.",
    "Trial": "The case is scheduled for, or in, trial.",
    "Disbursement": "The case has resolved and funds are being paid out.",
    "Closed": "The case is closed.",
}

# Document folders whose files belong to a treating provider (records and bills), lowercase substrings.
PROVIDER_DOC_FOLDERS = ("medical",)

# How far ahead "upcoming" looks, in days.
UPCOMING_DAYS = 21

# ---- Red-flag thresholds (app/core/flags.py) ----
# Stages at or after which a lawsuit has been filed (the limitations date no longer threatens the claim).
SUIT_STAGES = ("Litigation", "Trial", "Disbursement", "Closed")
OVERDUE_HIGH_DAYS = 30        # an open task overdue by more than this makes the overdue flag "high"
SOL_WARN_DAYS = 180           # limitations date within this many days (before suit) is flagged
SOL_HIGH_DAYS = 90            # ... and "high" within this many
NO_CLIENT_CONTACT_DAYS = 30   # no email/call with the client for longer than this
TREATMENT_GAP_DAYS = 60       # gap between consecutive dated treatment items for one provider
TREATMENT_MIN_ITEMS = 3       # fewer dated items than this per provider = too thin to judge a gap
FLAG_DOC_CHUNK_CHARS = 60000  # max characters of document text sent to the model per call
FLAG_MAX_ASSERTIONS = 15      # key factual assertions extracted from the case file
FLAG_QUOTE_MATCH = 90         # rapidfuzz partial_ratio needed for a quote to count as found in its source

# ---- Worth vs coverage (firm view) ----
# Coverage on the bar = the per-person limit parsed from the Policy Limits field (facts.reachable_coverage).
# ASSUMED until an attorney confirms that is the right ceiling; set to "" once confirmed.
COVERAGE_ASSUMPTION = "ASSUMED: per-person limit, confirm with attorney"

# ---- Case journey (firm view) ----
# The first document received in a folder whose name contains the key marks that milestone.
MILESTONE_FOLDERS = [
    ("medical records", "Medical records collected"),
    ("pleadings", "Lawsuit filed"),
    ("discovery", "Discovery exchanged"),
    ("experts", "Expert reports"),
    ("settlement", "Settlement papers"),
]
