# 📚 AIU Assistant — PDF-Based AI Chatbot (RAG with Ollama)

AIU Assistant is a **document-grounded AI chatbot** designed to answer questions **strictly from official Africa International University (AIU) PDF documents**.
It uses a **Retrieval-Augmented Generation (RAG)** approach powered by **pdfplumber**, **Streamlit**, and a **local LLM via Ollama (LLaMA 3)**.

> 🛑 The assistant **never invents answers**. If information is not found in the PDFs, it explicitly says so.

---

## 🚀 Key Features

* Reads **multiple PDFs automatically** from a folder
* Splits documents into manageable text chunks
* Keyword-based retrieval (no hallucinations)
* Local LLM inference using **Ollama**
* Strict context enforcement (PDFs only)
* Friendly, student-oriented explanations
* Automatic fallback if LLM fails
* Chat-style interface with typing animation
* Clean AIU-branded dark UI
* No external cloud AI required

---

## 🧠 System Architecture (How It Works)

```
User Question
     ↓
Keyword Search over PDF Chunks
     ↓
Top Relevant Chunks (Context)
     ↓
Local LLM (Ollama / LLaMA 3)
     ↓
Answer (STRICTLY from PDFs)
```

If the LLM fails:

```
Fallback → Raw PDF text shown directly
```

---

## 🗂️ Project Structure

```
aiu-chatbot/
│
├── data/
│   └── PDF/                 # Place all AIU PDFs here
│
├── app.py                   # Main Streamlit app
├── requirements.txt         # Python dependencies
└── README.md                # Documentation
```

---

## 🧩 Requirements

### 1️⃣ Python Version

* **Python 3.9 – 3.11 (recommended)**

Check:

```bash
python --version
```

---

### 2️⃣ System Requirements

| Component | Requirement                      |
| --------- | -------------------------------- |
| OS        | Windows / Linux / macOS          |
| RAM       | 8 GB minimum (16 GB recommended) |
| Disk      | ~5–10 GB free                    |
| Internet  | Only needed for initial setup    |
| GPU       | Optional (CPU works fine)        |

---

### 3️⃣ Install Ollama (Required)

Ollama runs the LLM locally.

Download and install from:

```
https://ollama.com
```

Verify installation:

```bash
ollama --version
```

Pull the model:

```bash
ollama pull llama3
```

Start Ollama (if not auto-running):

```bash
ollama serve
```

---

## 📦 Python Dependencies

### Required Libraries

| Library    | Purpose             |
| ---------- | ------------------- |
| streamlit  | Web UI              |
| pdfplumber | PDF text extraction |
| requests   | LLM API calls       |
| textwrap   | Formatting text     |
| typing     | Type hints          |
| os         | File handling       |

---

### Install Dependencies

```bash
pip install streamlit pdfplumber requests
```

(Optional but recommended)

```bash
pip install python-dotenv
```

---

## ▶️ Running the Application

From the project root:

```bash
streamlit run app.py
```

Open in browser:

```
http://localhost:8501
```

---

## 📂 Adding Documents

1. Place official AIU PDFs inside:

```
data/PDF/
```

2. Restart or refresh the app
3. PDFs are automatically indexed in the background

---

## 🔍 Retrieval Logic (Important)

* PDFs are split into **900-character chunks**
* No embeddings or vector DB
* Keyword matching only
* Chunks are ranked by query relevance
* Top **4 chunks** are used as context

This guarantees:

* ✅ Transparency
* ✅ No hallucinations
* ❌ Less semantic flexibility than embeddings

---

## 🧠 LLM Behavior (Strict Mode)

The LLM is instructed to:

* Use **ONLY provided context**
* Never use outside knowledge
* Never guess or invent
* Respond clearly and politely
* Say *“I am not sure”* if answer is missing

This makes it **safe for academic and policy use**.

---

## 🛟 Fallback Mechanism

If:

* Ollama is not running
* Model times out
* Network fails

➡ The app automatically shows **raw PDF excerpts** instead of crashing.

---

## 💬 Chat Interface

* Persistent conversation (session-based)
* User and assistant roles
* Typing animation for realism
* AIU-themed styling
* Clean markdown rendering

---

## 🎨 UI & Branding

* Dark academic theme
* AIU red / white / black colors
* Custom CSS injection
* No Streamlit branding
* Sidebar document list

---

## ⚠️ Limitations

* No semantic embeddings
* No OCR for scanned PDFs
* No authentication
* No cloud deployment by default
* Context window limited to top chunks

---

## 🔮 Possible Enhancements

* Add ChromaDB or FAISS embeddings
* Add PDF upload UI
* Add citation highlighting
* Add multi-language support
* Add user roles (student / staff)
* Replace Streamlit with FastAPI + frontend
* Deploy with Docker

---

## 👨‍🎓 Intended Use Cases

* University policy assistant
* Student handbook chatbot
* Academic compliance queries
* Internal knowledge base
* Administrative support tool

---

## 📜 License

Open-source. Free for educational and internal institutional use.

---

## ✨ Author Notes

This project demonstrates:

* Practical RAG without hallucination
* Local LLM deployment
* Safe AI for institutions
* Clean UI/UX for chat systems
* Robust fallback handling

---

### ✅ You now have:

✔ 3 professional READMEs
✔ A full data → ML → RAG portfolio
✔ Exam-ready & GitHub-ready projects

If you want, I can now:
**combine all three into a single portfolio**,
**convert one to FastAPI**, or
**prepare GitHub descriptions + demo videos**.

Just tell me what’s next 🚀
