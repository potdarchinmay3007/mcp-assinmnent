import httpx
from fastmcp import FastMCP

mcp = FastMCP("Job Vacancy Finder")

API_URL = "https://remotive.com/api/remote-jobs"


@mcp.tool
def search_jobs(role: str, limit: int = 5) -> str:
    """Search current remote job vacancies for a job role, for example
    'python developer', and return title, company, location, type, salary and link."""
    limit = max(1, min(limit, 20))
    try:
        response = httpx.get(
            API_URL, params={"search": role, "limit": limit}, timeout=15
        )
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
    except httpx.HTTPError as error:
        return f"Could not fetch jobs right now: {error}"

    if not jobs:
        return f"No current vacancies found for '{role}'."

    results = []
    for job in jobs:
        results.append(
            f"Title: {job.get('title')}\n"
            f"Company: {job.get('company_name')}\n"
            f"Location: {job.get('candidate_required_location')}\n"
            f"Type: {job.get('job_type')}\n"
            f"Salary: {job.get('salary') or 'Not listed'}\n"
            f"Posted: {job.get('publication_date')}\n"
            f"Link: {job.get('url')}"
        )
    return "\n\n".join(results) + "\n\nSource: Remotive (https://remotive.com)"


@mcp.resource("data://job-sources")
def job_sources() -> str:
    """Explain where the job data comes from and what its limits are."""
    return (
        "Data source: Remotive public API (https://remotive.com).\n"
        "Coverage: remote jobs only, not local or on-site listings.\n"
        "Freshness: listings are usually delayed by about 24 hours.\n"
        "Rate limit: avoid more than 2 requests per minute."
    )


@mcp.prompt
def job_search_prompt(role: str, experience: str = "fresher") -> str:
    """Create a prompt asking the model to find and summarize vacancies for a role."""
    return (
        f"Use the search_jobs tool to find current vacancies for '{role}'. "
        f"I am at the '{experience}' level. Show the best matches, explain the "
        f"key requirements for each, and suggest which one to apply to first."
    )


if __name__ == "__main__":
    mcp.run()