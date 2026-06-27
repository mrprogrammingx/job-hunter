import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from core.models import Job, CandidateProfile, MatchResult, Application, ApplicationMaterials

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
    """SQLite has no ADD COLUMN IF NOT EXISTS — catch the duplicate-column error instead."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            url TEXT UNIQUE,
            source TEXT,
            date_posted TEXT,
            description TEXT,
            user_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            projects TEXT,
            certifications TEXT,
            raw_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            profile_id INTEGER,
            score REAL,
            skill_gaps TEXT,
            matching_skills TEXT,
            recommendation TEXT,
            reasoning TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (profile_id) REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER UNIQUE,
            status TEXT DEFAULT 'discovered',
            date_discovered TEXT,
            date_applied TEXT,
            match_score REAL DEFAULT 0,
            notes TEXT,
            user_id INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );

        CREATE TABLE IF NOT EXISTS application_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER UNIQUE,
            tailored_resume TEXT,
            cover_letter TEXT,
            recruiter_message TEXT,
            linkedin_message TEXT,
            interview_questions TEXT,
            interview_tips TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
    """)
    conn.commit()

    # Migrate existing databases that predate the user_id columns
    _add_column_if_missing(conn, "jobs", "user_id", "INTEGER")
    _add_column_if_missing(conn, "applications", "user_id", "INTEGER")
    _add_column_if_missing(conn, "profiles", "user_id", "INTEGER")

    conn.close()


# --- Jobs ---

def save_job(job: Job, user_id: Optional[int] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO jobs
               (title, company, location, url, source, date_posted, description, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.title, job.company, job.location, job.url,
             job.source, job.date_posted, job.description, user_id),
        )
        conn.commit()
        job_id = cur.lastrowid
        if not job_id:
            row = conn.execute("SELECT id FROM jobs WHERE url = ?", (job.url,)).fetchone()
            job_id = row["id"] if row else 0
        return job_id
    finally:
        conn.close()


def get_all_jobs(user_id: Optional[int] = None) -> List[Job]:
    conn = get_connection()
    try:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE user_id = ? ORDER BY id DESC", (user_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        return [Job(**{k: row[k] for k in row.keys() if k != "user_id"}) for row in rows]
    finally:
        conn.close()


def get_job(job_id: int) -> Optional[Job]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return Job(**{k: row[k] for k in row.keys() if k != "user_id"})
    finally:
        conn.close()


# --- Profiles ---

def save_profile(profile: CandidateProfile, user_id: Optional[int] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO profiles
               (name, email, phone, skills, experience, education, projects, certifications, raw_text, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile.name, profile.email, profile.phone,
                json.dumps(profile.skills), json.dumps(profile.experience),
                json.dumps(profile.education), json.dumps(profile.projects),
                json.dumps(profile.certifications), profile.raw_text, user_id,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_latest_profile(user_id: Optional[int] = None) -> Optional[CandidateProfile]:
    conn = get_connection()
    try:
        if user_id is not None:
            row = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        d = dict(row)
        return CandidateProfile(
            id=d["id"], name=d["name"] or "", email=d["email"] or "", phone=d["phone"] or "",
            skills=json.loads(d["skills"] or "[]"),
            experience=json.loads(d["experience"] or "[]"),
            education=json.loads(d["education"] or "[]"),
            projects=json.loads(d["projects"] or "[]"),
            certifications=json.loads(d["certifications"] or "[]"),
            raw_text=d["raw_text"] or "",
        )
    finally:
        conn.close()


# --- Match Results ---

def save_match(match: MatchResult) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT OR REPLACE INTO match_results
               (job_id, profile_id, score, skill_gaps, matching_skills, recommendation, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                match.job_id, match.profile_id, match.score,
                json.dumps(match.skill_gaps), json.dumps(match.matching_skills),
                match.recommendation, match.reasoning,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_match(job_id: int) -> Optional[MatchResult]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM match_results WHERE job_id = ?", (job_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        return MatchResult(
            id=d["id"], job_id=d["job_id"], profile_id=d["profile_id"],
            score=d["score"], skill_gaps=json.loads(d["skill_gaps"] or "[]"),
            matching_skills=json.loads(d["matching_skills"] or "[]"),
            recommendation=d["recommendation"], reasoning=d["reasoning"],
        )
    finally:
        conn.close()


# --- Applications ---

def upsert_application(app: Application, user_id: Optional[int] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO applications
               (job_id, status, date_discovered, date_applied, match_score, notes, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(job_id) DO UPDATE SET
                 status=excluded.status, date_applied=excluded.date_applied,
                 match_score=excluded.match_score, notes=excluded.notes,
                 user_id=COALESCE(excluded.user_id, applications.user_id)""",
            (app.job_id, app.status, app.date_discovered,
             app.date_applied, app.match_score, app.notes, user_id),
        )
        conn.commit()
        return cur.lastrowid or conn.execute(
            "SELECT id FROM applications WHERE job_id=?", (app.job_id,)
        ).fetchone()["id"]
    finally:
        conn.close()


def get_all_applications(user_id: Optional[int] = None) -> List[dict]:
    conn = get_connection()
    try:
        if user_id is not None:
            rows = conn.execute(
                """SELECT a.*, j.title, j.company, j.location, j.url
                   FROM applications a JOIN jobs j ON a.job_id = j.id
                   WHERE a.user_id = ?
                   ORDER BY a.id DESC""",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT a.*, j.title, j.company, j.location, j.url
                   FROM applications a JOIN jobs j ON a.job_id = j.id
                   ORDER BY a.id DESC"""
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_application_status(job_id: int, status: str, notes: str = "") -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE applications SET status=?, notes=? WHERE job_id=?",
            (status, notes, job_id),
        )
        conn.commit()
    finally:
        conn.close()


# --- Application Materials ---

def save_materials(materials: ApplicationMaterials) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO application_materials
               (job_id, tailored_resume, cover_letter, recruiter_message,
                linkedin_message, interview_questions, interview_tips)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(job_id) DO UPDATE SET
                 tailored_resume=excluded.tailored_resume,
                 cover_letter=excluded.cover_letter,
                 recruiter_message=excluded.recruiter_message,
                 linkedin_message=excluded.linkedin_message,
                 interview_questions=excluded.interview_questions,
                 interview_tips=excluded.interview_tips""",
            (
                materials.job_id, materials.tailored_resume, materials.cover_letter,
                materials.recruiter_message, materials.linkedin_message,
                json.dumps(materials.interview_questions), materials.interview_tips,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_materials(job_id: int) -> Optional[ApplicationMaterials]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM application_materials WHERE job_id = ?", (job_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        return ApplicationMaterials(
            id=d["id"], job_id=d["job_id"],
            tailored_resume=d["tailored_resume"] or "",
            cover_letter=d["cover_letter"] or "",
            recruiter_message=d["recruiter_message"] or "",
            linkedin_message=d["linkedin_message"] or "",
            interview_questions=json.loads(d["interview_questions"] or "[]"),
            interview_tips=d["interview_tips"] or "",
        )
    finally:
        conn.close()
