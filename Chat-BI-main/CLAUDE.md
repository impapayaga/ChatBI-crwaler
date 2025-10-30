# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChatBI is a Business Intelligence chat application that combines natural language processing with data visualization. Users can ask questions in natural language, and the system generates charts and insights from a PostgreSQL database.

**Tech Stack:**
- **Frontend**: Vue 3 + Vuetify 3 + TypeScript + Vite
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL (via Docker)
- **State Management**: Pinia
- **Charts**: ECharts (vue-echarts)
- **Styling**: Vuetify + Tailwind CSS + SASS

## Development Commands

### Frontend (from `frontend/` directory)

```bash
# Development server (runs on http://localhost:3000)
pnpm dev

# Type checking
pnpm type-check

# Build for production
pnpm build

# Preview production build
pnpm preview

# Linting
pnpm lint

# Code formatting
pnpm format
```

### Backend (from `backend/` directory)

```bash
# Activate conda environment
conda activate chatbi

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL database (Docker)
docker-compose up -d

# Initialize database (creates tables and inserts mock data)
python init_db.py

# Run backend server (http://127.0.0.1:11434)
python main.py
```

## Architecture

### Frontend Architecture

The frontend uses Vuetify's **Recommended preset** with automatic component imports and file-based routing:

- **Auto-imports**: Components, layouts, and Vue APIs are automatically imported via `unplugin-vue-components` and `unplugin-auto-import`
- **File-based routing**: Pages in `src/pages/` automatically become routes via `unplugin-vue-router`
- **Layouts system**: `src/layouts/` contains layout components (default, sidebar, navbar) using `vite-plugin-vue-layouts`
- **Global state**: Pinia stores in `src/stores/` (e.g., `theme.ts` for dark/light mode)

**Key Files:**
- `src/components/Home.vue`: Main chat interface with message bubbles, chart display, and auto-resizing textarea input
- `src/components/EChart.vue`: ECharts wrapper component for data visualization
- `src/layouts/default.vue`: Main layout with sidebar and navbar integration
- `src/stores/theme.ts`: Dark/light theme management using Vuetify's theme system

**Important**: The main container uses Vuetify's `v-main` with `app` prop on `v-app-bar` and `v-navigation-drawer`. Fixed positioning elements must account for Vuetify's automatic margin adjustments.

### Backend Architecture

FastAPI application with async PostgreSQL database access:

- **Main entry**: `backend/main.py` - FastAPI app with lifespan events for DB initialization
- **Configuration**: `backend/core/config.py` - Environment-based settings (DB, API URLs, CORS)
- **Database**: SQLAlchemy async with `asyncpg` driver
- **API Endpoints** in `backend/api/endpoints/`:
  - `generate_chart.py`: Processes user questions, queries DB, returns chart data
  - `insight_analysis_stream.py`: Streaming AI analysis responses (SSE)
  - `ai_model_config.py`: AI model configuration endpoints

**API Flow:**
1. User input → `POST /api/generate_chart`
2. Function calling to extract SQL parameters
3. Database query execution
4. Chart data refinement and type selection
5. Return structured data for ECharts
6. Trigger streaming insight analysis via `POST /api/insight_analysis_stream`

### Database Schema

The backend uses `backend/db/init_db.py` to automatically create tables and insert mock data on startup. Schema is defined in `backend/api/config/database_schema.py`.

## Environment Variables

### Frontend `.env`
```
VITE_API_BASE_URL=http://127.0.0.1:11434
```

### Backend `.env`
Key variables (see `backend/core/config.py`):
- Database: `DBNAME`, `DBUSER`, `DBPGPASSWORD`, `DBHOST`, `DBPORT`
- FastAPI: `FASTAPI_HOST`, `FASTAPI_PORT`, `FASTAPI_ENV`
- Frontend CORS: `FRONTEND_URL`
- AI API endpoints: `API_URL_14B_CHAT`, `API_URL_72B_CHAT`

## UI Design Patterns

The application follows a **Grok-inspired design** with these key patterns:

1. **Message Bubbles**: User messages have dark background (black in light mode, white in dark mode) with rounded corners except top-right
2. **Auto-resizing Input**: Textarea auto-expands up to 6 lines (150px max height)
   - Enter: Send message
   - Shift+Enter: New line
3. **Fixed Input Container**: Bottom input uses `position: fixed` with blur backdrop
4. **Responsive Layout**: Content adapts to sidebar expansion/collapse via Vuetify's layout system
5. **Theme Toggle**: Dark/light mode via Pinia store with Vuetify theme integration

## Key Integration Points

### Frontend → Backend Communication

```typescript
// Example: Generate chart request
const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/generate_chart`, {
  user_input: inputValue.value
})

// Example: Streaming analysis (SSE)
const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/insight_analysis_stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_input, data: chartData })
})
const reader = response.body.getReader()
// Process SSE stream...
```

### Chart Data Format

Backend returns:
```json
{
  "data": [...],           // Raw query results
  "refined_data": {
    "x_axis": "field_name",
    "y_axes": ["metric1", "metric2"],
    "scale": "...",
    "unit": "..."
  },
  "chart_type": "bar"     // bar, line, pie, doughnut
}
```

Frontend converts to ECharts options format.

## Common Patterns

### Adding New API Endpoints

1. Create endpoint file in `backend/api/endpoints/`
2. Define route with FastAPI decorator
3. Import and include in `backend/api/endpoints/__init__.py` router
4. Auto-registered via `app.include_router(api_router)` in `main.py`

### Adding New Frontend Components

1. Place in `src/components/` - auto-imported globally
2. Use Vuetify components without imports (auto-imported)
3. Access theme via `import { useThemeStore } from '@/stores/theme'`

### Styling Approach

- **Vuetify components**: Use Vuetify's props system for styling
- **Custom styles**: Scoped SASS with Tailwind utility classes
- **Dark mode**: Use `:global(.v-theme--dark)` selectors or Vuetify's theme colors
- **Fixed positioning**: Account for Vuetify's layout margins (sidebar, app-bar)

## Development Workflow

1. Start backend: `conda activate chatbi` → `docker-compose up -d` → `python main.py`
2. Start frontend: `cd frontend` → `pnpm dev`
3. Access: http://localhost:3000
4. Database auto-initializes with mock data on first run

## TypeScript Patterns

- Use `ref<Type>()` for typed refs
- Event handlers: Cast event targets explicitly `(event.target as HTMLTextAreaElement)`
- Use `import type` for type-only imports
- Vuetify components imported from `vuetify/components` when needed
