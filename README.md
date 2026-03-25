# Telegram Trading Copier

This project consists of a FastAPI backend (with a Telegram listener) and a Next.js frontend.

## Prerequisites

- Python 3.9+
- Node.js 18+
- MetaTrader 5 (MT5) Terminal installed and logged in.

## Project Structure

- `backend`: FastAPI application, database, and Telegram client.
- `frontend`: Next.js web dashboard.

## Getting Started

You need to run **three** separate processes (terminals) to have the full system operational.

### 1. Verification of MT5
Ensure your MetaTrader 5 application is open and "AutoTrading" is enabled.

### 2. Backend API Server
This server handles the database and API requests from the frontend.

```powershell
cd backend
# Install dependencies if not already done
# pip install -r requirements.txt

# Run the API server
python -m uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

### 3. Telegram Listener
This separate process connects to Telegram to listen for signals and executes trades on MT5.

```powershell
cd backend
# Run the listener
python -m app.telegram.listener
```

*Note: You will see logs indicating "Telegram Client started..." and connection status.*

### 4. Frontend Dashboard
This is the user interface to view trades and settings.

```powershell
cd frontend
# Install dependencies if not already done
# npm install

# Run the development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

---

## Troubleshooting

### "A required privilege is not held by the client" (Turbopack Error)
If you see this error when running `npm run dev`:
1.  **Run as Administrator**: Open your terminal (PowerShell/CMD) as Administrator. Turbopack requires permission to create symbolic links on Windows.
2.  **Or Disable Turbopack**: Modify `package.json` to use Webpack instead (if applicable), or simply run as Admin.
