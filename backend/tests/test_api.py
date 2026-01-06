"""
Integration tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io
from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_upload_pdf_success(self):
        """Test successful PDF upload."""
        # Create a minimal PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF"
        
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.pdf"
        assert "page_count" in data
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type."""
        files = {
            "file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")
        }
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_upload_file_too_large(self):
        """Test upload with file exceeding size limit."""
        # Create a file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        
        files = {
            "file": ("large.pdf", io.BytesIO(large_content), "application/pdf")
        }
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "too large" in data["error"].lower()
    
    def test_process_invalid_file_id(self):
        """Test processing with invalid file_id."""
        payload = {
            "file_id": "nonexistent-id",
            "intent": "convert_to_word",
            "parameters": {}
        }
        
        response = client.post("/api/process", json=payload)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_process_invalid_intent(self):
        """Test processing with invalid intent."""
        payload = {
            "file_id": "test-id-12345",
            "intent": "invalid_intent",
            "parameters": {}
        }
        
        response = client.post("/api/process", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_download_nonexistent_file(self):
        """Test downloading non-existent file."""
        response = client.get("/api/download/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_delete_file(self):
        """Test file deletion endpoint."""
        # This will return 404 for non-existent file
        response = client.delete("/api/file/test-id")
        
        assert response.status_code == 404


@pytest.fixture
def sample_pdf_bytes():
    """Fixture providing minimal valid PDF bytes."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF"
