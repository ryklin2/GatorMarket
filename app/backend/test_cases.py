##to use this in windows: open a venvironment by running "python -m venv venv" in the terminal pip install -r requirements.txt and python-magic-bin
##after that run "python -m pytest test_cases.py" in the terminal, but realisticlly most of these you want to be running inside the docker container, but some of them should work outside of it or as long as docker is running
## most of these are AI generated too which is bad for tests, but I wanted to play around with it.
## to use your real db to have some more visual debugging with workbench:
## use $env:MYSQL_HOST = "localhost"
## $env:MYSQL_USER = "root"
## $env:MYSQL_PASSWORD = "rootpass"
## $env:MYSQL_DATABASE = "gator_market"
## $env:DB_TESTING_ENABLED = "true"

## alot more of these failed than I would have liked, but many are failing due to running locally and some are intended to fail
## honestly this is a lot of stuff I knew more about at the start of the term, this file would have made stuff so much easier, but I had problems like people not knowing how to call an api function

## not a lot of these are correct or even useful but I wanted to play around with it
## since I generated this with claude after coming up with 10 test cases for just some random functions myself I didn't really look at a lot of the code, MANY work entirely as intended but just are returning the wrong http code
## some of claude's intended codes would probably be better as we definitely have some cases
## like 500 and 400 codes are basically all the same thing cause it doesnt work right?
## also some of the dummy data just doesnt work unless you full on make a db locally, so please dont run this outside of a venv unless you want me to accidentally ruin whatever is in localhost


'''
## also just a funny post-mortem on the presentation just in case Anthony ever reads this:
## I had originally interpreted 'at least 1 image as "well 1 is a number that is at least 1" and Yash was fixing that at the last minute
## but what happened there was he made a new function entirely to upload multiple images and a new db table for it
## But this disconnected product creation from image upload entirely and lead to the the test webp being able to fail to upload

For the record though I maintain that the upload fails it is still entirely rejected from the server as I uploaded some python code to check during the presentation and it was rejected but did not return any error to the frontend or toasts.
Also wow this whole test thing even just like 50% vibe coded is really neat and I'm learning a lot even with the project already over, this seems much more applicable than me desperately trying to learn react and aws and everything else at the same time.
I wish we had a better db schema to start too, but I defintely learned a LOT about sql from it.

'''
 

"""
EXPECTED TEST RESULTS WHEN RUNNING LOCALLY:

[PASS] = Expected to pass in local environment
[FAIL] = Expected to fail in local environment
[VARY] = May pass or fail depending on configuration

----- DIRECT UNIT TESTS -----
[PASS] TestAuthFunctions::test_generate_token - Tests token generation which doesn't need external services
[PASS] TestAuthFunctions::test_token_required_decorator_valid_token - Uses patched request and DB
[PASS] TestAuthFunctions::test_verified_user_required_decorator - Uses patched request and DB
[PASS] TestWishlistFunctions::test_archive_wishlist_item - Uses mocked authentication
[PASS] TestWishlistFunctions::test_get_archived_wishlist - Uses mocked authentication
[PASS] TestProductFunctions::test_verify_image_content - Simple unit test with mocks
[PASS] TestProductFunctions::test_mark_product_as_sold - Uses mocked authentication
[PASS] TestProductFunctions::test_search_products - Uses mocked DB
[PASS] TestEmailVerificationFunctions::test_generate_secure_token - Pure function test
[PASS] TestEmailVerificationFunctions::test_verify_token_signature_valid - Pure function test
[PASS] TestEmailVerificationFunctions::test_verify_token_signature_invalid - Pure function test
[PASS] TestEmailVerificationFunctions::test_verify_token_signature_expired - Uses time mocking
[PASS] TestEmailVerificationFunctions::test_cleanup_expired_tokens_called - Uses patched functions
[PASS] TestMessagingFunctions::test_get_conversation_not_participant - Uses mocked authentication
[PASS] TestMessagingFunctions::test_send_message_too_long - Uses mocked authentication
[PASS] TestMessagingFunctions::test_mark_messages_as_read - Uses mocked authentication
[PASS] TestAdditionalFunctions::test_get_notifications_with_no_data - Uses mocked authentication
[PASS] TestAdditionalFunctions::test_serve_image_product_not_found - Simple route test
[PASS] TestAdditionalFunctions::test_serve_image_pending_approval - Uses mocked send_from_directory

----- INTEGRATION TESTS -----
[PASS] TestRegister::test_register_success - Uses mocked DB
[PASS] TestRegister::test_register_missing_fields - Uses mocked DB
[PASS] TestRegister::test_register_duplicate_username - Uses mocked DB
[PASS] TestRegister::test_register_invalid_email - Simple validation test
[PASS] TestRegister::test_register_weak_password - Simple validation test
[PASS] TestLogin::test_login_success - Uses mocked DB
[PASS] TestLogin::test_login_invalid_username - Uses mocked DB
[PASS] TestLogin::test_login_invalid_password - Uses mocked DB with bcrypt
[PASS] TestLogin::test_login_unverified_email - Uses mocked DB
[PASS] TestLogin::test_login_inactive_account - Uses mocked DB
[PASS] TestAddToWishlist::* - All tests use mocked auth and DB
[PASS] TestGetUserWishlist::* - All tests use mocked auth and DB
[PASS] TestUploadImage::* - All tests use mocked auth and filesystem
[PASS] TestGetProduct::* - All tests use mocked DB
[PASS] TestSendVerificationEmail::* - All tests use mocked DB and email
[PASS] TestConfirmVerification::* - All tests use mocked token verification
[PASS] TestGetUnreadCount::* - All tests use mocked auth and DB
[PASS] TestCreateConversation::* - All tests use mocked auth and DB
[PASS] TestCreateReview::* - All tests use mocked auth and DB
[PASS] TestGetReviewsForSeller::* - All tests use mocked DB
[PASS] TestReportUser::* - All tests use mocked auth and DB

----- AWS DEPENDENT TESTS -----
[FAIL] TestAWSSES::test_ses_setup_success - Needs AWS credentials
[FAIL] TestAWSSES::test_ses_setup_message_rejected - Needs AWS credentials
[FAIL] TestAWSSES::test_ses_setup_access_denied - Needs AWS credentials
[FAIL] TestAWSSES::test_ses_setup_no_env_vars - Needs AWS credentials

----- DATABASE DEPENDENT TESTS -----
[VARY] TestDatabaseConnection::* - These will fail unless DB_TESTING_ENABLED=true

----- ADMIN FUNCTION TESTS -----
[PASS] TestAdminFunctions::* - All tests use mocked admin auth and DB
"""

