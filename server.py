import httpx
from fastmcp import FastMCP

mcp = FastMCP("Job Vacancy Finder")

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs"


def _salary_text(low, high, currency):
    """Build a readable salary string, or 'Not listed' if none is given."""
    if low and high:
        return f"{low} - {high} {currency or ''} per year".strip()
    if low or high:
        return f"{low or high} {currency or ''} per year".strip()
    return "Not listed"


def _from_remotive(role, limit):
    """Fetch jobs from the Remotive API."""
    response = httpx.get(
        REMOTIVE_URL, params={"search": role, "limit": limit}, timeout=15
    )
    response.raise_for_status()
    jobs = []
    for job in response.json().get("jobs", []):
        jobs.append(
            {
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("candidate_required_location"),
                "type": job.get("job_type"),
                "salary": job.get("salary") or "Not listed",
                "posted": job.get("publication_date"),
                "link": job.get("url"),
                "source": "Remotive",
            }
        )
    return jobs


def _from_jobicy(role, limit):
    """Fetch jobs from the Jobicy API."""
    response = httpx.get(
        JOBICY_URL, params={"count": limit, "tag": role}, timeout=15
    )
    response.raise_for_status()
    jobs = []
    for job in response.json().get("jobs", []):
        jobs.append(
            {
                "title": job.get("jobTitle"),
                "company": job.get("companyName"),
                "location": job.get("jobGeo"),
                "type": job.get("jobType"),
                "salary": _salary_text(
                    job.get("annualSalaryMin"),
                    job.get("annualSalaryMax"),
                    job.get("salaryCurrency"),
                ),
                "posted": job.get("pubDate"),
                "link": job.get("url"),
                "source": "Jobicy",
            }
        )
    return jobs


@mcp.tool
def search_jobs(role: str, limit: int = 5) -> str:
    """Search current remote job vacancies for a role, for example
    'python developer', from Remotive and Jobicy. Returns title, company,
    location, type, salary (if listed), posting date and apply link."""
    limit = max(1, min(limit, 10))
    jobs = []
    notes = []

    for name, fetch in (("Remotive", _from_remotive), ("Jobicy", _from_jobicy)):
        try:
            jobs.extend(fetch(role, limit))
        except (httpx.HTTPError, ValueError) as error:
            notes.append(f"{name} could not be reached: {error}")

    if not jobs:
        return f"No current vacancies found for '{role}'. " + " ".join(notes)

    results = []
    for job in jobs:
        results.append(
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Type: {job['type']}\n"
            f"Salary: {job['salary']}\n"
            f"Posted: {job['posted']}\n"
            f"Link: {job['link']}\n"
            f"Source: {job['source']}"
        )

    footer = "Sources: Remotive (https://remotive.com), Jobicy (https://jobicy.com)"
    if notes:
        footer += "\n" + "\n".join(notes)
    return "\n\n".join(results) + "\n\n" + footer


@mcp.resource("data://job-sources")
def job_sources() -> str:
    """Explain where the job data comes from and what its limits are."""
    return (
        "Data sources: Remotive (https://remotive.com) and Jobicy (https://jobicy.com), "
        "both free public APIs.\n"
        "Coverage: remote jobs only. LinkedIn, Naukri, Indeed and similar portals "
        "are not included because they have no free public API.\n"
        "Salary: shown only when the posting lists it, otherwise 'Not listed'.\n"
        "Freshness: listings can be delayed, so a job may already be filled.\n"
        "Usage: avoid sending requests too frequently."
    )


@mcp.prompt
def job_search_prompt(role: str, experience: str = "fresher") -> str:
    """Create a prompt asking the model to find and compare vacancies for a role."""
    return (
        f"Use the search_jobs tool to find current vacancies for '{role}'. "
        f"I am at the '{experience}' level. Compare the best matches, include the "
        f"salary when it is listed, explain the key requirements, and suggest "
        f"which one to apply to first."
    )


if __name__ == "__main__":
    mcp.run()