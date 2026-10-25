# UK Wind Power Analytics

A full-stack web application for analysing UK wind power generation and day-ahead forecasts using Elexon data. The application compares actual wind generation with forecasts in 30-minute intervals and calculates forecast accuracy metrics to support electricity procurement decisions.

The application is scoped to January 2026, as required by the assignment.

## Live Application

- **Frontend:** https://uwa-xi.vercel.app
- **Backend API:** https://uwa-dgex.vercel.app
- **Backend health check:** https://uwa-dgex.vercel.app/health
- **Wind data API:** https://uwa-dgex.vercel.app/api/wind-data?date=2026-01-15

The frontend and backend are deployed on Vercel.

## Features

- View actual UK wind power generation and day-ahead forecasts.
- Select dates within January 2026.
- Compare actual and forecast generation in 30-minute intervals.
- Visualise actual and forecast generation on a chart.
- View generation values in a data table.
- Calculate forecast accuracy using:
  - Mean Absolute Error (MAE)
  - Root Mean Square Error (RMSE)
  - Bias (forecast minus actual)
- Align actual generation and forecasts by their target timestamps.
- Select eligible day-ahead forecasts using the midnight publication cutoff.
- Handle missing observations without inventing values.
- Validate supported dates and report data retrieval errors.

## Tech Stack

**Frontend**
- React
- Vite
- Tailwind CSS
- Recharts
- Axios

**Backend**
- Python
- FastAPI
- Pydantic
- Pandas
- Pytest

**Data Source**
- Elexon BMRS API
- FUELHH dataset for actual generation
- WINDFOR dataset for forecast generation

**Deployment and Development**
- Docker
- Docker Compose
- Vercel

## Project Structure

```text
uk-wind-analytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── services.py
│   │   └── mock_data.py
│   ├── tests/
│   │   └── test_services.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── WindChart.jsx
│   │       └── MetricsCard.jsx
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── nginx.conf
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

The `.env` file is intended for local configuration and should remain excluded from version control. It is not required to be committed to the repository.

## Requirements

For local development:

- Python 3.11 or later
- Node.js 20.19+ or 22.12+
- npm
- Docker and Docker Compose (for containerised execution)

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd uk-wind-analytics
```

Replace `<YOUR_REPOSITORY_URL>` with the repository's actual URL.

### 2. Configure environment variables

Copy the example configuration to a local `.env` file.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Review the available variables before running the application.

### 3. Run with Docker Compose

From the repository root:

```bash
docker-compose up --build
```

Open the frontend at:

http://localhost:3000

The backend API is expected at:

http://localhost:8000

FastAPI documentation:

http://localhost:8000/docs

Stop the containers with:

```bash
docker-compose down
```

### 4. Run the backend locally

Open a terminal in the repository root.

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The backend will be available at:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

### 5. Run the frontend locally

Open another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the Vite development URL shown in the terminal. By default, this is:

http://localhost:5173

For local development, configure the frontend API URL to point to the local backend.

## Configuration

The application uses environment variables to configure the backend and frontend.

| Variable | Purpose |
|---|---|
| `USE_MOCK_DATA` | Enables the local demonstration data mode when supported. Keep it unset or set to `false` for production data. |
| `ALLOWED_ORIGINS` | Specifies the frontend origins permitted to access the backend. |
| `VITE_API_URL` | Sets the backend base URL used by the frontend at build time. |

### Local configuration

For local development, the frontend API URL can point to:

```text
VITE_API_URL=http://localhost:8000
```

### Production configuration

The frontend's Vercel project should use:

```text
VITE_API_URL=https://uwa-dgex.vercel.app
```

The backend's `ALLOWED_ORIGINS` configuration should permit the deployed frontend origin:

```text
https://uwa-xi.vercel.app
```

Configure these variables in the appropriate Vercel project settings. `VITE_API_URL` is a frontend build-time variable, so redeploy the frontend after changing it.

Do not put secrets in frontend environment variables or commit private `.env` files.

## Data Source and Processing