import pytest
import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import bcrypt
import jwt
import mysql.connector
from io import BytesIO
from werkzeug.datastructures import FileStorage

# Import your app modules (assuming these are in the same directory)
# Note: You may need to adjust imports based on your project structure
from app import app, get_db_connection
from auth import token_required, admin_required, generate_token, verified_user_required
from wishlist import wishlist_bp
from products import products_bp, verify_image_content
from email_verification import email_bp, send_email_ses, verify_token_signature, generate_secure_token, cleanup_expired_tokens
from messaging import messaging_bp
from reviews import reviews_bp
from report import report_bp
from testSES import test_ses_setup

# Configure pytest to skip certain tests in local environment
SKIP_AWS_TESTS = os.environ.get("AWS_TESTING_ENABLED") != "true"
SKIP_DB_TESTS = os.environ.get("DB_TESTING_ENABLED") != "true"

# Setup pytest fixture
@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    """Mock database connection and cursor properly"""
    conn_mock = MagicMock()
    cursor_mock = MagicMock()
    conn_mock.cursor.return_value = cursor_mock

    # By default, get_db_connection always returns a valid connection mock
    with patch('app.get_db_connection', return_value=conn_mock):
        yield cursor_mock, conn_mock

@pytest.fixture
def auth_token():
    """Generate a test auth token"""
    return generate_token(1, 'testuser', 'user')

@pytest.fixture
def admin_token():
    """Generate a test admin token"""
    return generate_token(1, 'admin', 'admin')

