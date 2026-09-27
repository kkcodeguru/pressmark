# Pressmark

Pressmark is a sample Flask application: a job board for a small letterpress shop. Add a docket, move it from queued to on press, drying, and delivered, and search the board by client, piece, or ink.

Jobs live in a local SQLite file at `instance/pressmark.sqlite`. There are no accounts. The first launch creates the database and loads six sample jobs. If you delete that file, the next launch seeds them again. Clearing every job and restarting leaves the board empty.

## Run it

Python 3.11 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.

Open [http://127.0.0.1:5341](http://127.0.0.1:5341).

The development server uses a fixed secret (`pressmark-dev-only` unless you set `SECRET_KEY`). Keep this app on your own machine.

## Tests

```bash
source .venv/bin/activate
pytest
```

## What you can do

- Scan the board and filter by status
- Search by client, piece title, or ink
- Add, edit, and remove a job
- Move a job between Queued, On press, Drying, and Delivered
- See an overdue mark when a due date has passed and the job is not delivered

Unknown pages and missing job numbers show a 404. A form that fails validation stays on the page with the errors. A form submitted without its token shows a 400 page.