The application uses Elexon BMRS data for actual and forecast UK wind generation.

### Actual generation

Actual generation data is retrieved from the FUELHH dataset, filtered for wind generation.

Dataset documentation:

https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream

### Forecast generation

Forecast data is retrieved from the WINDFOR dataset.

Dataset documentation:

https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream

Forecast records contain a target timestamp and a publication timestamp. Forecast selection follows the application's configured midnight publication cutoff so that forecasts available by the procurement decision cutoff are used.

Actual and forecast observations are aligned by their 30-minute target timestamps before accuracy metrics are calculated.

Missing or invalid observations are not replaced with fabricated generation values.

## Date Range

The application is scoped to January 2026.

Supported dates:

- Start date: `2026-01-01`
- End date: `2026-01-31`

The dashboard allows users to select dates within this period. Requests outside the supported range are rejected by the backend.

## API Endpoints

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Wind generation data

```http
GET /api/wind-data?date=YYYY-MM-DD
```

Example:

https://uwa-dgex.vercel.app/api/wind-data?date=2026-01-15

The response contains a data collection and forecast accuracy metrics. Each data point includes the target timestamp, actual generation, and forecast generation where available.

The metrics include:

- `mae`: mean absolute error
- `rmse`: root mean square error
- `bias`: mean forecast error, calculated as forecast minus actual
- `dataPoints`: number of valid paired observations used in the metrics

The exact response schema is defined by the backend's Pydantic response models.

### Error handling

The API validates the requested date and handles data retrieval failures.

- Invalid or unsupported dates are rejected.
- Upstream data failures are reported rather than silently replaced with mock production data.
- Missing observations are handled without inventing actual or forecast values.

Refer to the backend route implementation for the exact HTTP status codes returned for different errors.

## Forecast Accuracy Metrics

The dashboard calculates forecast accuracy from valid actual-versus-forecast pairs.

### Mean Absolute Error (MAE)

The average absolute difference between forecast and actual generation.

### Root Mean Square Error (RMSE)

The square root of the average squared difference between forecast and actual generation.

### Bias

The average signed difference between forecast and actual generation:

```text
Bias = Forecast - Actual
```

A positive bias indicates that forecasts are higher than actual generation on average. A negative bias indicates that forecasts are lower than actual generation on average.

The metrics are expressed in MW.

## Testing

### Backend tests

From the repository root:

```bash
cd backend
python -m pytest -v
```

The automated backend tests cover service-level functionality, including forecast metrics, publication cutoff handling, and missing or invalid data.

### Frontend production build

From the repository root:

```bash
cd frontend
npm ci
npm run build
```

Vite generates the production frontend in the `dist/` directory.

### Deployed application checks

The deployed application can be checked using the following URLs:

- Frontend: https://uwa-xi.vercel.app
- Health check: https://uwa-dgex.vercel.app/health
- Sample data request: https://uwa-dgex.vercel.app/api/wind-data?date=2026-01-15

When validating a release, check that the dashboard loads, the selected date is reflected in the API request, the chart and table update, and the displayed metrics correspond to the returned data.

## Deployment

### Frontend — Vercel

The frontend is deployed at:

https://uwa-xi.vercel.app

The frontend project uses the `frontend/` directory and Vite's production build.

Typical build settings:

- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL=https://uwa-dgex.vercel.app`

### Backend — Vercel

The backend is deployed at:

https://uwa-dgex.vercel.app

Health check:

https://uwa-dgex.vercel.app/health

The backend production configuration should keep mock data disabled and permit requests from the deployed frontend origin.

### Docker

Dockerfiles and Docker Compose configuration are included for containerised local development and execution. The Docker workflow is separate from the Vercel deployment configuration.

## AI Tool Disclosure

AI tools were used as supporting resources during development for debugging, troubleshooting implementation issues, reviewing requirements, and assisting with routine development and documentation tasks.

The suggestions were reviewed and the application was tested against the project requirements. Responsibility for the final implementation, technical decisions, and validation remains with the developer.
