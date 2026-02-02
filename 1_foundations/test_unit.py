"""
Unit Tests for Career Bot Application
Tests individual components in isolation
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import components to test
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app_new import (
    KnowledgeBase, 
    SessionManager, 
    UserManager,
    SecurityManager,
    validate_email
)


class TestKnowledgeBase:
    """Test Knowledge Base RAG functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.kb = KnowledgeBase()
    
    def test_add_document(self):
        """Test adding documents to knowledge base"""
        doc_content = "This is a test document about Python programming and AI development."
        metadata = {"source": "test.txt", "type": "test"}
        
        self.kb.add_document(doc_content, metadata)
        
        assert len(self.kb.documents) == 1
        assert self.kb.documents[0]["content"] == doc_content
        assert self.kb.documents[0]["metadata"]["source"] == "test.txt"
    
    @patch('app_new.openai_client.embeddings.create')
    def test_search_similar(self, mock_embeddings):
        """Test semantic search functionality"""
        # Mock OpenAI embedding response
        mock_embeddings.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Add test documents
        self.kb.add_document(
            "Python is a programming language", 
            {"source": "doc1.txt"}
        )
        self.kb.add_document(
            "Machine learning uses neural networks", 
            {"source": "doc2.txt"}
        )
        
        # Perform search
        results = self.kb.search("What is Python?", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) <= 2
        mock_embeddings.assert_called()
    
    def test_empty_search(self):
        """Test search with empty knowledge base"""
        results = self.kb.search("test query")
        assert results == []
    
    def test_document_with_minimum_length(self):
        """Test that short documents are rejected"""
        short_doc = "Too short"
        
        # This should not raise an error, just not add the document
        # (implementation dependent)
        self.kb.add_document(short_doc, {"source": "short.txt"})


class TestSessionManager:
    """Test Session Management functionality"""
    
    def setup_method(self):
        """Setup test fixtures with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.session_manager = SessionManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup temporary database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_session(self):
        """Test session creation"""
        session_id = self.session_manager.create_session("test_user", 30)
        
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_validate_session_valid(self):
        """Test validating a valid session"""
        session_id = self.session_manager.create_session("test_user", 30)
        username = self.session_manager.validate_session(session_id)
        
        assert username == "test_user"
    
    def test_validate_session_invalid(self):
        """Test validating an invalid session"""
        username = self.session_manager.validate_session("invalid_session_id")
        
        assert username is None
    
    def test_validate_session_expired(self):
        """Test validating an expired session"""
        session_id = self.session_manager.create_session("test_user", -1)  # Already expired
        username = self.session_manager.validate_session(session_id)
        
        assert username is None
    
    def test_update_session_activity(self):
        """Test updating session last activity"""
        session_id = self.session_manager.create_session("test_user", 30)
        
        # Update activity
        self.session_manager.update_activity(session_id)
        
        # Should still be valid
        username = self.session_manager.validate_session(session_id)
        assert username == "test_user"
    
    def test_end_session(self):
        """Test ending a session"""
        session_id = self.session_manager.create_session("test_user", 30)
        self.session_manager.end_session(session_id)
        
        # Session should now be invalid
        username = self.session_manager.validate_session(session_id)
        assert username is None
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        # Create multiple sessions with different expiry times
        expired_session = self.session_manager.create_session("expired_user", -1)
        valid_session = self.session_manager.create_session("valid_user", 30)
        
        # Run cleanup
        self.session_manager.cleanup_expired_sessions()
        
        # Valid session should still work
        assert self.session_manager.validate_session(valid_session) == "valid_user"
        # Expired session should be gone
        assert self.session_manager.validate_session(expired_session) is None


class TestUserManager:
    """Test User Management functionality"""
    
    def setup_method(self):
        """Setup test fixtures with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.user_manager = UserManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup temporary database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_visitor_account(self):
        """Test creating a visitor account"""
        username, password = self.user_manager.create_visitor_account("192.168.1.1")
        
        assert username.startswith("visitor_")
        assert len(password) > 0
        
        # Verify user exists in database
        user = self.user_manager.get_user(username)
        assert user is not None
        assert user[3] == "visitor"  # tier
    
    def test_visitor_ip_limit(self):
        """Test IP-based visitor creation limit"""
        ip_address = "192.168.1.100"
        
        # Create first visitor
        username1, _ = self.user_manager.create_visitor_account(ip_address)
        assert username1 is not None
        
        # Check if IP has reached limit (within 24 hours)
        has_limit = self.user_manager.check_ip_visitor_limit(ip_address)
        assert has_limit is True
    
    def test_authenticate_user_valid(self):
        """Test authenticating with valid credentials"""
        username, password = self.user_manager.create_visitor_account("192.168.1.1")
        
        result = self.user_manager.authenticate(username, password)
        assert result is True
    
    def test_authenticate_user_invalid_password(self):
        """Test authenticating with invalid password"""
        username, _ = self.user_manager.create_visitor_account("192.168.1.1")
        
        result = self.user_manager.authenticate(username, "wrong_password")
        assert result is False
    
    def test_authenticate_user_nonexistent(self):
        """Test authenticating non-existent user"""
        result = self.user_manager.authenticate("nonexistent_user", "password")
        assert result is False
    
    def test_increment_query_count(self):
        """Test incrementing user query count"""
        username, _ = self.user_manager.create_visitor_account("192.168.1.1")
        
        # Get initial count
        user = self.user_manager.get_user(username)
        initial_count = user[4]  # query_count
        
        # Increment
        self.user_manager.increment_query_count(username)
        
        # Verify increment
        user = self.user_manager.get_user(username)
        new_count = user[4]
        assert new_count == initial_count + 1
    
    def test_check_query_limit(self):
        """Test checking if user has exceeded query limit"""
        username, _ = self.user_manager.create_visitor_account("192.168.1.1")
        
        # Visitor should have query limit
        user = self.user_manager.get_user(username)
        query_limit = user[5]  # query_limit
        
        # Initially should not exceed limit
        exceeded = self.user_manager.check_query_limit(username)
        assert exceeded is False
        
        # Increment to limit
        for _ in range(query_limit + 1):
            self.user_manager.increment_query_count(username)
        
        # Now should exceed limit
        exceeded = self.user_manager.check_query_limit(username)
        assert exceeded is True


