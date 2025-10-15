"""
Unit tests for configuration management.

Tests the Config class and environment variable validation.
"""

import pytest
import os
from unittest.mock import patch
from src.config import Config


class TestConfig:
    """Test suite for Config class."""
    
    def test_config_loads_from_env(self):
        """Test that Config loads values from environment variables."""
        with patch.dict(os.environ, {
            'SFTP_HOST': 'test.example.com',
            'SFTP_USERNAME': 'testuser',
            'SFTP_PASSWORD': 'testpass',
            'SFTP_REMOTE_PATH': '/test/path'
        }):
            # Reload config
            from importlib import reload
            from src import config
            reload(config)
            
            assert config.Config.SFTP_HOST == 'test.example.com'
            assert config.Config.SFTP_USERNAME == 'testuser'
    
    def test_config_validation_raises_on_missing(self):
        """Test that validation raises error when required configs are missing."""
        with patch.dict(os.environ, {
            'SFTP_HOST': '',  # Missing
            'SFTP_USERNAME': 'user',
            'SFTP_PASSWORD': 'pass',
            'SFTP_REMOTE_PATH': '/path'
        }):
            from importlib import reload
            from src import config
            reload(config)
            
            with pytest.raises(ValueError, match="Missing required configuration"):
                config.Config.validate()
    
    def test_config_to_dict_legacy_support(self):
        """Test that to_dict() returns proper dictionary structure."""
        with patch.dict(os.environ, {
            'SFTP_HOST': 'localhost',
            'SFTP_PORT': '22',
            'SFTP_USERNAME': 'user',
            'SFTP_PASSWORD': 'pass',
            'SFTP_REMOTE_PATH': '/data'
        }):
            from importlib import reload
            from src import config
            reload(config)
            
            config_dict = config.Config.to_dict()
            
            assert 'sftp' in config_dict
            assert config_dict['sftp']['host'] == 'localhost'
            assert config_dict['sftp']['port'] == 22
            assert 'destination' in config_dict
            assert 'tracker' in config_dict
    
    def test_config_defaults(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {
            'SFTP_HOST': 'localhost',
            'SFTP_USERNAME': 'user',
            'SFTP_PASSWORD': 'pass',
            'SFTP_REMOTE_PATH': '/data'
        }, clear=True):
            from importlib import reload
            from src import config
            reload(config)
            
            # Check defaults
            assert config.Config.SFTP_PORT == 22
            assert config.Config.TRACKER_DB_PATH == 'data/file_tracker.db'
            assert config.Config.LAKEHOUSE_PATH == 'data/lakehouse/bronze/'
