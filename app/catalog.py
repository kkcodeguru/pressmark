from .db import STATUSES, get_db


def like_pattern(term):
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def as_dict(job):
    return {key: job[key] for key in job.keys()}


def job_counts():
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
    ).fetchall()
    counts = {key: 0 for key in STATUSES}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["n"]
    return counts, sum(counts.values())


def list_jobs(status, query):
    status = (status or "").strip()
    if status not in STATUSES:
        status = ""
    query = (query or "").strip()

    sql = "SELECT * FROM jobs WHERE 1 = 1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if query:
        sql += " AND (client LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\' OR ink LIKE ? ESCAPE '\\')"
        pattern = like_pattern(query)
        params.extend([pattern, pattern, pattern])
    sql += """
        ORDER BY CASE status
            WHEN 'on_press' THEN 0
            WHEN 'drying' THEN 1
            WHEN 'queued' THEN 2
            ELSE 3
        END,
        due_on IS NULL,
        due_on ASC,
        id DESC
    """
    jobs = get_db().execute(sql, params).fetchall()
    counts, total = job_counts()
    return jobs, counts, total, status, query


def fetch_job(job_id):
    return get_db().execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def insert_job(data):
    cursor = get_db().execute(
        """
        INSERT INTO jobs (client, title, kind, quantity, ink, status, due_on, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["client"],
            data["title"],
            data["kind"],
            data["quantity"],
            data["ink"],
            data["status"],
            data["due_on"],
            data["notes"],
        ),
    )
    get_db().commit()
    return cursor.lastrowid


def update_job_row(job_id, data):
    get_db().execute(
        """
        UPDATE jobs
        SET client = ?, title = ?, kind = ?, quantity = ?, ink = ?, status = ?, due_on = ?, notes = ?
        WHERE id = ?
        """,
        (
            data["client"],
            data["title"],
            data["kind"],
            data["quantity"],
            data["ink"],
            data["status"],
            data["due_on"],
            data["notes"],
            job_id,
        ),
    )
    get_db().commit()


def update_status(job_id, status):
    get_db().execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    get_db().commit()


def remove_job(job_id):
    get_db().execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    get_db().commit()