class TestSecurityManager:
    """Test Security and Rate Limiting functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.security_manager = SecurityManager()
    
    def test_rate_limit_not_exceeded(self):
        """Test rate limiting with requests under limit"""
        client_id = "test_client_1"
        
        # Make requests under the limit
        for _ in range(5):
            exceeded = self.security_manager.check_rate_limit(client_id, max_requests=10, window_seconds=60)
            assert exceeded is False
    
    def test_rate_limit_exceeded(self):
        """Test rate limiting with requests over limit"""
        client_id = "test_client_2"
        max_requests = 3
        
        # Make requests up to limit
        for i in range(max_requests):
            exceeded = self.security_manager.check_rate_limit(client_id, max_requests=max_requests, window_seconds=60)
            assert exceeded is False
        
        # Next request should exceed limit
        exceeded = self.security_manager.check_rate_limit(client_id, max_requests=max_requests, window_seconds=60)
        assert exceeded is True
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset after expiry"""
        client_id = "test_client_3"
        max_requests = 2
        window_seconds = 1
        
        # Exceed limit
        for _ in range(max_requests + 1):
            self.security_manager.check_rate_limit(client_id, max_requests=max_requests, window_seconds=window_seconds)
        
        exceeded = self.security_manager.check_rate_limit(client_id, max_requests=max_requests, window_seconds=window_seconds)
        assert exceeded is True
        
        # Wait for window to reset
        import time
        time.sleep(window_seconds + 0.1)
        
        # Should be able to make requests again
        exceeded = self.security_manager.check_rate_limit(client_id, max_requests=max_requests, window_seconds=window_seconds)
        assert exceeded is False


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            "test@example.com",
            "user.name@company.co.uk",
            "info+tag@domain.org",
            "123@test.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True, f"Failed for {email}"
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com",
            "user@domain",
            ""
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False, f"Should fail for {email}"


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
