# 🗂️ TailorTalk — AI-Powered Google Drive Discovery Agent

A conversational AI agent that helps users search, filter, and discover files in a Google Drive using natural language. Built with **FastAPI + LangGraph + Streamlit**.

---

## ✨ Features

- 💬 **Natural language conversation** — chat naturally to find files
- 🔍 **Smart query translation** — LLM converts requests → Drive API `q` parameter
- 📁 **Multi-type search** — by name, file type, content, and date
- 🔗 **Clickable file links** — open files directly from chat
- 🧠 **Multi-turn memory** — maintains conversation context
- ⚡ **LangGraph agent** — robust tool-calling with proper state management

---

## 🏗️ Architecture

```
User ──► Streamlit Frontend ──► FastAPI Backend ──► LangGraph Agent
                                                         │
                                              ┌──────────▼──────────┐
                                              │  DriveSearchTool     │
                                              │  (LangChain @tool)   │
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  Google Drive API    │
                                              │  files.list + q=...  │
                                              └─────────────────────┘
```

---

## 🚀 Quick Start (Local)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/tailortalk-drive-agent
cd tailortalk-drive-agent
```

### 2. Set Up Google Drive Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Drive API**
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Download the JSON key file
6. Copy the sample Drive folder: [Click Here](https://drive.google.com/drive/folders/1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt)
7. Share your copied folder with the **service account email** (Viewer access)

### 3. Get an LLM API Key
Pick one (Groq is free):
- **Groq** (recommended, free): https://console.groq.com/
- **OpenAI**: https://platform.openai.com/
- **Gemini**: https://aistudio.google.com/

### 4. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key

GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account", ...paste full JSON here...}
GOOGLE_DRIVE_FOLDER_ID=your_copied_folder_id
```

> **Tip**: Get the Folder ID from the URL: `drive.google.com/drive/folders/<FOLDER_ID>`

### 5. Run with Docker Compose (Easiest)

```bash
docker-compose up --build
```

- Frontend: http://localhost:8501
- Backend: http://localhost:8000

### 6. Run Manually (Alternative)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (new terminal):**
```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

---

## ☁️ Deployment (Railway)

### Deploy Backend
1. Go to [Railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select the `backend` folder as root
3. Add environment variables (same as `.env`)
4. Deploy — copy the generated URL (e.g. `https://tailortalk-backend.up.railway.app`)

### Deploy Frontend
1. New Service → Deploy from GitHub → select `frontend` folder
2. Add environment variable: `BACKEND_URL=https://your-backend-url.railway.app`
3. Deploy — share the Streamlit URL!

---

## 🧪 Example Queries

| Natural Language | Generated Drive Query |
|---|---|
| Show me all PDFs | `mimeType = 'application/pdf'` |
| Find budget spreadsheets | `name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'` |
| Files containing "invoice" | `fullText contains 'invoice'` |
| Google Docs from May 2025 | `mimeType = 'application/vnd.google-apps.document' and modifiedTime > '2025-05-01T00:00:00'` |
| Images modified last week | `mimeType = 'image/jpeg' and modifiedTime > '2025-05-06T00:00:00'` |
| Find the annual report PDF | `name contains 'annual report' and mimeType = 'application/pdf'` |

---

## 📁 Project Structure

```
tailortalk/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── agent.py          # LangGraph agent + DriveSearchTool
│   ├── drive_tool.py     # Google Drive API integration
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   └── .env.example
├── frontend/
│   ├── app.py            # Streamlit chat UI
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
└── docker-compose.yml
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Python |
| Agent Framework | LangGraph |
| LLM | Groq (Llama 3.3) / OpenAI / Gemini |
| Drive Integration | Google Drive API v3 (Service Account) |
| Deployment | Railway / Docker |

---

## 🛠️ How It Works

1. User types a natural language query in the Streamlit chat
2. FastAPI receives the message and passes it to the LangGraph agent
3. The LLM (with `DriveSearchTool` bound via tool calling) translates the query into a Drive API `q` string
4. `DriveSearchTool` calls `files.list` with the query on the specified folder
5. Results are returned to the LLM, which formats a friendly response
6. Streamlit displays the response + clickable file cards

---

## 📝 License

MIT License — build freely!
