"""
Integration tests for authentication and session management.

Tests the complete login/logout/re-login flow to verify session management works properly.
Uses admin user credentials from users_seed.json for test data.
"""

import pytest
import json
import jwt
from datetime import datetime, timedelta, timezone
from flask import Flask
from models.user_session import UserSession
from models.library_user import LibraryUser
from constants.config import JWT_SECRET_KEY


@pytest.mark.integration
class TestAuthSessionManagement:
    """Test class for authentication and session management integration tests."""

    def test_complete_session_lifecycle(self, client, db_session, admin_user, admin_user_data):
        """
        Test complete session lifecycle: login → session validation → logout → re-login.
        
        This test verifies:
        1. User can login successfully and receive session token
        2. Session token can be used to access protected resources
        3. Session can be invalidated (logout)
        4. User can re-login after logout
        """
        
        # Step 1: Get nonce for login
        nonce_response = client.get('/api/v1/nonce')
        assert nonce_response.status_code == 200
        
        nonce_data = json.loads(nonce_response.data)
        assert 'nonce' in nonce_data
        nonce = nonce_data['nonce']
        
        # Step 2: Login with admin credentials (using test email from fixture)
        login_data = {
            'email': admin_user.email,  # Use the email from the created admin user
            'password': admin_user_data['password'],
            'nonce': nonce
        }
        
        login_response = client.post('/api/v1/login', 
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        # Debug: Print response if login fails
        if login_response.status_code != 200:
            print(f"Login failed with status {login_response.status_code}")
            print(f"Response: {json.loads(login_response.data)}")
        
        assert login_response.status_code == 200
        
        login_result = json.loads(login_response.data)
        assert login_result['message'] == 'Login successful'
        assert login_result['user_id'] == admin_user.user_id
        assert login_result['role'] == 'Admin'
        
        # Extract session ID from cookie
        session_id = None
        for cookie in login_response.headers.getlist('Set-Cookie'):
            if 'session_token=' in cookie:
                session_id = cookie.split('session_token=')[1].split(';')[0]
                break
        
        assert session_id is not None, "Session ID should be set in cookie"
        
        # Step 3: Verify session is valid in database
        assert UserSession.is_session_valid(db_session, session_id) is True
        
        # Step 4: Generate JWT token manually for testing (since the API uses both JWT + session)
        from datetime import datetime, timedelta
        from constants.constants import TOKEN_EXPIRY_HOURS
        
        jwt_payload = {
            "user_id": admin_user.user_id,
            "email": admin_user.email,
            "role": admin_user.user_role.role,
            "exp": datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm="HS256")
        
        # Test session with protected endpoint (password reset)
        headers = {'Authorization': f'Bearer {jwt_token}'}
        
        protected_data = {
            'old_password': admin_user_data['password'],
            'new_password1': 'NewPass123!@#',
            'new_password2': 'NewPass123!@#'
        }
        
        protected_response = client.put('/api/v1/account/reset-password',
                                      data=json.dumps(protected_data),
                                      content_type='application/json',
                                      headers=headers)
        
        assert protected_response.status_code == 200
        protected_result = json.loads(protected_response.data)
        assert 'Password changed successfully' in protected_result['message']
        
        # Update admin_user_data password for subsequent tests
        admin_user_data['password'] = 'NewPass123!@#'
        
        # Step 5: Simulate logout by creating and then invalidating a session
        # Since there's no logout endpoint, we'll test session invalidation directly
        user_session = UserSession.create_session(
            session=db_session,
            user_uuid=admin_user.user_uuid,
            device_id='test-device-001',
            user_agent='pytest-test-agent',
            ip_address='127.0.0.1'
        )
        
        # Verify session is active
        assert UserSession.is_session_valid(db_session, user_session.session_id) is True
        
        # Invalidate session (simulate logout)
        logout_success = UserSession.invalidate_session(db_session, user_session.session_id)
        assert logout_success is True
        
        # Verify session is no longer valid
        assert UserSession.is_session_valid(db_session, user_session.session_id) is False
        
        # Step 6: Test re-login after logout
        # Get new nonce
        nonce_response_2 = client.get('/api/v1/nonce')
        assert nonce_response_2.status_code == 200
        
        nonce_data_2 = json.loads(nonce_response_2.data)
        new_nonce = nonce_data_2['nonce']
        
        # Re-login with updated password
        relogin_data = {
            'email': admin_user.email,  # Use the email from the created admin user
            'password': admin_user_data['password'],  # Updated password
            'nonce': new_nonce
        }
        
        relogin_response = client.post('/api/v1/login',
                                     data=json.dumps(relogin_data),
                                     content_type='application/json')
        
        assert relogin_response.status_code == 200
        
        relogin_result = json.loads(relogin_response.data)
        assert relogin_result['message'] == 'Login successful'
        assert relogin_result['user_id'] == admin_user.user_id
        assert relogin_result['role'] == 'Admin'


    def test_login_with_invalid_credentials(self, client, admin_user, admin_user_data):
        """Test login fails with invalid credentials."""
        
        # Get nonce
        nonce_response = client.get('/api/v1/nonce')
        nonce = json.loads(nonce_response.data)['nonce']
        
        # Try login with wrong password
        login_data = {
            'email': admin_user.email,  # Use the test email from created admin user
            'password': 'WrongPassword123!',
            'nonce': nonce
        }
        
        response = client.post('/api/v1/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        
        result = json.loads(response.data)
        assert result['error'] == 'Invalid credentials'


    def test_login_with_invalid_nonce(self, client, admin_user, admin_user_data):
        """Test login fails with invalid nonce."""
        
        login_data = {
            'email': admin_user.email,  # Use the test email from created admin user
            'password': admin_user_data['password'],
            'nonce': 'invalid-nonce-12345'
        }
        
        response = client.post('/api/v1/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        
        result = json.loads(response.data)
        assert result['error'] == 'Invalid or expired nonce'


    def test_protected_endpoint_without_token(self, client):
        """Test protected endpoint rejects requests without valid token."""
        
        protected_data = {
            'old_password': 'SomePassword123!',
            'new_password1': 'NewPass123!@#',
            'new_password2': 'NewPass123!@#'
        }
        
        response = client.put('/api/v1/account/reset-password',
                            data=json.dumps(protected_data),
                            content_type='application/json')
        
        assert response.status_code == 401
        
        result = json.loads(response.data)
        assert result['error'] == 'Token is missing'


    def test_protected_endpoint_with_expired_token(self, client, admin_user):
        """Test protected endpoint rejects expired tokens."""
        
        # Create expired token
        expired_payload = {
            "user_id": admin_user.user_id,
            "email": admin_user.email,
            "role": "Admin",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm="HS256")
        
        headers = {'Authorization': f'Bearer {expired_token}'}
        protected_data = {
            'old_password': 'SomePassword123!',
            'new_password1': 'NewPass123!@#',
            'new_password2': 'NewPass123!@#'
        }
        
        response = client.put('/api/v1/account/reset-password',
                            data=json.dumps(protected_data),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 401
        
        result = json.loads(response.data)
        assert result['error'] == 'Token has expired'


    def test_session_creation_and_management(self, db_session, admin_user):
        """Test UserSession model functionality for session management."""
        
        # Clean up any existing sessions for this user first
        UserSession.deactivate_all_sessions(db_session, admin_user.user_uuid)
        
        # Test session creation
        session1 = UserSession.create_session(
            session=db_session,
            user_uuid=admin_user.user_uuid,
            device_id='device-001',
            user_agent='Mozilla/5.0 Test Browser',
            ip_address='192.168.1.100'
        )
        
        assert session1.user_uuid == admin_user.user_uuid
        assert session1.device_id == 'device-001'
        assert session1.is_active is True
        assert session1.expires_at > datetime.now(timezone.utc)
        
        # Test getting active sessions
        active_sessions = UserSession.get_active_sessions(db_session, admin_user.user_uuid)
        assert len(active_sessions) == 1
        assert active_sessions[0].session_id == session1.session_id
        
        # Test session validation
        assert UserSession.is_session_valid(db_session, session1.session_id) is True
        
        # Test session refresh
        original_expiry = session1.expires_at
        refresh_success = UserSession.refresh_session(db_session, session1.session_id, ttl_minutes=780)  # 13 hours - longer than default
        assert refresh_success is True
        
        # Refresh the session object from database
        db_session.refresh(session1)
        assert session1.expires_at > original_expiry
        
        # Test session invalidation
        invalidate_success = UserSession.invalidate_session(db_session, session1.session_id)
        assert invalidate_success is True
        assert UserSession.is_session_valid(db_session, session1.session_id) is False
        
        # Test creating multiple sessions and deactivating all
        session2 = UserSession.create_session(db_session, admin_user.user_uuid, 'device-002')
        session3 = UserSession.create_session(db_session, admin_user.user_uuid, 'device-003')
        
        # Verify multiple active sessions
        active_count = UserSession.count_active_sessions(db_session, admin_user.user_uuid)
        assert active_count == 2
        
        # Deactivate all sessions
        deactivated_count = UserSession.deactivate_all_sessions(db_session, admin_user.user_uuid)
        assert deactivated_count == 2
        
        # Verify no active sessions remain
        final_active_count = UserSession.count_active_sessions(db_session, admin_user.user_uuid)
        assert final_active_count == 0


    def test_login_with_phone_number(self, client, admin_user, admin_user_data):
        """Test login using phone number instead of email."""
        
        # Get nonce
        nonce_response = client.get('/api/v1/nonce')
        nonce = json.loads(nonce_response.data)['nonce']
        
        # Login with phone number
        login_data = {
            'phone_number': admin_user.phone_number,  # Use the test phone from created admin user
            'password': admin_user_data['password'],
            'nonce': nonce
        }
        
        response = client.post('/api/v1/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['message'] == 'Login successful'
        assert result['user_id'] == admin_user.user_id
        assert result['role'] == 'Admin'


    def test_concurrent_sessions_same_user(self, db_session, admin_user):
        """Test that same user can have multiple concurrent sessions from different devices."""
        
        # Clean up any existing sessions for this user first
        UserSession.deactivate_all_sessions(db_session, admin_user.user_uuid)
        
        # Create sessions from different devices
        session_desktop = UserSession.create_session(
            db_session, admin_user.user_uuid, 'desktop-001', 'Chrome Desktop'
        )
        session_mobile = UserSession.create_session(
            db_session, admin_user.user_uuid, 'mobile-001', 'Mobile Safari'
        )
        session_tablet = UserSession.create_session(
            db_session, admin_user.user_uuid, 'tablet-001', 'iPad Safari'
        )
        
        # Verify all sessions are active
        active_sessions = UserSession.get_active_sessions(db_session, admin_user.user_uuid)
        assert len(active_sessions) == 3
        
        session_ids = [s.session_id for s in active_sessions]
        assert session_desktop.session_id in session_ids
        assert session_mobile.session_id in session_ids
        assert session_tablet.session_id in session_ids
        
        # Invalidate one session (simulate logout from one device)
        UserSession.invalidate_session(db_session, session_mobile.session_id)
        
        # Verify other sessions remain active
        remaining_sessions = UserSession.get_active_sessions(db_session, admin_user.user_uuid)
        assert len(remaining_sessions) == 2
        
        remaining_ids = [s.session_id for s in remaining_sessions]
        assert session_desktop.session_id in remaining_ids
        assert session_tablet.session_id in remaining_ids
        assert session_mobile.session_id not in remaining_ids 