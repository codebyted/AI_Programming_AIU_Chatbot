import os
import textwrap
from typing import List, Tuple

import pdfplumber
import requests
import streamlit as st

# =============================
# CONFIGURATION
# =============================

PDF_FOLDER = "data/PDF"   # Folder where your PDFs live
CHUNK_SIZE = 900          # Characters per chunk of PDF text
MAX_CONTEXT_CHUNKS = 4    # How many chunks to feed into the LLM
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3:latest"  # using llama3:latest


# =============================
# PDF LOADING & INDEXING
# =============================

def load_pdfs(folder_path: str) -> List[Tuple[str, str]]:
    """
    Load all PDF files from folder_path and return a list of (filename, full_text).
    Runs silently except if a PDF is completely unreadable.
    """
    documents = []
    if not os.path.isdir(folder_path):
        return documents

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            try:
                with pdfplumber.open(full_path) as pdf:
                    pages_text = []
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        pages_text.append(page_text)
                    full_text = "\n".join(pages_text).strip()
                    if full_text:
                        documents.append((filename, full_text))
            except Exception as e:
                # Only warn if something is really wrong with a file
                st.warning(f"Could not read {filename}: {e}")
    return documents


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Split a long string into non-overlapping chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size
    return chunks


def build_index(documents: List[Tuple[str, str]]):
    """
    Turn raw documents into a searchable list of chunks.
    Each item in the index is (doc_name, chunk_text).
    """
    index = []
    for name, text in documents:
        for chunk in split_into_chunks(text):
            if chunk:
                index.append((name, chunk))
    return index


