"""
Unit tests for FileManager utility.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from app.utils.file_manager import FileManager


@pytest.fixture
def file_manager():
    """Create a FileManager instance with temporary directory."""
    temp_dir = Path(tempfile.mkdtemp())
    fm = FileManager(base_dir=temp_dir)
    fm.initialize()
    yield fm
    # Cleanup
    fm.cleanup_all()
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


class TestFileManager:
    """Test suite for FileManager."""
    
    def test_initialization(self, file_manager):
        """Test FileManager initialization."""
        assert file_manager.uploads_dir.exists()
        assert file_manager.results_dir.exists()
    
    def test_save_upload(self, file_manager):
        """Test saving uploaded file."""
        content = b"Test PDF content"
        filename = "test.pdf"
        
        file_id = file_manager.save_upload(content, filename)
        
        assert file_id is not None
        assert file_manager.file_exists(file_id)
        
        # Verify metadata
        info = file_manager.get_file_info(file_id)
        assert info['filename'] == filename
        assert info['mime_type'] == 'application/pdf'
        assert info['size_bytes'] == len(content)
    
    def test_save_result(self, file_manager):
        """Test saving result file."""
        # Create a temporary source file
        temp_file = file_manager.get_temp_path(suffix=".pdf")
        temp_file.write_text("Result content")
        
        result_id = file_manager.save_result(
            temp_file,
            "result.pdf",
            mime_type="application/pdf"
        )
        
        assert result_id is not None
        assert file_manager.file_exists(result_id)
        
        # Cleanup
        temp_file.unlink()
    
    def test_get_file_path(self, file_manager):
        """Test retrieving file path."""
        content = b"Test content"
        file_id = file_manager.save_upload(content, "test.pdf")
        
        path = file_manager.get_file_path(file_id)
        assert path.exists()
        assert path.read_bytes() == content
    
    def test_delete_file(self, file_manager):
        """Test file deletion."""
        content = b"Test content"
        file_id = file_manager.save_upload(content, "test.pdf")
        
        assert file_manager.file_exists(file_id)
        
        file_manager.delete_file(file_id)
        
        assert not file_manager.file_exists(file_id)
    
    def test_sanitize_filename(self, file_manager):
        """Test filename sanitization."""
        dangerous_names = [
            "../../../etc/passwd",
            "test\\..\\file.pdf",
            "test\x00file.pdf"
        ]
        
        for name in dangerous_names:
            safe_name = file_manager._sanitize_filename(name)
            assert ".." not in safe_name
            assert "/" not in safe_name
            assert "\\" not in safe_name
            assert "\x00" not in safe_name
    
    def test_file_not_found(self, file_manager):
        """Test handling of non-existent file."""
        with pytest.raises(ValueError):
            file_manager.get_file_path("nonexistent-id")
    
    def test_cleanup_all(self, file_manager):
        """Test cleanup of all files."""
        # Create multiple files
        for i in range(3):
            file_manager.save_upload(b"content", f"test{i}.pdf")
        
        file_manager.cleanup_all()
        
        # Verify all metadata cleared
        assert len(file_manager.metadata) == 0
