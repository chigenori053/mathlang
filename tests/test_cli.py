import pytest
from unittest.mock import patch, mock_open
from main import main
import sys

def test_cli_runs_valid_file(capsys):
    source = """
    x = 1 + 1
    show x
    """
    with patch("builtins.open", mock_open(read_data=source)):
        # Pass arguments to main via the argv parameter
        return_code = main(['test.mlang', '--lang', 'en'])
            
    captured = capsys.readouterr()
    
    assert return_code == 0
    assert "x = 1 + 1 → 2" in captured.out
    assert "show x → 2" in captured.out
    assert "Output: 2" in captured.out

def test_cli_handles_file_not_found(capsys):
    with patch("builtins.open", side_effect=FileNotFoundError):
        return_code = main(['nonexistent.mlang', '--lang', 'en'])
            
    captured = capsys.readouterr()
    
    assert return_code == 1
    assert "Error: File not found" in captured.err

def test_cli_handles_parser_error(capsys):
    source = "x = @"
    with patch("builtins.open", mock_open(read_data=source)):
        return_code = main(['bad.mlang', '--lang', 'en'])
            
    captured = capsys.readouterr()
    
    assert return_code == 1
    assert "Error:" in captured.err
    assert "Unexpected character" in captured.err

def test_cli_handles_evaluation_error(capsys):
    source = "x = 1 / 0"
    with patch("builtins.open", mock_open(read_data=source)):
        return_code = main(['bad_eval.mlang', '--lang', 'en'])
            
    captured = capsys.readouterr()
    
    assert return_code == 1
    assert "Error: Division by zero" in captured.err
