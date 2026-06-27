import requests
from typing import List
from core.models import Job

REMOTEOK_URL = "https://remoteok.com/api"
HN_WHOISHIRING_URL = "https://hacker-news.firebaseio.com/v0"


def fetch_jobs(roles: List[str], keywords: List[str], location: str = "remote") -> List[Job]:
    """Fetch jobs from RemoteOK filtered by roles and keywords."""
    jobs: List[Job] = []
    jobs.extend(_fetch_remoteok(roles, keywords))
    return _deduplicate(jobs)


def _fetch_remoteok(roles: List[str], keywords: List[str]) -> List[Job]:
    headers = {"User-Agent": "JobHunterApp/1.0 (educational project)"}
    try:
        resp = requests.get(REMOTEOK_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    search_terms = {t.lower() for t in roles + keywords}
    jobs = []

    for item in data:
        if not isinstance(item, dict) or "position" not in item:
            continue

        title = item.get("position", "")
        tags = item.get("tags", []) or []
        description = item.get("description", "") or ""
        combined = f"{title} {' '.join(tags)} {description}".lower()

        if any(term in combined for term in search_terms):
            jobs.append(Job(
                title=title,
                company=item.get("company", "Unknown"),
                location=item.get("location") or "Remote",
                url=item.get("url", "") or f"https://remoteok.com/remote-jobs/{item.get('id', '')}",
                source="RemoteOK",
                date_posted=item.get("date", ""),
                description=_clean(description, 3000),
            ))

    return jobs[:30]


def _clean(text: str, max_len: int) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _deduplicate(jobs: List[Job]) -> List[Job]:
    seen_urls: set = set()
    seen_titles: set = set()
    unique = []
    for job in jobs:
        key = job.url or f"{job.title}|{job.company}"
        dedup_key = f"{job.title.lower()}|{job.company.lower()}"
        if key not in seen_urls and dedup_key not in seen_titles:
            seen_urls.add(key)
            seen_titles.add(dedup_key)
            unique.append(job)
    return unique