def search_index(query: str, index: List[Tuple[str, str]]):
    """
    Simple keyword-based search:
    - Lowercase query & chunks
    - Score chunks based on how many query words they contain
    - Return best chunks
    """
    query = query.strip().lower()
    if not query:
        return []

    query_words = [w for w in query.split() if len(w) > 2]
    if not query_words:
        return []

    scored_chunks = []
    for doc_name, chunk in index:
        chunk_lower = chunk.lower()
        score = 0
        for word in query_words:
            if word in chunk_lower:
                score += 1
        if score > 0:
            scored_chunks.append((score, doc_name, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:MAX_CONTEXT_CHUNKS]

    results = []
    for score, doc_name, chunk in top_chunks:
        results.append((doc_name, chunk))
    return results


# =============================
# LLM CALL (OLLAMA)
# =============================

def call_ollama_llm(question: str, context: str) -> str:
    """
    Call a local LLM via Ollama.
    Strongly instructs the model to use ONLY the provided context.
    """
    system_prompt = (
        "You are a helpful assistant for Africa International University (AIU) PDF documents. "
        "You MUST answer strictly and only using the information in the provided CONTEXT. "
        "If the answer is not explicitly in the context, you MUST reply: "
        "\"I am not sure; the PDFs I have do not say that clearly.\" "
        "Do NOT invent facts. Do not use outside knowledge. "
        "Be clear, concise, and friendly."
    )

    user_prompt = (
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT (from AIU PDFs):\n{context}\n\n"
        "Now give a clear, student-friendly answer using only this context. "
        "If the context does not contain the answer, say you are not sure."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


# =============================
# ANSWER GENERATION
# =============================

def build_strict_answer_from_chunks(matches: List[Tuple[str, str]]) -> str:
    """
    Non-LLM fallback: just shows the relevant chunks directly from the PDFs.
    """
    if not matches:
        return (
            "I could not find an exact answer to your question in the available PDFs. "
            "Please try rephrasing your question or checking the documents directly."
        )

    blocks = []
    for doc_name, chunk in matches:
        wrapped = textwrap.fill(chunk, width=90)
        block = f"From **{doc_name}**:\n\n{wrapped}"
        blocks.append(block)

    return "\n\n---\n\n".join(blocks)


def generate_answer(query: str, index: List[Tuple[str, str]], use_llm: bool) -> str:
    """
    - Search for relevant PDF chunks.
    - If use_llm: feed them to the LLM with strict instructions.
      If LLM fails, fall back to strict chunk answer.
    """
    matches = search_index(query, index)

    if not matches:
        return (
            "I could not find a matching answer to your question in the PDFs. "
            "Try using different words that might appear in the documents."
        )

    # Build context text for the LLM
    context_pieces = []
    for doc_name, chunk in matches:
        context_pieces.append(f"Document: {doc_name}\n{chunk}")
    context_text = "\n\n-----\n\n".join(context_pieces)

    # Always use LLM now
    try:
        llm_answer = call_ollama_llm(query, context_text)
        return llm_answer
    except Exception as e:
        st.warning(f"⚠️ LLM call failed, falling back to PDF text only. Error: {e}")
        return build_strict_answer_from_chunks(matches)


# =============================
# STREAMLIT UI HELPERS
# =============================

def inject_custom_css():
    """
    Apply AIU-style theme (red, white, black) and clean layout.
    """
    st.markdown(
        """
        <style>
        /* Hide default Streamlit chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Page background */
        body, .block-container {
            background-color: #111111;
        }

        [data-testid="stAppViewContainer"] > .main {
            background: #111111;
        }

        .block-container {
            padding-top: 1.5rem;
        }

        /* Header text */
        .aiu-title {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-weight: 700;
            font-size: 2rem;
            color: #ffffff;
        }
        .aiu-subtitle {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 0.95rem;
            color: #cccccc;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #181818;
            border-right: 1px solid #2a2a2a;
        }
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {
            color: #f0f0f0;
        }

        /* Loaded docs badge */
        .aiu-doc-badge {
            background-color: #222222;
            border-radius: 0.75rem;
            padding: 0.6rem 0.8rem;
            border: 1px solid #333333;
            font-size: 0.85rem;
            color: #f0f0f0;
        }
        .aiu-doc-badge strong {
            color: #ff4b4b;
        }

        /* Chat messages */
        .stChatMessage {
            border-radius: 16px;
            padding: 10px 14px;
            margin-bottom: 10px;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 0.95rem;
        }
        .stChatMessage[data-testid="stChatMessageUser"] {
            background: linear-gradient(135deg, #d71920, #9a0f16);
            color: #ffffff;
        }
        .stChatMessage[data-testid="stChatMessageAssistant"] {
            background-color: #181818;
            border: 1px solid #2d2d2d;
            color: #f5f5f5;
        }

        /* Chat input */
        div[data-testid="stChatInput"] {
            border-top: 1px solid #2a2a2a;
        }
        div[data-testid="stChatInput"] textarea {
            background-color: #181818;
            color: #f0f0f0;
            border-radius: 999px !important;
            border: 1px solid #333333;
        }

        /* Typing animation */
        .aiu-typing {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9rem;
            color: #dddddd;
        }
        .aiu-typing-label {
            opacity: 0.85;
        }
        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #d71920;
            display: inline-block;
            animation: blink 1.2s infinite;
        }
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes blink {
            0% { opacity: 0.2; transform: translateY(0px); }
            30% { opacity: 1; transform: translateY(-1px); }
            100% { opacity: 0.2; transform: translateY(0px); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def get_index():
    """
    Build and cache the index in the background (no UI noise).
    """
    documents = load_pdfs(PDF_FOLDER)
    index = build_index(documents)
    doc_names = sorted({name for name, _ in documents})
    return index, doc_names


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


# =============================
# MAIN APP
# =============================

def main():
    st.set_page_config(
        page_title="AIU Assistant",
        page_icon="📚",
        layout="wide",
    )

    inject_custom_css()
    init_session_state()

    # Build index quietly (cached)
    index, doc_names = get_index()

    # ========= HEADER =========
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            "<h1 class='aiu-title' style='text-align:center;'>AIU Assistant</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='aiu-subtitle' style='text-align:center;'>Ask questions about official AIU documents and policies.</p>",
            unsafe_allow_html=True,
        )

    # ========= SIDEBAR =========
    with st.sidebar:
        st.markdown("### 📂 Documents")
        if doc_names:
            st.markdown(
                f"<div class='aiu-doc-badge'><strong>{len(doc_names)}</strong> PDF(s) loaded from <code>{PDF_FOLDER}</code></div>",
                unsafe_allow_html=True,
            )
            st.markdown("")
            for name in doc_names:
                st.markdown(f"- {name}")
        else:
            st.markdown(
                "<div class='aiu-doc-badge'>No PDFs found. Add files to the folder and refresh.</div>",
                unsafe_allow_html=True,
            )

        # No answer-mode toggle anymore – always LLM
        st.markdown("---")
        st.markdown(
            "<p style='font-size:0.85rem;color:#cccccc;'>Mode: <strong>Friendly AI explanation</strong> based on AIU PDFs only.</p>",
            unsafe_allow_html=True,
        )

    # ========= CHAT AREA =========
    chat_container = st.container()

    with chat_container:
        # Previous conversation
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if not doc_names:
            st.info("Add at least one AIU PDF to start chatting.")
            return

        user_input = st.chat_input("Type your question about AIU policies, rules, or information...")
        if user_input:
            # Show user message
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Assistant message with typing animation
            with st.chat_message("assistant"):
                placeholder = st.empty()

                # Show typing animation immediately
                placeholder.markdown(
                    """
                    <div class="aiu-typing">
                        <span class="aiu-typing-label">AIU Assistant is thinking</span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Generate answer using LLM only
                answer = generate_answer(user_input, index, use_llm=True)

                # Replace typing animation with the final answer
                placeholder.markdown(answer)

            st.session_state["messages"].append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