# Helper functions for auth mocking
def mock_token_auth(role='user'):
    """Helper to create properly mocked auth decorators"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Directly call the original function with a mock user
            return f({'user_id': 1, 'user_role': role, 'username': 'testuser', 'email': 'test@example.com'}, *args, **kwargs)
        return wrapper
    return decorator

def mock_admin_auth(f):
    """Helper to create properly mocked admin auth decorators"""
    def wrapper(*args, **kwargs):
        # Directly call the original function with a mock admin user
        return f({'user_id': 1, 'user_role': 'admin', 'username': 'admin', 'email': 'admin@example.com'}, *args, **kwargs)
    return wrapper

#################################################
# 1. Authentication Tests (auth.py)
#################################################

class TestRegister:
    """
    Test user registration functionality
    
    Expected Results:
    [PASS] test_register_success: Should fail after the first run...
    [PASS] test_register_missing_fields: Should pass - Simple validation test
    [PASS] test_register_duplicate_username: Should pass - Uses mocked DB error
    [PASS] test_register_invalid_email: Should pass - Simple validation test
    [PASS] test_register_weak_password: Should pass - Simple validation test
    """
    
    def test_register_success(self, client, mock_db):
        """Test successful user registration"""
        cursor_mock, conn_mock = mock_db
        cursor_mock.lastrowid = 1
        
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@sfsu.edu',
            'password': 'Password1!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 201
        assert b'User registered successfully' in response.data
        cursor_mock.execute.assert_called()
        conn_mock.commit.assert_called_once()

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post('/auth/register', json={
            'username': 'missingfields',
            'email': 'missing@sfsu.edu'
            # Missing password, first_name, last_name
        })
        
        assert response.status_code == 400
        assert b'Missing required field' in response.data

    def test_register_duplicate_username(self, client, mock_db):
        """Test registration with existing username"""
        cursor_mock, conn_mock = mock_db
        # Simulate database duplicate key error
        conn_mock.commit.side_effect = mysql.connector.Error("Duplicate entry 'existinguser' for key 'username'")
        
        response = client.post('/auth/register', json={
            'username': 'existinguser',
            'email': 'new@sfsu.edu',
            'password': 'Password1!',
            'first_name': 'Existing',
            'last_name': 'User'
        })
        
        assert response.status_code == 409
        assert b'Username already exists' in response.data

    def test_register_invalid_email(self, client):
        """Test registration with non-SFSU email"""
        response = client.post('/auth/register', json={
            'username': 'invalidemail',
            'email': 'user@gmail.com',  # Not an sfsu.edu email
            'password': 'Password1!',
            'first_name': 'Invalid',
            'last_name': 'Email'
        })
        
        assert response.status_code == 400
        assert b'valid SFSU email' in response.data

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/auth/register', json={
            'username': 'weakpass',
            'email': 'weak@sfsu.edu',
            'password': 'password',  # Weak password
            'first_name': 'Weak',
            'last_name': 'Password'
        })
        
        assert response.status_code == 400
        assert b'Password must be' in response.data

class TestLogin:
    """
    Test user login functionality
    
    Expected Results:
    ✅ test_login_success: Should PASS - Uses mocked DB and bcrypt
    ✅ test_login_invalid_username: Should PASS - Uses mocked DB
    ✅ test_login_invalid_password: Should PASS - Uses mocked DB and bcrypt
    ✅ test_login_unverified_email: Should PASS - Uses mocked DB
    ✅ test_login_inactive_account: Should PASS - Uses mocked DB
    """
    
    def test_login_success(self, client, mock_db):
        """Test successful login"""
        cursor_mock, conn_mock = mock_db
        # Setup mock return value for user query
        hashed_pw = bcrypt.hashpw('Password1!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'username': 'testuser',
            'password_hash': hashed_pw,
            'email': 'test@sfsu.edu',
            'first_name': 'Test',
            'last_name': 'User',
            'verification_status': 'verified',
            'account_status': 'active',
            'user_role': 'user'
        }
        
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'Password1!'
        })
        
        assert response.status_code == 200
        assert b'Login successful' in response.data
        assert b'token' in response.data

    def test_login_invalid_username(self, client, mock_db):
        """Test login with non-existent username"""
        cursor_mock, conn_mock = mock_db
        cursor_mock.fetchone.return_value = None
        
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'Password1!'
        })
        
        assert response.status_code == 401
        assert b'Invalid credentials' in response.data

    def test_login_invalid_password(self, client, mock_db):
        """Test login with wrong password"""
        cursor_mock, conn_mock = mock_db
        # Setup mock return value with correct user but password won't match
        hashed_pw = bcrypt.hashpw('RealPassword1!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'username': 'testuser',
            'password_hash': hashed_pw,
            'email': 'test@sfsu.edu',
            'verification_status': 'verified',
            'account_status': 'active'
        }
        
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'WrongPassword1!'
        })
        
        assert response.status_code == 401
        assert b'Invalid credentials' in response.data

    def test_login_unverified_email(self, client, mock_db):
        """Test login with unverified email"""
        cursor_mock, conn_mock = mock_db
        # Setup mock with unverified user
        hashed_pw = bcrypt.hashpw('Password1!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'username': 'unverified',
            'password_hash': hashed_pw,
            'email': 'unverified@sfsu.edu',
            'verification_status': 'unverified',
            'account_status': 'active'
        }
        
        response = client.post('/auth/login', json={
            'username': 'unverified',
            'password': 'Password1!'
        })
        
        assert response.status_code == 403
        assert b'email is not verified' in response.data

    def test_login_inactive_account(self, client, mock_db):
        """Test login with inactive account"""
        cursor_mock, conn_mock = mock_db
        # Setup mock with inactive account
        hashed_pw = bcrypt.hashpw('Password1!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'username': 'inactive',
            'password_hash': hashed_pw,
            'email': 'inactive@sfsu.edu',
            'verification_status': 'verified',
            'account_status': 'inactive/banned'
        }
        
        response = client.post('/auth/login', json={
            'username': 'inactive',
            'password': 'Password1!'
        })
        
        assert response.status_code == 401
        assert b'Account is not active' in response.data

#################################################
# 2. Wishlist Tests (wishlist.py)
#################################################

class TestAddToWishlist:
    """
    Test wishlist addition functionality
    
    Expected Results:
    [PASS] All tests should pass - Uses mocked auth and DB
    """

class TestGetUserWishlist:
    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_wishlist_success(self, mock_auth, client, mock_db):
        """Test successfully retrieving wishlist"""
        cursor_mock, conn_mock = mock_db
        # this works as intended just returns wrong
        cursor_mock.fetchall.return_value = [
            {'product_id': 1, 'name': 'Test Product', 'image_url': '/images/test.jpg', 'status': 'active'},
            {'product_id': 2, 'name': 'Another Product', 'image_url': '/images/another.jpg', 'status': 'active'}
        ]
        
        response = client.get('/wishlist/user')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['product_id'] == 1
        assert data[1]['name'] == 'Another Product'

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_wishlist_empty(self, mock_auth, client, mock_db):
        """Test retrieving empty wishlist"""
        cursor_mock, conn_mock = mock_db
        # Return empty list
        cursor_mock.fetchall.return_value = []
        
        response = client.get('/wishlist/user')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0
        assert isinstance(data, list)

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_wishlist_db_error(self, mock_auth, client, mock_db):
        """Test database error while retrieving wishlist"""
        cursor_mock, conn_mock = mock_db
        # Simulate database error
        cursor_mock.execute.side_effect = Exception("Database error")
        
        response = client.get('/wishlist/user')
        
        assert response.status_code == 500
        assert b'Failed to fetch wishlist' in response.data

#################################################
# 3. Products Tests (products.py)
#################################################

class TestUploadImage:
    @patch('auth.token_required', side_effect=mock_token_auth())
    @patch('products.verify_image_content', return_value=True)
    @patch('uuid.uuid4', return_value='test-uuid')
    @patch('os.path.join', return_value='/app/product_images/test-uuid_test.jpg')
    def test_upload_image_success(self, mock_join, mock_uuid, mock_verify, mock_auth, client):
        """Test successful image upload"""
        # Create a test file
        test_file = FileStorage(
            stream=BytesIO(b'test file content'),
            filename='test.jpg',
            content_type='image/jpeg',
        )
        
        # Mock file save
        with patch.object(test_file, 'save') as mock_save:
            response = client.post(
                '/products/upload-image',
                data={'file': test_file},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['url'] == '/products/serve-image/test-uuid_test.jpg'
            mock_save.assert_called_once()

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_upload_image_no_file(self, mock_auth, client):
        """Test image upload with no file"""
        response = client.post(
            '/products/upload-image',
            data={},  # No file
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        assert b'No file part' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_upload_image_invalid_type(self, mock_auth, client):
        """Test uploading file with invalid extension"""
        # Create a test file with invalid extension
        test_file = FileStorage(
            stream=BytesIO(b'test file content'),
            filename='test.txt',
            content_type='text/plain',
        )
        
        response = client.post(
            '/products/upload-image',
            data={'file': test_file},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        assert b'Invalid file type' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    @patch('products.verify_image_content', return_value=False)
    def test_upload_invalid_image_content(self, mock_verify, mock_auth, client):
        """Test uploading file with invalid image content"""
        # Create a test file with valid extension but invalid content
        test_file = FileStorage(
            stream=BytesIO(b'not a real image'),
            filename='fake.jpg',
            content_type='image/jpeg',
        )
        
        response = client.post(
            '/products/upload-image',
            data={'file': test_file},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        assert b'Invalid image content' in response.data

class TestGetProduct:
    def test_get_product_success(self, client, mock_db):
        """Test successfully retrieving a product"""
        cursor_mock, conn_mock = mock_db
        # Setup product info
        cursor_mock.fetchone.side_effect = [
            # First fetch for product details
            {
                'product_id': 1,
                'name': 'Test Product',
                'description': 'Test description',
                'price': 99.99,
                'user_id': 1,
                'username': 'seller',
                'seller_rating': 4.5
            },
            # Mock will return None after first fetchone
        ]
        # Setup images
        cursor_mock.fetchall.return_value = [
            {'image_url': '/images/test1.jpg'},
            {'image_url': '/images/test2.jpg'}
        ]
        
        response = client.get('/products/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product_id'] == 1
        assert data['name'] == 'Test Product'
        assert len(data['images']) == 2
        assert data['images'][0] == '/images/test1.jpg'
        assert data['seller_rating'] == 4.5

    def test_get_product_not_found(self, client, mock_db):
        """Test retrieving non-existent product"""
        cursor_mock, conn_mock = mock_db
        # Setup cursor to return None (product not found)
        cursor_mock.fetchone.return_value = None
        
        response = client.get('/products/999')
        
        assert response.status_code == 404
        assert b'Product not found' in response.data

    def test_get_product_no_images(self, client, mock_db):
        """Test retrieving product with no images"""
        cursor_mock, conn_mock = mock_db
        # Setup product info
        cursor_mock.fetchone.return_value = {
            'product_id': 1,
            'name': 'Test Product',
            'description': 'Test description',
            'price': 99.99,
            'user_id': 1,
            'username': 'seller',
            'seller_rating': None
        }
        # Setup empty images list
        cursor_mock.fetchall.return_value = []
        
        response = client.get('/products/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product_id'] == 1
        assert len(data['images']) == 0
        assert data['seller_rating'] == 0.0

#################################################
# 4. Email Verification Tests (email_verification.py)
#################################################

class TestSendVerificationEmail:
    def test_send_verification_email_success(self, client, mock_db):
        """Test successfully sending verification email"""
        cursor_mock, conn_mock = mock_db
        # Setup user for verification
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'verification_status': 'unverified',
            'verification_token_created_at': datetime.now() - timedelta(days=1)
        }
        
        with patch('email_verification.send_email_ses', return_value=True):
            response = client.post('/verify/send', json={
                'email': 'test@sfsu.edu'
            })
            
            assert response.status_code == 200
            assert b'Verification email sent' in response.data
            conn_mock.commit.assert_called_once()

    def test_send_verification_email_user_not_found(self, client, mock_db):
        """Test sending verification email to non-existent user"""
        cursor_mock, conn_mock = mock_db
        # Setup cursor to return None (user not found)
        cursor_mock.fetchone.return_value = None
        
        response = client.post('/verify/send', json={
            'email': 'nonexistent@sfsu.edu'
        })
        
        assert response.status_code == 404
        assert b'User not found' in response.data

    def test_send_verification_email_already_verified(self, client, mock_db):
        """Test sending verification email to already verified user"""
        cursor_mock, conn_mock = mock_db
        # Setup already verified user
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'verification_status': 'verified',
            'verification_token_created_at': None
        }
        
        response = client.post('/verify/send', json={
            'email': 'verified@sfsu.edu'
        })
        
        assert response.status_code == 400
        assert b'Email already verified' in response.data

    def test_send_verification_email_rate_limit(self, client, mock_db):
        """Test rate limiting for verification emails"""
        cursor_mock, conn_mock = mock_db
        # Setup user with recent verification email
        cursor_mock.fetchone.return_value = {
            'user_id': 1,
            'verification_status': 'unverified',
            'verification_token_created_at': datetime.now() - timedelta(seconds=30)  # 30 seconds ago
        }
        
        response = client.post('/verify/send', json={
            'email': 'ratelimited@sfsu.edu'
        })
        
        assert response.status_code == 429
        assert b'Please wait at least 90 seconds' in response.data

class TestConfirmVerification:
    def test_confirm_verification_success(self, client, mock_db):
        """Test successful email verification"""
        cursor_mock, conn_mock = mock_db
        
        # Mock token verification
        with patch('email_verification.verify_token_signature') as mock_verify:
            mock_verify.return_value = {'user_id': 1, 'email': 'test@sfsu.edu', 'timestamp': int(datetime.now().timestamp())}
            
            # Setup user verification data
            cursor_mock.fetchone.return_value = {
                'verification_status': 'unverified',
                'verification_token': 'valid-token'
            }
            
            response = client.get('/verify/confirm?token=valid-token')
            
            assert response.status_code == 200
            assert b'Email verified successfully' in response.data
            cursor_mock.execute.assert_called()
            conn_mock.commit.assert_called_once()

    def test_confirm_verification_invalid_token(self, client):
        """Test verification with invalid token"""
        # Mock token verification to return None (invalid token)
        with patch('email_verification.verify_token_signature', return_value=None):
            response = client.get('/verify/confirm?token=invalid-token')
            
            assert response.status_code == 400
            assert b'Invalid or expired token' in response.data

    def test_confirm_verification_expired_token(self, client):
        """Test verification with expired token"""
        # Mock token verification to indicate expired token
        with patch('email_verification.verify_token_signature') as mock_verify:
            # Token from 25 hours ago (exceeds 24-hour limit)
            mock_verify.return_value = None
            
            response = client.get('/verify/confirm?token=expired-token')
            
            assert response.status_code == 400
            assert b'Invalid or expired token' in response.data

    def test_confirm_verification_already_verified(self, client, mock_db):
        """Test verification for already verified user"""
        cursor_mock, conn_mock = mock_db
        
        # Mock token verification
        with patch('email_verification.verify_token_signature') as mock_verify:
            mock_verify.return_value = {'user_id': 1, 'email': 'verified@sfsu.edu', 'timestamp': int(datetime.now().timestamp())}
            
            # Setup already verified user
            cursor_mock.fetchone.return_value = {
                'verification_status': 'verified',
                'verification_token': 'some-token'
            }
            
            response = client.get('/verify/confirm?token=some-token')
            
            assert response.status_code == 400
            assert b'Email already verified' in response.data

#################################################
# 5. Messaging Tests (messaging.py)
#################################################

class TestGetUnreadCount:
    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_unread_count_success(self, mock_auth, client, mock_db):
        """Test successfully retrieving unread count"""
        cursor_mock, conn_mock = mock_db
        # Setup unread count
        cursor_mock.fetchone.return_value = {'count': 5}
        
        response = client.get('/messaging/unread-count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 5

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_unread_count_zero(self, mock_auth, client, mock_db):
        """Test retrieving unread count when zero"""
        cursor_mock, conn_mock = mock_db
        # Setup zero unread count
        cursor_mock.fetchone.return_value = {'count': 0}
        
        response = client.get('/messaging/unread-count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_get_unread_count_tables_missing(self, mock_auth, client, mock_db):
        """Test retrieving unread count when tables don't exist"""
        cursor_mock, conn_mock = mock_db
        # Simulate table missing error
        cursor_mock.execute.side_effect = mysql.connector.Error("Table 'gator_market.conversation_participants' doesn't exist")
        
        response = client.get('/messaging/unread-count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert 'error' in data
        assert 'not initialized' in data['error']

class TestCreateConversation:
    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_conversation_success(self, mock_auth, client, mock_db):
        """Test successfully creating a conversation"""
        cursor_mock, conn_mock = mock_db
        # Setup table check
        cursor_mock.fetchone.side_effect = [
            ('conversations',),  # Tables exist
            None  # No existing conversation
        ]
        cursor_mock.lastrowid = 123  # New conversation ID
        
        response = client.post('/messaging/conversations', json={
            'product_id': 1,
            'recipient_id': 2,
            'subject': 'Interested in your product',
            'initial_message': 'Is this still available?'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['conversation_id'] == 123
        assert b'created successfully' in response.data
        conn_mock.commit.assert_called_once()

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_conversation_existing(self, mock_auth, client, mock_db):
        """Test adding to existing conversation"""
        cursor_mock, conn_mock = mock_db
        # Setup table check and existing conversation
        cursor_mock.fetchone.side_effect = [
            ('conversations',),  # Tables exist
            (456,)  # Existing conversation ID
        ]
        
        response = client.post('/messaging/conversations', json={
            'product_id': 1,
            'recipient_id': 2,
            'subject': 'Interested in your product',
            'initial_message': 'Following up on my previous message'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['conversation_id'] == 456
        assert b'added to existing conversation' in response.data
        conn_mock.commit.assert_called_once()

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_conversation_missing_fields(self, mock_auth, client):
        """Test creating conversation with missing fields"""
        response = client.post('/messaging/conversations', json={
            'product_id': 1,
            # Missing recipient_id, subject, initial_message
        })
        
        assert response.status_code == 400
        assert b'Missing required field' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_conversation_message_too_long(self, mock_auth, client):
        """Test creating conversation with too long message"""
        response = client.post('/messaging/conversations', json={
            'product_id': 1,
            'recipient_id': 2,
            'subject': 'Interested in your product',
            'initial_message': 'A' * 1001  # Over 1000 characters
        })
        
        assert response.status_code == 400
        assert b'Message is too long' in response.data

#################################################
# 6. Reviews Tests (reviews.py)
#################################################

class TestCreateReview:
    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_review_success(self, mock_auth, client, mock_db):
        """Test successfully creating a review"""
        cursor_mock, conn_mock = mock_db
        
        response = client.post('/reviews/', json={
            'seller_id': 2,
            'rating': 5,
            'comment': 'Great seller, fast shipping!'
        })
        
        assert response.status_code == 201
        assert b'Review created successfully' in response.data
        conn_mock.commit.assert_called_once()

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_review_missing_fields(self, mock_auth, client):
        """Test creating review with missing fields"""
        response = client.post('/reviews/', json={
            'seller_id': 2,
            # Missing rating and comment
        })
        
        assert response.status_code == 400
        assert b'Missing field' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_review_invalid_rating(self, mock_auth, client):
        """Test creating review with invalid rating"""
        response = client.post('/reviews/', json={
            'seller_id': 2,
            'rating': 6,  # Rating must be 1-5
            'comment': 'Amazing seller!'
        })
        
        assert response.status_code == 400
        assert b'Rating must be between 1 and 5' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_create_review_db_error(self, mock_auth, client, mock_db):
        """Test database error while creating review"""
        cursor_mock, conn_mock = mock_db
        # Simulate database error
        cursor_mock.execute.side_effect = Exception("Database error")
        
        response = client.post('/reviews/', json={
            'seller_id': 2,
            'rating': 4,
            'comment': 'Good seller'
        })
        
        assert response.status_code == 500
        assert b'error' in response.data.lower()

class TestGetReviewsForSeller:
    def test_get_reviews_success(self, client, mock_db):
        """Test successfully retrieving seller reviews"""
        cursor_mock, conn_mock = mock_db
        # Setup review data
        cursor_mock.fetchall.return_value = [
            {
                'review_id': 1,
                'rating': 5,
                'comment': 'Great seller!',
                'created_at': datetime.now()
            },
            {
                'review_id': 2,
                'rating': 4,
                'comment': 'Good experience',
                'created_at': datetime.now() - timedelta(days=1)
            }
        ]
        
        response = client.get('/reviews/2')  # Get reviews for seller id 2
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['rating'] == 5
        assert data[1]['comment'] == 'Good experience'

    def test_get_reviews_empty(self, client, mock_db):
        """Test retrieving reviews for seller with no reviews"""
        cursor_mock, conn_mock = mock_db
        # Return empty list
        cursor_mock.fetchall.return_value = []
        
        response = client.get('/reviews/3')  # Get reviews for seller id 3
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0
        assert isinstance(data, list)

    def test_get_reviews_db_error(self, client, mock_db):
        """Test database error while retrieving reviews"""
        cursor_mock, conn_mock = mock_db
        # Simulate database error
        cursor_mock.execute.side_effect = Exception("Database error")
        
        response = client.get('/reviews/2')
        
        assert response.status_code == 500
        assert b'error' in response.data.lower()

#################################################
# 7. Report Tests (report.py)
#################################################

class TestReportUser:
    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_report_user_success(self, mock_auth, client, mock_db):
        """Test successfully reporting a user"""
        cursor_mock, conn_mock = mock_db
        
        response = client.post('/reports/users', json={
            'reported_user_id': 2,
            'reason': 'Suspicious behavior',
            'additional_comments': 'User was asking for payment outside the platform'
        })
        
        assert response.status_code == 201
        assert b'User report submitted successfully' in response.data
        conn_mock.commit.assert_called_once()

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_report_user_missing_fields(self, mock_auth, client):
        """Test reporting user with missing fields"""
        response = client.post('/reports/users', json={
            'reported_user_id': 2
            # Missing reason
        })
        
        assert response.status_code == 400
        assert b'Missing required fields' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_report_user_db_error(self, mock_auth, client, mock_db):
        """Test database error while reporting user"""
        cursor_mock, conn_mock = mock_db
        # Simulate database error
        cursor_mock.execute.side_effect = Exception("Database error")
        
        response = client.post('/reports/users', json={
            'reported_user_id': 2,
            'reason': 'Suspicious behavior'
        })
        
        assert response.status_code == 500
        assert b'Failed to submit report' in response.data

    @patch('auth.token_required', side_effect=mock_token_auth())
    def test_report_user_without_comments(self, mock_auth, client, mock_db):
        """Test reporting user without additional comments"""
        cursor_mock, conn_mock = mock_db
        
        response = client.post('/reports/users', json={
            'reported_user_id': 2,
            'reason': 'Suspicious behavior'
            # No additional_comments
        })
        
        assert response.status_code == 201
        assert b'User report submitted successfully' in response.data
        conn_mock.commit.assert_called_once()

#################################################
# 8. AWS SES Email Testing (testSES.py)
#################################################

class TestAWSSES:
    """
    Test AWS SES email functionality
    
    Expected Results:
    [FAIL] test_ses_setup_success: Will fail locally - Needs AWS credentials
    [FAIL] test_ses_setup_message_rejected: Will fail locally - Needs AWS credentials 
    [FAIL] test_ses_setup_access_denied: Will fail locally - Needs AWS credentials
    [FAIL] test_ses_setup_no_env_vars: Will fail locally - Needs AWS credentials
    """
    @pytest.mark.skipif(SKIP_AWS_TESTS, reason="AWS credentials not available in local environment")
    @patch('boto3.client')
    @patch('os.getenv', return_value='us-west-1')
    def test_ses_setup_success(self, mock_getenv, mock_boto3):
        """Test successful SES email setup"""
        # Setup boto3 client mock
        ses_client_mock = MagicMock()
        mock_boto3.return_value = ses_client_mock
        # Setup successful response
        ses_client_mock.send_email.return_value = {'MessageId': 'test-message-id'}
        
        result = test_ses_setup()
        
        assert result is True
        ses_client_mock.send_email.assert_called_once()

    @pytest.mark.skipif(SKIP_AWS_TESTS, reason="AWS credentials not available in local environment")
    @patch('boto3.client')
    @patch('os.getenv', return_value='us-west-1')
    def test_ses_setup_message_rejected(self, mock_getenv, mock_boto3):
        """Test SES message rejection"""
        # Setup boto3 client mock
        ses_client_mock = MagicMock()
        mock_boto3.return_value = ses_client_mock
        # Setup rejection error - using botocore.exceptions.ClientError, not boto3.exceptions.ClientError
        error_response = {'Error': {'Code': 'MessageRejected', 'Message': 'Email address not verified'}}
        ses_client_mock.send_email.side_effect = ClientError(error_response, 'send_email')
        
        result = test_ses_setup()
        
        assert result is False
        ses_client_mock.send_email.assert_called_once()

    @pytest.mark.skipif(SKIP_AWS_TESTS, reason="AWS credentials not available in local environment")
    @patch('boto3.client')
    @patch('os.getenv', return_value='us-west-1')
    def test_ses_setup_access_denied(self, mock_getenv, mock_boto3):
        """Test SES access denied"""
        # Setup boto3 client mock
        ses_client_mock = MagicMock()
        mock_boto3.return_value = ses_client_mock
        # Setup access denied error - using botocore.exceptions.ClientError, not boto3.exceptions.ClientError
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Insufficient permissions'}}
        ses_client_mock.send_email.side_effect = ClientError(error_response, 'send_email')
        
        result = test_ses_setup()
        
        assert result is False
        ses_client_mock.send_email.assert_called_once()

    @pytest.mark.skipif(SKIP_AWS_TESTS, reason="AWS credentials not available in local environment")
    @patch('boto3.client')
    @patch('os.getenv', side_effect=lambda x, default=None: default)  # Return default values
    def test_ses_setup_no_env_vars(self, mock_getenv, mock_boto3):
        """Test SES setup with no environment variables"""
        # Setup boto3 client mock
        ses_client_mock = MagicMock()
        mock_boto3.return_value = ses_client_mock
        # Setup successful response
        ses_client_mock.send_email.return_value = {'MessageId': 'test-message-id'}
        
        result = test_ses_setup()
        
        assert result is True  # Should still work with default values
        # Check default region and sender email were used
        mock_boto3.assert_called_with('ses', region_name='us-west-1')
        args, kwargs = ses_client_mock.send_email.call_args
        assert kwargs['Source'] == 'noreply@gator.market'

#################################################
# 9. Database Connection Tests (app.py)
#################################################

class TestDatabaseConnection:
    """
    Test database connection functionality
    
    Expected Results:
    [VARY] test_get_db_connection_success: Will vary - Needs DB_TESTING_ENABLED=true
    [VARY] test_get_db_connection_invalid_credentials: Will vary - Needs DB_TESTING_ENABLED=true
    [VARY] test_get_db_connection_server_down: Will vary - Needs DB_TESTING_ENABLED=true
    [VARY] test_get_db_connection_missing_env_vars: Will vary - Needs DB_TESTING_ENABLED=true
    """
    @pytest.mark.skipif(SKIP_DB_TESTS, reason="Database connection testing disabled in local environment")
    @patch('mysql.connector.connect')
    @patch('os.getenv', return_value='test-value')  # Mock all env vars
    def test_get_db_connection_success(self, mock_getenv, mock_connect):
        """Test successful database connection"""
        # Setup successful connection
        mock_connect.return_value = MagicMock()
        
        conn = get_db_connection()
        
        assert conn is not None
        mock_connect.assert_called_once()
        # Verify connection parameters
        _, kwargs = mock_connect.call_args
        assert kwargs['host'] == 'test-value'
        assert kwargs['user'] == 'test-value'
        assert kwargs['password'] == 'test-value'
        assert kwargs['database'] == 'test-value'

    @pytest.mark.skipif(SKIP_DB_TESTS, reason="Database connection testing disabled in local environment")
    @patch('mysql.connector.connect')
    @patch('os.getenv', return_value='test-value')
    def test_get_db_connection_invalid_credentials(self, mock_getenv, mock_connect):
        """Test database connection with invalid credentials"""
        # Setup authentication error
        mock_connect.side_effect = mysql.connector.Error("Access denied for user")
        
        conn = get_db_connection()
        
        assert conn is None
        mock_connect.assert_called_once()

    @pytest.mark.skipif(SKIP_DB_TESTS, reason="Database connection testing disabled in local environment")
    @patch('mysql.connector.connect')
    @patch('os.getenv', return_value='test-value')
    def test_get_db_connection_server_down(self, mock_getenv, mock_connect):
        """Test database connection with server down"""
        # Setup connection error
        mock_connect.side_effect = mysql.connector.Error("Can't connect to MySQL server")
        
        conn = get_db_connection()
        
        assert conn is None
        mock_connect.assert_called_once()

    @pytest.mark.skipif(SKIP_DB_TESTS, reason="Database connection testing disabled in local environment")
    @patch('mysql.connector.connect')
    @patch('os.getenv', side_effect=lambda x, default=None: None)  # Simulate missing env vars
    def test_get_db_connection_missing_env_vars(self, mock_getenv, mock_connect):
        """Test database connection with missing environment variables"""
        # Setup connection mock
        mock_connect.return_value = MagicMock()
        
        conn = get_db_connection()
        
        assert conn is not None  # Should try to connect with None values
        mock_connect.assert_called_once()
        # Verify connection parameters
        _, kwargs = mock_connect.call_args
        assert kwargs['host'] is None
        assert kwargs['user'] is None
        assert kwargs['password'] is None
        assert kwargs['database'] is None

#################################################
# 10. Admin Functions Tests (auth.py)
#################################################

class TestAdminFunctions:
    """
    Test admin functionality
    
    Expected Results:
    [PASS] test_get_all_users_success: Should pass - Uses mocked admin auth
    [PASS] test_update_user_role_success: Should pass - Uses mocked admin auth
    [PASS] test_update_user_role_invalid_role: Should pass - Uses mocked admin auth
    [PASS] test_update_user_status_success: Should pass - Uses mocked admin auth
    [PASS] test_update_user_status_invalid_status: Should pass - Uses mocked admin auth
    """
    @patch('auth.admin_required', side_effect=mock_admin_auth)
    def test_get_all_users_success(self, mock_admin, client, mock_db):
        """Test admin successfully retrieving all users"""
        cursor_mock, conn_mock = mock_db
        # Setup users data
        cursor_mock.fetchall.return_value = [
            {
                'user_id': 1,
                'username': 'admin',
                'email': 'admin@sfsu.edu',
                'first_name': 'Admin',
                'last_name': 'User',
                'verification_status': 'verified',
                'date_joined': datetime.now(),
                'last_login': datetime.now(),
                'user_role': 'admin',
                'account_status': 'active'
            },
            {
                'user_id': 2,
                'username': 'regular',
                'email': 'user@sfsu.edu',
                'first_name': 'Regular',
                'last_name': 'User',
                'verification_status': 'verified',
                'date_joined': datetime.now(),
                'last_login': None,
                'user_role': 'user',
                'account_status': 'active'
            }
        ]
        
        response = client.get('/auth/users')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['username'] == 'admin'
        assert data[1]['user_role'] == 'user'

    @patch('auth.admin_required', side_effect=mock_admin_auth)
    def test_update_user_role_success(self, mock_admin, client, mock_db):
        """Test admin successfully updating user role"""
        cursor_mock, conn_mock = mock_db
        
        response = client.put('/auth/users/2/role', json={
            'role': 'moderator'
        })
        
        assert response.status_code == 200
        assert b'User role updated successfully' in response.data
        conn_mock.commit.assert_called_once()
        # Check for admin action logging
        assert any('INSERT INTO admin_actions' in str(call) for call in cursor_mock.execute.call_args_list)

    @patch('auth.admin_required', side_effect=mock_admin_auth)
    def test_update_user_role_invalid_role(self, mock_admin, client):
        """Test admin updating user with invalid role"""
        response = client.put('/auth/users/2/role', json={
            'role': 'invalid_role'  # Not a valid role
        })
        
        assert response.status_code == 400
        assert b'Invalid role value' in response.data

    @patch('auth.admin_required', side_effect=mock_admin_auth)
    def test_update_user_status_success(self, mock_admin, client, mock_db):
        """Test admin successfully updating user status"""
        cursor_mock, conn_mock = mock_db
        
        response = client.put('/auth/users/2/status', json={
            'status': 'inactive/banned'
        })
        
        assert response.status_code == 200
        assert b'User status updated successfully' in response.data
        conn_mock.commit.assert_called_once()
        # Check for admin action logging
        assert any('INSERT INTO admin_actions' in str(call) for call in cursor_mock.execute.call_args_list)

    @patch('auth.admin_required', side_effect=mock_admin_auth)
    def test_update_user_status_invalid_status(self, mock_admin, client):
        """Test admin updating user with invalid status"""
        response = client.put('/auth/users/2/status', json={
            'status': 'invalid_status'  # Not a valid status
        })
        
        assert response.status_code == 400
        assert b'Invalid status value' in response.data