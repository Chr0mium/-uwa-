# UK Wind Power Analytics

A full-stack web application for analysing UK wind power generation and day-ahead forecasts using Elexon data. The app compares actual and forecast generation in 30-minute intervals and calculates forecast accuracy metrics.

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **Deployment:** Docker Compose, Vercel, Heroku or Render

## Project Structure

```text
uk-wind-analytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # package marker
│   │   ├── main.py            # FastAPI app, routes, CORS, input validation, error mapping
│   │   ├── models.py          # Pydantic response schemas (WindDataPoint / MetricsResponse / DataResponse)
│   │   ├── services.py        # Elexon FUELHH+WINDFOR fetch, 30‑min alignment, day‑ahead cutoff, metrics
│   │   └── mock_data.py       # opt‑in local demo generator (only when USE_MOCK_DATA=true)
│   ├── tests/
│   │   └── test_services.py   # metrics + day‑ahead cutoff + missing/invalid‑data unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api.js             # axios client; base URL from VITE_API_URL
│   │   ├── App.jsx            # UI, date filter, loading/error/empty states, data table
│   │   ├── main.jsx           # React entry
│   │   ├── index.css          # Tailwind directives
│   │   └── components/
│   │       ├── WindChart.jsx     # forecast‑vs‑actual chart (Recharts)
│   │       └── MetricsCard.jsx   # MAE / RMSE / bias cards
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── nginx.conf             # SPA serving — Docker/compose path only (Vercel does not use it)
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml         # local / container orchestration
├── .env.example               # committed template (safe defaults)
├── .env                       # local only — git‑ignored
├── .gitignore
└── README.md
```

## Getting Started

### Requirements

- Docker and Docker Compose
- Node.js 20.19+ or 22.12+
- Python 3.11+

### Run with Docker

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Start the application:

   ```bash
   docker-compose up --build
   ```

4. Open the application at [http://localhost:3000](http://localhost:3000).

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs).

### Run Locally

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1`.

**Frontend**

```bash
cd frontend
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Configuration

Copy `.env.example` to `.env` and configure the following variables:

| Variable | Purpose |
|---|---|
| `USE_MOCK_DATA` | Set to `true` for local demos; leave unset or `false` in production. |
| `ALLOWED_ORIGINS` | Allowed frontend origins. Set the exact frontend URL in production. |
  | `VITE_API_URL` | Public backend URL with **no trailing slash** (a trailing `/` yields `//api/wind-data`), configured at frontend build time. |

## API

- `GET /api/wind-data?date=YYYY-MM-DD` — Returns actual generation, day-ahead forecasts and accuracy metrics.
- `GET /health` — Health check.

Supported dates are 1–31 January 2026. Invalid dates return `400`, and upstream data failures return `503`.

Forecast metrics include mean absolute error (MAE), root mean square error (RMSE) and bias.

## Tests

Run the backend tests from the `backend/` directory:

```bash
python -m pytest -v
```

## Deployment

- **Frontend:** Deploy `frontend/` to Vercel using `npm run build` and `dist` as the output directory. Set `VITE_API_URL` before building.
- **Backend:** Deploy the `backend/Dockerfile` to Heroku or Render. Configure `USE_MOCK_DATA=false` and set `ALLOWED_ORIGINS` to the deployed frontend URL.

Ensure `frontend/package-lock.json` is committed before deployment. Verify that the API returns real Elexon data before releasing to production.

**Live application:** Pending deployment.

## AI Tool Disclosure

I developed this project with a focus on understanding the requirements, designing the solution, and validating the implementation. I used AI tools as a supporting resource for debugging, troubleshooting implementation issues, refining code, and assisting with routine development tasks and documentation. I reviewed the suggestions, tested the application, and made the necessary adjustments to ensure the solution aligned with the project requirements. I am responsible for the final implementation, technical decisions, and validation of the work.