import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
    search_term='"engineering intern" software summer (java OR python OR c++) 2025',
    results_wanted=100,
    location='United States',
    hours_old=1000,
    country_indeed='USA',
    
)
print(f"Found {len(jobs)} jobs")
print(jobs.head())
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)