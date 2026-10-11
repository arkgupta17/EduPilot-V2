# EduPilot V2 — AI-Powered Programme Research Assistant

EduPilot is a Retrieval-Augmented Generation (RAG) application designed to help users research academic programmes, understand admission requirements, and explore programme information using indexed knowledge sources.

Instead of manually searching through lengthy documents and webpages, users can ingest information into a knowledge base and ask natural-language questions grounded in retrieved evidence.

## Features

- **PDF ingestion:** Upload PDF documents to build a searchable knowledge base.
- **Website ingestion:** Ingest webpages and supported linked PDF documents.
- **RAG-based question answering:** Retrieve relevant information to answer questions using indexed sources.
- **Knowledge source selection:** Select a document or website to scope queries to the relevant material.
- **Source citations:** Display supporting sources alongside generated answers.
- **Vector search:** Store and retrieve document embeddings using FAISS.
- **OCR support:** Extract text from scanned PDFs where required.
- **Interactive dashboard:** Chat interface for querying knowledge sources and viewing retrieved evidence.

## What's New in EduPilot V2?

EduPilot V2 builds on the original EduPilot project with a stronger focus on document-grounded question answering, knowledge-source management, and a more polished research experience.

| Area | Version 1 | Version 2 |
|---|---|---|
| Knowledge ingestion | Initial document and programme research workflow | Expanded ingestion workflow supporting PDFs, webpages, and supported linked PDF documents |
| Document processing | Foundational content extraction | PDF text extraction, OCR support for scanned documents, and webpage processing |
| Retrieval pipeline | Initial retrieval-based question answering | FAISS-backed semantic retrieval with document and source-level query scoping |
| Answer grounding | Basic RAG question answering | Retrieved evidence and source references presented alongside generated answers |
| Knowledge management | Initial source workflow | Dedicated knowledge-source selection and source management within the dashboard |
| User experience | Earlier interface and interaction flow | Redesigned Next.js dashboard with a more structured research and chat experience |
| Project direction | Initial implementation of the programme research assistant | Greater emphasis on retrieval reliability, evidence-based answers, and source isolation |

### Key Improvements

- **More flexible ingestion:** Work with programme information from PDFs and webpages rather than relying on a single content format.
- **Evidence-oriented answers:** Retrieve relevant content from indexed knowledge sources and display supporting references.
- **Knowledge-source scoping:** Select a document or website to focus questions on the intended source.
- **Improved interface:** Provide a more organized workspace for source selection, conversations, and retrieved evidence.
- **Foundation for evaluation:** Establish a clearer path toward testing retrieval quality, answer grounding, and source isolation.

### Development Status

EduPilot V2 is actively evolving. Retrieval reliability, source isolation, evaluation, and deployment readiness remain areas for continued improvement.



## Architecture

EduPilot V2 uses a frontend and backend architecture:

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI
- **Retrieval:** FAISS vector store and embedding-based semantic search
- **Document processing:** PDF text extraction, OCR, and webpage processing
- **Generation:** Large language model integration for answer generation

## Project Structure

```text
EduPilot-V2/
├── backend/       # API, ingestion, retrieval, and RAG pipeline
├── frontend/      # Next.js dashboard and user interface
├── scripts/       # Supporting scripts
├── README.MD
└── .gitignore
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Python
- Node.js and npm
- Tesseract OCR, if OCR functionality is required
- Access to the language model provider configured by the backend

### 1. Clone the repository

```bash
git clone https://github.com/arkgupta17/EduPilot-V2.git
cd EduPilot-V2
```

### 2. Configure the backend

Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies using the dependency file provided in `backend/`.

Configure the required environment variables using a local `.env` file. Never commit API keys or credentials.

Start the backend using the project's configured entry point. If `run_server.py` is present in `backend/`, run:

```bash
cd backend
python run_server.py
```

### 3. Configure the frontend

Open another terminal:

```bash
cd frontend
npm install
```

Configure the frontend environment variables as needed. For local development, the API URL can point to:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

> Setup commands and environment variables may need adjustment to match the dependency files and configuration in the repository.

## How It Works

1. Upload a PDF or ingest a website.
2. Process and extract the source content.
3. Split the content into searchable chunks and generate embeddings.
4. Store the embeddings in FAISS.
5. Select a knowledge source and ask a question.
6. Retrieve relevant content and generate an answer with supporting evidence.

## Security

- Keep API keys, access tokens, and credentials out of version control.
- Do not commit private documents, local environment files, or sensitive datasets.
- Review retrieved evidence and generated answers before relying on them for important decisions.

## Roadmap

- Improve retrieval quality and answer grounding.
- Strengthen knowledge-source isolation.
- Add a repeatable evaluation suite for RAG responses.
- Improve document processing and error handling.
- Prepare the application for reliable deployment.

## Author

**Ark Gupta**

GitHub: [@arkgupta17](https://github.com/arkgupta17)

---

*EduPilot V2 is an evolving project focused on making programme research more accessible through retrieval-augmented generation.*
