# Voice PDF Assistant - Backend

Production-ready Python FastAPI backend for voice-controlled PDF document processing.

## 🎯 Overview

This backend powers a voice-controlled PDF assistant that processes PDFs based on natural language commands from the Next.js frontend. It handles PDF uploads, executes operations like extraction, conversion, and editing, then returns downloadable results.

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application & routes
│   ├── config.py               # Configuration management
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── pdf_service.py      # Core PDF processing logic
│   │   └── command_parser.py   # Command interpretation
│   └── utils/
│       └── file_manager.py     # Temporary file handling
├── tests/                      # Unit & integration tests
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment (optional):**
   ```bash
   copy .env.example .env
   # Edit .env with your settings
   ```

### Running the Server

**Development mode (with auto-reload):**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Or using Python directly:**

```bash
python -m app.main
```

The API will be available at:

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check

```http
GET /api/health
```

Returns service status and version.

### Upload PDF

```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**

```json
{
  "file_id": "uuid-string",
  "filename": "document.pdf",
  "page_count": 10,
  "size_mb": 2.5
}
```

### Process PDF

```http
POST /api/process
Content-Type: application/json

{
  "file_id": "uuid-string",
  "intent": "convert_to_word",
  "parameters": {}
}
```

**Response:**

```json
{
  "result_file_id": "uuid-string",
  "filename": "document_converted.docx",
  "message": "Successfully processed: Converting entire PDF to Word document",
  "operation": "convert_to_word"
}
```

### Download Result

```http
GET /api/download/{file_id}
```

Returns the processed file for download.

### Delete File

```http
DELETE /api/file/{file_id}
```

Manually delete a temporary file.

## 🧠 Supported Commands

### 1. Convert to Word

```json
{
  "intent": "convert_to_word",
  "parameters": {}
}
```

### 2. Extract Specific Pages

```json
{
  "intent": "extract_pages",
  "parameters": {
    "pages": [1, 3, 5],
    "format": "pdf" // or "docx"
  }
}
```

### 3. Extract Page Range

```json
{
  "intent": "extract_page_range",
  "parameters": {
    "startPage": 2,
    "endPage": 5,
    "format": "pdf"
  }
}
```

### 4. Remove Pages

```json
{
  "intent": "remove_pages",
  "parameters": {
    "pages": [1, 3]
  }
}
```

### 5. Merge Pages

```json
{
  "intent": "merge_pages",
  "parameters": {
    "pages": [2, 3, 4]
    // OR
    "startPage": 2,
    "endPage": 4
  }
}
```

### 6. Extract to Word

```json
{
  "intent": "extract_to_word",
  "parameters": {
    "pages": [2, 3]
  }
}
```

## 🛡️ Security Features

- **File Type Validation**: Only PDF files accepted
- **Size Limits**: Maximum 50MB upload size
- **Sanitized Filenames**: Prevents directory traversal attacks
- **Temporary Storage**: No persistent file storage
- **Auto-Cleanup**: Files automatically deleted after timeout
- **CORS Protection**: Configured for trusted origins only

## 🔧 Configuration

Environment variables (`.env` file):

```env
# API Settings
API_TITLE=Voice PDF Assistant API
API_VERSION=1.0.0

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# File Settings
MAX_FILE_SIZE_MB=50
UPLOAD_CLEANUP_SECONDS=3600
RESULT_CLEANUP_SECONDS=1800

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=True

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

**Run all tests:**

```bash
pytest
```

**Run with coverage:**

```bash
pytest --cov=app --cov-report=html
```

**Run specific test file:**

```bash
pytest tests/test_command_parser.py -v
```

## 📦 Dependencies

### Core Framework

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### PDF Processing

- **PyMuPDF (fitz)**: Fast PDF manipulation
- **pdfplumber**: Text and table extraction

### Document Conversion

- **python-docx**: Word document generation
- **Pillow**: Image processing

### Development

- **pytest**: Testing framework
- **httpx**: HTTP client for tests

## 🔄 Request Flow

1. **Upload**: Frontend uploads PDF → Backend returns `file_id`
2. **Command**: Frontend sends confirmed command with `file_id`
3. **Process**: Backend executes PDF operation
4. **Result**: Backend returns `result_file_id`
5. **Download**: Frontend downloads via `result_file_id`
6. **Cleanup**: Files auto-deleted after timeout

## 📊 Performance Considerations

- **Streaming**: File uploads use streaming to avoid memory overflow
- **Efficient Processing**: PyMuPDF optimized for speed
- **Background Tasks**: Cleanup runs asynchronously
- **Memory Management**: Avoids loading entire PDFs into memory
- **Concurrent Requests**: Thread-safe file operations

## 🔮 Extensibility

The backend is designed for easy extension:

### Adding OCR Support

```python
# In pdf_service.py
def _extract_with_ocr(self, file_id: str) -> str:
    import pytesseract
    # Implement OCR logic
```

### Adding LLM Command Parsing

```python
# In command_parser.py
def parse_natural_language(self, text: str) -> PDFCommand:
    # Use LLM to interpret free-form commands
```

### Adding Batch Operations

```python
# New endpoint in main.py
@app.post("/api/batch-process")
async def batch_process(requests: List[ProcessRequest]):
    # Process multiple files
```

## 🐛 Error Handling

All errors return consistent JSON format:

```json
{
  "error": "Human-readable error message"
}
```

Common error codes:

- `400`: Invalid request (bad parameters, wrong file type)
- `404`: File not found or expired
- `500`: Internal server error

## 📝 Logging

Logs are written to console with the following format:

```
2024-12-18 10:30:45 - app.main - INFO - Uploaded PDF: document.pdf (ID: abc123, Pages: 10)
```

Configure log level via `LOG_LEVEL` environment variable.

## 🚢 Production Deployment

### Using Gunicorn (recommended for production):

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Integration with Frontend

Update your Next.js frontend API calls:

```typescript
// Upload PDF
const formData = new FormData();
formData.append("file", pdfFile);

const uploadRes = await fetch("http://localhost:8000/api/upload", {
  method: "POST",
  body: formData,
});
const { file_id } = await uploadRes.json();

// Process command
const processRes = await fetch("http://localhost:8000/api/process", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    file_id,
    intent: "convert_to_word",
    parameters: {},
  }),
});
const { result_file_id } = await processRes.json();

// Download result
window.location.href = `http://localhost:8000/api/download/${result_file_id}`;
```

## 📄 License

This backend is part of the Voice PDF Assistant project.

## 🆘 Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'fitz'`
**Solution**: Install PyMuPDF: `pip install PyMuPDF`

**Problem**: Port 8000 already in use
**Solution**: Change port: `uvicorn app.main:app --port 8001`

**Problem**: CORS errors from frontend
**Solution**: Update `CORS_ORIGINS` in `.env` to include your frontend URL

**Problem**: File cleanup not working
**Solution**: Check background tasks are enabled and adjust cleanup timeouts in config

---

**Built with ❤️ using FastAPI and PyMuPDF**
