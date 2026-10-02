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
