#!/usr/bin/env python3
"""
Unit tests for security_scanner.py path validation
Tests for the validate_project_path() function
"""

import pytest
import os
import sys
from pathlib import Path

# Import the validate_project_path function
# We'll need to extract it or import the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "security_scanner",
    Path(__file__).parent / "security_scanner.py"
)
security_scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security_scanner)
validate_project_path = security_scanner.validate_project_path


class TestValidateProjectPath:
    """Test suite for validate_project_path function"""
    
    def test_valid_directory_absolute_path(self, tmp_path):
        """Test validation with valid absolute directory path"""
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        
        result = validate_project_path(str(test_dir))
        
        assert result == str(test_dir.absolute())
        assert os.path.isabs(result)
    
    def test_valid_directory_relative_path(self, tmp_path, monkeypatch):
        """Test validation with valid relative directory path"""
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        
        # Change to parent directory
        monkeypatch.chdir(tmp_path)
        
        result = validate_project_path("test_project")
        
        assert os.path.isabs(result)
        assert result.endswith("test_project")
    
    def test_current_directory(self, tmp_path, monkeypatch):
        """Test validation with current directory '.'"""
        monkeypatch.chdir(tmp_path)
        
        result = validate_project_path(".")
        
        assert result == str(tmp_path)
        assert os.path.isabs(result)
    
    def test_nonexistent_directory(self):
        """Test validation fails with nonexistent directory"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("/nonexistent/directory/path")
        
        assert exc_info.value.code == 2
    
    def test_file_instead_of_directory(self, tmp_path):
        """Test validation fails when path is a file, not a directory"""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path(str(test_file))
        
        assert exc_info.value.code == 2
    
    def test_symlink_directory(self, tmp_path):
        """Test validation fails when path is a symlink"""
        real_dir = tmp_path / "real_directory"
        real_dir.mkdir()
        
        symlink_dir = tmp_path / "symlink_directory"
        symlink_dir.symlink_to(real_dir)
        
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path(str(symlink_dir))
        
        assert exc_info.value.code == 2
    
    def test_path_with_semicolon(self, tmp_path):
        """Test validation fails with semicolon in path"""
        # Note: This tests the input validation, not the filesystem
        # The path string itself is checked for dangerous characters
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test;rm -rf /")
        
        assert exc_info.value.code == 2
    
    def test_path_with_pipe(self, tmp_path):
        """Test validation fails with pipe character in path"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test | cat")
        
        assert exc_info.value.code == 2
    
    def test_path_with_backtick(self, tmp_path):
        """Test validation fails with backtick in path"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test`whoami`")
        
        assert exc_info.value.code == 2
    
    def test_path_with_dollar_sign(self, tmp_path):
        """Test validation fails with dollar sign in path"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test$VARIABLE")
        
        assert exc_info.value.code == 2
    
    def test_path_with_ampersand(self, tmp_path):
        """Test validation fails with ampersand in path"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test & whoami")
        
        assert exc_info.value.code == 2
    
    def test_path_with_redirect(self, tmp_path):
        """Test validation fails with redirect characters in path"""
        with pytest.raises(SystemExit) as exc_info:
            validate_project_path("test > /tmp/output")
        
        assert exc_info.value.code == 2
    
    def test_error_message_shows_absolute_path(self, capsys, tmp_path):
        """Test that error messages display the absolute path"""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test")
        
        with pytest.raises(SystemExit):
            validate_project_path(str(test_file))
        
        captured = capsys.readouterr()
        # Error message should contain the absolute path
        assert str(test_file.absolute()) in captured.out
        assert "not a valid directory" in captured.out
    
    def test_symlink_error_message(self, capsys, tmp_path):
        """Test error message for symlink paths"""
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        
        symlink_dir = tmp_path / "symlink_dir"
        symlink_dir.symlink_to(real_dir)
        
        with pytest.raises(SystemExit):
            validate_project_path(str(symlink_dir))
        
        captured = capsys.readouterr()
        # Error message should contain absolute path
        assert str(symlink_dir.absolute()) in captured.out
    
    def test_forbidden_chars_error_message(self, capsys):
        """Test error message for paths with forbidden characters"""
        with pytest.raises(SystemExit):
            validate_project_path("test;dangerous")
        
        captured = capsys.readouterr()
        assert "forbidden characters" in captured.out


class TestSecurityScannerIntegration:
    """Integration tests to ensure the scanner works with validated paths"""
    
    def test_scanner_with_valid_path(self, tmp_path):
        """Test that SecurityScanner works with validated path"""
        test_dir = tmp_path / "project"
        test_dir.mkdir()
        
        validated_path = validate_project_path(str(test_dir))
        scanner = security_scanner.SecurityScanner(validated_path)
        
        assert scanner.project_path == str(test_dir.absolute())
        assert os.path.exists(scanner.reports_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
