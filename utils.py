import os
from num2words import num2words

# --- BANK LOGOS CONFIGURATION ---
BANKS = [
    {"name": "State Bank of India", "file": "logos/SBI.jpg"},
    {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
    {"name": "ICICI Bank", "file": "logos/ICICI Bank.jpg"},
    {"name": "Axis Bank", "file": "logos/Axis Bank.jpg"},
    {"name": "Indian Bank", "file": "logos/Indian Bank.jpg"},
    {"name": "Canara Bank", "file": "logos/Canara.jpg"},
    {"name": "Bank of Baroda", "file": "logos/Bank of Baroda.jpg"},
    {"name": "Union Bank of India", "file": "logos/Union Bank of India.jpg"},
    {"name": "Karur Vysya Bank", "file": "logos/KVB.jpg"},
    {"name": "Yes Bank", "file": "logos/Yes Bank.jpg"},
    {"name": "IDFC First Bank", "file": "logos/IDFC First Bank.jpg"},
    {"name": "Bandhan Bank", "file": "logos/Bandhan Bank.jpg"},
    {"name": "Kotak Mahindra Bank", "file": "logos/KMB.jpg"},
    {"name": "South Indian Bank", "file": "logos/South Indian Bank.jpg"},
    {"name": "Central Bank of India", "file": "logos/Central Bank of India.jpg"},
    {"name": "Indian Overseas Bank", "file": "logos/Indian Overseas Bank.jpg"},
    {"name": "Bank of India", "file": "logos/Bank of India.jpg"},
    {"name": "UCO Bank", "file": "logos/UCO Bank.jpg"},
    {"name": "City Union Bank", "file": "logos/City Union Bank.jpg"},
    {"name": "Deutsche Bank", "file": "logos/Deutsche Bank.jpg"},
    {"name": "Equitas Bank", "file": "logos/Equitas Bank.jpg"},
    {"name": "IDBI Bank", "file": "logos/IDBI Bank.jpg"},
    {
        "name": "The Hongkong and Shanghai Banking Corporation",
        "file": "logos/HSBC.jpg",
    },
    {
        "name": "Tamilnad Mercantile Bank",
        "file": "logos/Tamilnad Mercantile Bank.jpg",
    },
    {"name": "Karnataka Bank", "file": "logos/Karnataka Bank.jpg"},
    {"name": "CSB Bank", "file": "logos/CSB Bank.jpg"},
    {"name": "Standard Chartered Bank", "file": "logos/Standard Chartered Bank.jpg"},
    {"name": "Federal Bank", "file": "logos/Federal Bank.jpg"},
]

CC_ADVANCE_TEMPLATE = "CCTemplate.docx"
SD_TEMPLATE = "SDTemplate.docx"

OTHER_PURPOSES = [
    "Advance Payment",
    "Advance Security Deposit (ASD)",
    "Security Deposit and Meter Security Deposit (SD and MSD)",
    "Processing Fee",
]

MONTH_LIST = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
YEAR_OPTIONS = [2026, 2025]


def format_indian_currency(number):
    try:
        main = str(int(float(number)))
        if len(main) <= 3:
            return main
        last_three = main[-3:]
        remaining = main[:-3]
        res = ""
        while len(remaining) > 2:
            res = "," + remaining[-2:] + res
            remaining = remaining[:-2]
        if remaining:
            res = remaining + res
        return f"{res},{last_three}"
    except Exception:
        return "0"


def amount_words(number):
    return (
        num2words(int(number), lang="en_IN")
        .replace(",", "")
        .replace(" And ", " and ")
        .title()
        .replace(" And ", " and ")
    )


def format_period_month_text(target_months):
    year_to_months = {}
    for month_name, year in target_months:
        year_to_months.setdefault(year, []).append(month_name)

    parts = []
    for year, months in year_to_months.items():
        parts.append(f"{', '.join(months)} - {year}")

    return " and ".join(parts)


class SafeReceipt(dict):
    def __getattr__(self, name):
        return self.get(name, "")
