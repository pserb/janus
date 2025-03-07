# Janus - Internship Tracker

Janus is a hybrid application designed to help university students find software and hardware engineering internships and entry-level positions by aggregating job listings directly from company career pages.

![Janus Logo](frontend/public/vercel.svg)

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/janus.git
   cd janus
   ```

2. Launch the application:
   ```bash
   docker compose up -d
   ```

3. Seed the database with sample data:
   ```bash
   docker compose exec backend python -m app.cli seed
   ```

4. Access the application:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🏛 Project Architecture

Janus consists of two main components:

### Backend (FastAPI)
- Web scrapers that collect job listings from company career pages
- PostgreSQL database to store job listings
- REST API for the frontend to retrieve job data
- ML processors to summarize job requirements

### Frontend (Next.js)
- Modern, responsive UI built with React and Next.js
- Local storage with IndexedDB for offline access
- Synchronization with the backend to get the latest jobs

## 🛠 Development

### Backend Development

Make changes to the backend code in the `backend/app` directory. After making changes:

```bash
# Rebuild and restart just the backend
docker compose build backend
docker compose up -d backend
```

#### CLI Commands

The backend includes useful CLI commands for management:

```bash
# Seed database with sample data
docker compose exec backend python -m app.cli seed

# Run job scrapers manually
docker compose exec backend python -m app.cli scrape

# Run ML processor manually to summarize job requirements
docker compose exec backend python -m app.cli process
```

### Frontend Development

Make changes to the frontend code in the `frontend` directory. After making changes:

```bash
# Rebuild and restart just the frontend
docker compose build frontend
docker compose up -d frontend
```

### Checking Logs

```bash
# View logs from all services
docker compose logs

# View logs from a specific service
docker compose logs frontend
docker compose logs backend
docker compose logs db

# Follow logs in real-time
docker compose logs -f
```

## 📂 Project Structure

```
janus/
├── frontend/           # Next.js application
│   ├── app/            # Pages
│   ├── components/     # UI components
│   ├── lib/            # Utilities and services
│   └── types/          # TypeScript types
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── scraper/    # Web scrapers
│   │   ├── ml/         # ML processors
│   │   ├── models.py   # Database models
│   │   ├── schemas.py  # Pydantic schemas
│   │   ├── crud.py     # Database operations
│   │   └── main.py     # API endpoints
└── docker-compose.yml  # Docker setup
```

## ⚡ Features

- **Chronological Job Listings**: See the most recently posted internships first
- **Category Filtering**: Filter between software and hardware roles
- **Offline Access**: Access job listings even when you're offline
- **Job Details**: View complete job descriptions and requirements
- **Direct Links**: Click through to apply directly on company websites
- **New Job Indicators**: Easily identify newly added positions
- **Requirements Summary**: Quick overview of key job requirements

## 🔧 Troubleshooting

### Common Issues

**Issue: Backend container fails to start with "uvicorn not found" error**

This usually happens if dependencies are missing in the `pyproject.toml` file.

Solution:
1. Ensure `uvicorn` is listed in the dependencies in `backend/pyproject.toml`
2. Rebuild the backend container:
   ```bash
   docker compose build --no-cache backend
   docker compose up -d
   ```

**Issue: Frontend shows IndexedDB errors**

This can happen due to transaction conflicts in the IndexedDB initialization.

Solution:
1. Check the database initialization in `frontend/lib/db.ts`
2. Ensure there are no nested transactions in the `upgrade` handler
3. Rebuild the frontend:
   ```bash
   docker compose build frontend
   docker compose up -d frontend
   ```

**Issue: API connection errors (404 Not Found or Connection Refused)**

Solution:
1. Verify the API URL in `frontend/next.config.ts` is set to `http://localhost:8000`
2. For Docker networking issues, ensure the frontend's environment in `docker-compose.yml` has:
   ```yaml
   environment:
     - NEXT_PUBLIC_API_URL=http://backend:8000
   ```
3. Rebuild and restart:
   ```bash
   docker compose down
   docker compose up -d
   ```

**Issue: 422 Unprocessable Entity errors**

This typically happens when API validation fails.

Solution:
Check the API validation constraints in `backend/app/main.py` and ensure the frontend respects these limits:
   ```bash
   # View backend logs to see the specific validation error
   docker compose logs backend
   ```

## 📖 API Documentation

The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) when the application is running. It provides details about all available endpoints, parameters, and response formats.

## 🔄 Keeping the Database Updated

### Manual Updates

Run the scrapers manually to fetch new job listings:

```bash
docker compose exec backend python -m app.cli scrape
```

### Automatic Updates

By default, the application runs scrapers automatically at intervals defined in the `scrape_frequency_hours` field of each company record (typically 24 hours).

## 🔐 Environment Variables

The application uses the following environment variables:

**Frontend:**
- `NEXT_PUBLIC_API_URL`: URL of the backend API (default: `http://localhost:8000`)

**Backend:**
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@db:5432/janus`)
- `ADMIN_API_TOKEN`: Token for admin API endpoints (optional)
- `ALLOWED_ORIGINS`: CORS allowed origins (default: `http://localhost:3000`)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.