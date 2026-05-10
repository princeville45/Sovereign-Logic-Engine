# Research Pipeline: High-CPM Story Lead Generator
# Focus: Financial Crime, Money Laundering, White-Collar Fraud

def get_high_cpm_leads():
    # In a real run, this pulls from Zapia search results
    leads = [
        {"title": "The Crypto Washer", "angle": "How a 19-year-old cycled B through shell accounts."},
        {"title": "Vatican Banking Scandal", "angle": "The intersection of faith and 00M fraud."},
        {"title": "Panama Papers 2.0", "angle": "New offshore leaks affecting top VCs."}
    ]
    return leads

if __name__ == "__main__":
    print("--- High-CPM Story Leads ---")
    for lead in get_high_cpm_leads():
        print(f"TARGET: {lead['title']} | LOGIC: {lead['angle']}")
