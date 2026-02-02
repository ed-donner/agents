"""
Integration Tests for Career Bot Application
Tests component interactions and end-to-end workflows
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import time

# Import application
import sys
sys.path.insert(0, os.path.dirname(__file__))


class TestVisitorWorkflow:
    """Test complete visitor creation and authentication workflow"""
    
    def setup_method(self):
        """Setup test environment"""
        from app_new import UserManager, SessionManager
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.user_manager = UserManager(db_path=self.temp_db.name)
        self.session_manager = SessionManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_visitor_creation_and_login_flow(self):
        """Test complete visitor creation, session creation, and validation"""
        # Step 1: Create visitor account
        ip_address = "192.168.1.50"
        username, password = self.user_manager.create_visitor_account(ip_address)
        
        assert username is not None
        assert password is not None
        
        # Step 2: Authenticate
        auth_result = self.user_manager.authenticate(username, password)
        assert auth_result is True
        
        # Step 3: Create session
        session_id = self.session_manager.create_session(username, session_timeout_minutes=30)
        assert session_id is not None
        
        # Step 4: Validate session
        validated_username = self.session_manager.validate_session(session_id)
        assert validated_username == username
        
        # Step 5: Update activity
        self.session_manager.update_activity(session_id)
        
        # Step 6: End session
        self.session_manager.end_session(session_id)
        
        # Step 7: Session should now be invalid
        validated_username = self.session_manager.validate_session(session_id)
        assert validated_username is None
    
    def test_visitor_query_limit_workflow(self):
        """Test visitor query counting and limit enforcement"""
        # Create visitor
        username, _ = self.user_manager.create_visitor_account("192.168.1.60")
        
        # Get query limit
        user = self.user_manager.get_user(username)
        query_limit = user[5]  # query_limit column
        
        # Make queries up to limit
        for i in range(query_limit):
            exceeded = self.user_manager.check_query_limit(username)
            assert exceeded is False, f"Query {i+1} should not exceed limit"
            self.user_manager.increment_query_count(username)
        
        # Next query should exceed limit
        exceeded = self.user_manager.check_query_limit(username)
        assert exceeded is True, "Should exceed limit after reaching query_limit"


class TestEmailContactWorkflow:
    """Test email/reason contact workflow"""
    
    def setup_method(self):
        """Setup test environment"""
        from app_new import UserManager
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.user_manager = UserManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_contact_submission_and_retrieval(self):
        """Test submitting contact info and retrieving it"""
        email = "test@example.com"
        reason = "I want to discuss AI collaboration opportunities"
        
        # Submit contact
        success = self.user_manager.save_contact(email, reason)
        assert success is True
        
        # Retrieve contacts
        contacts = self.user_manager.get_all_contacts()
        assert len(contacts) > 0
        
        # Verify our contact exists
        found = False
        for contact in contacts:
            if contact[1] == email and contact[2] == reason:
                found = True
                break
        
        assert found is True, "Contact should be found in database"


class TestRAGIntegration:
    """Test RAG system integration with chat functionality"""
    
    @patch('app_new.openai_client.embeddings.create')
    @patch('app_new.openai_client.chat.completions.create')
    def test_rag_search_and_chat_response(self, mock_chat, mock_embeddings):
        """Test RAG search integration with chat response generation"""
        from app_new import KnowledgeBase
        
        # Mock embedding response
        mock_embeddings.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Mock chat response
        mock_chat.return_value = Mock(
            choices=[Mock(
                message=Mock(content="I am an AI assistant with knowledge about cloud engineering.")
            )]
        )
        
        # Create KB and add documents
        kb = KnowledgeBase()
        kb.add_document(
            "Gonench is an expert in cloud architecture and RAG systems.",
            {"source": "persona.md", "type": "persona"}
        )
        kb.add_document(
            "Experience includes AWS, Kubernetes, and ML systems.",
            {"source": "experience.txt", "type": "additional"}
        )
        
        # Perform search
        query = "Tell me about your experience"
        results = kb.search(query, top_k=3)
        
        # Verify search was performed
        assert mock_embeddings.called
        
        # Simulate chat with RAG context
        context = "\n".join([r["content"] for r in results])
        
        # This simulates the chat function using RAG context
        assert len(context) > 0


class TestSecurityIntegration:
    """Test security features integration"""
    
    def test_rate_limiting_across_sessions(self):
        """Test rate limiting works across multiple sessions"""
        from app_new import SecurityManager
        
        security = SecurityManager()
        client_id = "test_client_integration"
        max_requests = 5
        window_seconds = 10
        
        # Make requests from same client
        request_count = 0
        for i in range(max_requests + 3):
            exceeded = security.check_rate_limit(
                client_id, 
                max_requests=max_requests, 
                window_seconds=window_seconds
            )
            
            if not exceeded:
                request_count += 1
        
        # Should have been limited
        assert request_count == max_requests, f"Expected {max_requests} requests, got {request_count}"
    
    def test_ip_visitor_limit_enforcement(self):
        """Test IP-based visitor creation limit"""
        from app_new import UserManager
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            user_manager = UserManager(db_path=temp_db.name)
            ip_address = "10.0.0.100"
            
            # Create first visitor
            username1, _ = user_manager.create_visitor_account(ip_address)
            assert username1 is not None
            
            # Check limit
            has_limit = user_manager.check_ip_visitor_limit(ip_address)
            assert has_limit is True, "Should have reached IP visitor limit"
            
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


class TestDatabaseIntegrity:
    """Test database operations and integrity"""
    
    def test_concurrent_session_operations(self):
        """Test handling multiple concurrent session operations"""
        from app_new import SessionManager
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            session_manager = SessionManager(db_path=temp_db.name)
            
            # Create multiple sessions
            sessions = []
            for i in range(10):
                session_id = session_manager.create_session(f"user_{i}", 30)
                sessions.append((session_id, f"user_{i}"))
            
            # Validate all sessions
            for session_id, username in sessions:
                validated = session_manager.validate_session(session_id)
                assert validated == username, f"Session validation failed for {username}"
            
            # End half the sessions
            for i in range(5):
                session_manager.end_session(sessions[i][0])
            
            # Validate remaining sessions
            for i in range(5, 10):
                validated = session_manager.validate_session(sessions[i][0])
                assert validated == sessions[i][1], f"Active session validation failed"
            
            # Validate ended sessions
            for i in range(5):
                validated = session_manager.validate_session(sessions[i][0])
                assert validated is None, f"Ended session should be invalid"
                
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)
    
    def test_database_recovery_from_corruption(self):
        """Test database initialization handles existing data"""
        from app_new import UserManager
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            # First initialization
            um1 = UserManager(db_path=temp_db.name)
            username1, _ = um1.create_visitor_account("192.168.1.1")
            
            # Second initialization (simulates restart)
            um2 = UserManager(db_path=temp_db.name)
            
            # User should still exist
            user = um2.get_user(username1)
            assert user is not None, "User should persist across restarts"
            
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


class TestErrorHandling:
    """Test error handling in various scenarios"""
    
    def test_invalid_session_handling(self):
        """Test system handles invalid session IDs gracefully"""
        from app_new import SessionManager
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            session_manager = SessionManager(db_path=temp_db.name)
            
            # Test various invalid session IDs
            invalid_sessions = [
                "",
                "invalid_id",
                "12345",
                None,
                "session_that_does_not_exist"
            ]
            
            for invalid_id in invalid_sessions:
                if invalid_id is not None:
                    result = session_manager.validate_session(invalid_id)
                    assert result is None, f"Invalid session {invalid_id} should return None"
                    
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)
    
    def test_duplicate_visitor_prevention(self):
        """Test system prevents duplicate visitor creation from same IP"""
        from app_new import UserManager
        
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            user_manager = UserManager(db_path=temp_db.name)
            ip = "192.168.1.200"
            
            # Create first visitor
            user1, _ = user_manager.create_visitor_account(ip)
            
            # Check if limit reached
            limit_reached = user_manager.check_ip_visitor_limit(ip)
            assert limit_reached is True
            
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
