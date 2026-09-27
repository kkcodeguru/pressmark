# Pressmark

Pressmark is a sample letterpress job board with two processes:

- **Flask** stores the jobs and serves both its own board and a JSON API.
- **Django** renders a second board and integrates with Flask over HTTP. Django does not keep its own copy of the jobs.

The shared integration key is `PRESSMARK_API_KEY` (default `pressmark-dev-only`). Django sends it as the `X-Pressmark-Key` header.

## Run both

Python 3.11 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

Start Flask first:

```bash
python run.py
```

Open the Flask board at [http://127.0.0.1:5341](http://127.0.0.1:5341).

In a second terminal, with the same virtual environment:

```bash
python django_board/manage.py migrate
python django_board/manage.py runserver 0.0.0.0:5342
```

Open the Django board at [http://127.0.0.1:5342](http://127.0.0.1:5342). Adding, editing, moving, or removing a job there calls Flask. Reload the Flask board and the same docket is there.

Jobs live in `instance/pressmark.sqlite`. The first Flask launch creates that file and loads six sample jobs. Django's own SQLite file is only for Django's built-in tables.

These development servers use fixed local secrets. Keep them on your own machine.

## Flask API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Integration check |
| GET | `/api/jobs` | List, with `q` and `status` |
| POST | `/api/jobs` | Create a job |
| GET | `/api/jobs/<id>` | Read one job |
| PUT | `/api/jobs/<id>` | Replace a job |
| POST | `/api/jobs/<id>/status` | Move status |
| DELETE | `/api/jobs/<id>` | Remove a job |

Every `/api` route requires `X-Pressmark-Key`.

## Tests

```bash
source .venv/bin/activate
pytest
```
