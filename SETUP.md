# Recipe Ingredient Calculator - Setup Guide

## Prerequisites

- **Python 3.10+** - [Download](https://python.org/downloads)
- **Git** - [Download](https://git-scm.com)
- **Gemini API Key** - [Get Free Key](https://makersuite.google.com/app/apikey)

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/Sai1929/ingredients_prediction.git
cd ingredients_prediction

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env

# 6. Edit .env and add your GEMINI_API_KEY

# 7. Run backend
python run.py

# 8. Open frontend/index.html in browser
```

---

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/Sai1929/ingredients_prediction.git
cd ingredients_prediction
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- Google Generative AI (Gemini SDK)
- SlowAPI (rate limiting)

### Step 4: Configure Environment

1. Copy the example config:
   ```bash
   # Windows
   copy .env.example .env

   # Mac/Linux
   cp .env.example .env
   ```

2. Edit `.env` file and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. Get your free API key from: https://makersuite.google.com/app/apikey

### Step 5: Run Backend Server

```bash
python run.py
```

Expected output:
```
============================================================
     Recipe Ingredient Calculator API  v1.0.0
============================================================
  Server: http://0.0.0.0:8000
  Docs:   http://localhost:8000/docs
  Health: http://localhost:8000/health
------------------------------------------------------------
  Gemini API: Configured
============================================================
```

### Step 6: Open Frontend

Open `frontend/index.html` in your browser:

- **Windows:** Double-click the file, or run `start frontend/index.html`
- **Mac:** Run `open frontend/index.html`
- **Linux:** Run `xdg-open frontend/index.html`

### Step 7: Test the Application

1. Enter a dish name (e.g., "Chicken Biryani")
2. Set number of servings (e.g., 4)
3. Click "Calculate Ingredients"
4. View the generated recipe with ingredients, instructions, and nutritional info

---

## Project Structure

```
ingredients_prediction/
├── app/                      # Backend application
│   ├── __init__.py
│   ├── config.py             # Configuration settings
│   ├── main.py               # FastAPI app factory
│   ├── core/
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── security.py       # CORS & security middleware
│   ├── models/
│   │   └── schemas.py        # Pydantic data models
│   ├── routes/
│   │   ├── health.py         # Health check endpoints
│   │   └── recipe.py         # Recipe API endpoints
│   └── services/
│       ├── cache.py          # In-memory caching
│       └── gemini.py         # Gemini AI integration
├── frontend/
│   ├── index.html            # React frontend
│   └── css/
│       └── styles.css        # Custom styles
├── .env                      # Environment config (create this)
├── .env.example              # Example config template
├── .gitignore                # Git ignore rules
├── render.yaml               # Render deployment config
├── requirements.txt          # Python dependencies
├── run.py                    # Backend entry point
└── SETUP.md                  # This file
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/api/recipe` | Generate recipe |
| GET | `/api/cache/stats` | Cache statistics |
| DELETE | `/api/cache/clear` | Clear cache |

### Example API Request

```bash
curl -X POST http://localhost:8000/api/recipe \
  -H "Content-Type: application/json" \
  -d '{"dish_name": "Chicken Biryani", "servings": 4}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `python not found` | Install Python and add to PATH |
| `pip not found` | Use `python -m pip install` instead |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `GEMINI_API_KEY not set` | Edit `.env` file with your API key |
| `Failed to fetch` in frontend | Ensure backend is running on port 8000 |
| `Port 8000 in use` | Kill other process or change PORT in `.env` |
| `CORS error` | Backend already configured for all origins |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `GEMINI_MAX_OUTPUT_TOKENS` | `8192` | Max response tokens |
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `DEBUG` | `false` | Enable debug mode |

---

## Deployment (Render)

1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect your GitHub repo
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `GEMINI_API_KEY`
7. Deploy

---

## Tech Stack

- **Backend:** FastAPI, Python 3.11
- **AI:** Google Gemini 2.5 Flash
- **Frontend:** React 18, Tailwind CSS
- **Caching:** In-memory with TTL
- **Rate Limiting:** SlowAPI (10 req/min)

---

## License

MIT License - Feel free to use and modify.
