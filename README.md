# Janus - Internship Tracker

Janus is a hybrid application designed to help university students find software and hardware engineering internships and entry-level positions by aggregating job listings directly from company career pages.

## Project Overview

Janus consists of two main components:

1. **Backend (FastAPI)**: 
   - Web scrapers that collect job listings from company career pages
   - PostgreSQL database to store job listings
   - REST API for the frontend to retrieve job data

2. **Frontend (Next.js)**:
   - Modern, responsive UI built with React and Next.js
   - Local storage with IndexedDB for offline access
   - Synchronization with the backend to get the latest jobs

## Features

- **Chronological Job Listings**: See the most recently posted internships first
- **Category Filtering**: Filter between software and hardware roles
- **Offline Access**: Access job listings even when you're offline
- **Job Details**: View complete job descriptions and requirements
- **Direct Links**: Click through to apply directly on company websites
- **New Job Indicators**: Easily identify newly added positions

## Tech Stack

### Frontend
- **Framework**: Next.js
- **UI Library**: React with Tailwind CSS and shadcn/ui
- **State Management**: React Context API
- **Local Database**: IndexedDB (via idb)
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Scraping**: Beautiful Soup, Playwright
- **ML Processing**: Hugging Face Transformers (for future enhancements)
- **Containerization**: Docker

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Running the Application

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/janus.git
   cd janus
   ```

2. Start the application with Docker Compose:
   ```
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The development server will start at http://localhost:3000 with hot-reloading enabled.

### Backend Development

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
uvicorn app.main:app --reload
```

The API server will start at http://localhost:8000 with auto-reload enabled.

### CLI Tools

The backend includes a command-line interface for common tasks:

```bash
# Seed the database with sample data
python -m app.cli seed

# Run scrapers manually
python -m app.cli scrape

# Run ML processor manually
python -m app.cli process
```

## Project Structure

```
janus/
├── frontend/           # Next.js application
│   ├── src/
│   │   ├── app/        # Pages
│   │   ├── components/ # UI components
│   │   ├── lib/        # Utilities and services
│   │   └── types/      # TypeScript types
│   └── ...
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── scraper/    # Web scrapers
│   │   ├── models.py   # Database models
│   │   ├── schemas.py  # Pydantic schemas
│   │   ├── crud.py     # Database operations
│   │   └── main.py     # API endpoints
│   └── ...
└── docker-compose.yml  # Docker setup
```

## Future Enhancements

- Location-based filtering
- User accounts for tracking applied positions
- Skill-based job matching
- Email notifications for new relevant positions
- Mobile applications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.