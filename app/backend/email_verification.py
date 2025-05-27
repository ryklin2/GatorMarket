from flask import Blueprint, request, jsonify, current_app
from app import get_db_connection
import uuid
import boto3
from botocore.exceptions import ClientError
import os
import logging
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from auth import generate_token

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email_bp = Blueprint('email_verification', __name__, url_prefix='/verify')

# Initialize AWS SES client
aws_region = os.getenv("AWS_REGION", "us-west-1") 
ses_client = boto3.client('ses', region_name=aws_region)

def cleanup_expired_tokens():
    """Clean up expired verification tokens and unverified accounts"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start transaction using the correct method for mysql.connector
        # Note: we're using cursor.execute() instead of conn.begin()
        cursor.execute("START TRANSACTION")
        
        # Get expired unverified accounts
        cursor.execute("""
            SELECT user_id 
            FROM users 
            WHERE verification_status = 'unverified'
            AND verification_token_created_at < NOW() - INTERVAL 24 HOUR
            FOR UPDATE
        """)
        expired_users = cursor.fetchall()

        deleted_count = 0
        for user in expired_users:
            user_id = user[0]
            
            try:
                # Clean up related records
                cursor.execute("DELETE FROM wishlist_tracking WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM messages WHERE sender_id = %s", (user_id,))
                cursor.execute("DELETE FROM conversation_participants WHERE user_id = %s", (user_id,))
                
                # Handle user_reports
                cursor.execute("DELETE FROM user_reports WHERE reporter_id = %s OR reported_user_id = %s", 
                              (user_id, user_id))
                
                # Delete reviews
                cursor.execute("DELETE FROM reviews WHERE seller_id = %s", (user_id,))
                
                # Delete product images and products
                cursor.execute("""
                    DELETE FROM product_images 
                    WHERE product_id IN (SELECT product_id FROM products WHERE user_id = %s)
                """, (user_id,))
                cursor.execute("DELETE FROM products WHERE user_id = %s", (user_id,))
                
                # Finally delete the user
                cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                
                deleted_count += 1
                logger.info(f"Deleted expired unverified account: {user_id}")
                
            except Exception as e:
                logger.error(f"Error deleting user {user_id}: {e}")
        
        # Commit the transaction
        conn.commit()
        logger.info(f"Cleanup completed. Deleted {deleted_count} expired accounts.")
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_tokens: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint to send email verification
@email_bp.route('/send', methods=['POST'])
def send_verification_email():
    """Send verification email to the user"""
    # Run cleanup as a separate operation to avoid blocking the API call
    try:
        cleanup_expired_tokens()
    except Exception as e:
        logger.error(f"Cleanup error (non-blocking): {e}")
    
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and is unverified
        cursor.execute("""
            SELECT user_id, verification_status, verification_token_created_at 
            FROM users 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user['verification_status'] == 'verified':
            return jsonify({'error': 'Email already verified'}), 400

        # Optional throttle: check if last token was sent within 5 minutes
        last_sent = user.get('verification_token_created_at')
        if last_sent:
            now = datetime.now(timezone.utc)
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
                
            if (now - last_sent).total_seconds() < 90:
                return jsonify({'error': 'Please wait a few minutes before requesting another email'}), 429

        # Generate and store new token
        token = str(uuid.uuid4())
        
        try:
            # START TRANSACTION using cursor.execute() instead of conn.begin()
            cursor.execute("START TRANSACTION")
            
            cursor.execute("""
                UPDATE users 
                SET verification_token = %s, verification_token_created_at = NOW()
                WHERE email = %s
            """, (token, email))
            
            # COMMIT the transaction directly
            conn.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500

        try:
            # Try to send email, but handle errors gracefully
            # Send email using SES
            subject = "Verify your email"
            frontend_origin = os.getenv("FRONTEND_ORIGIN", "https://csc648g1.me")
            verification_url = f"{frontend_origin}/verify-email?token={token}"
            delete_url = f"{frontend_origin}/delete-account?token={token}"
            
            # For better email formatting, use both text and HTML versions
            text_body = f"""
                Click the link to verify your email: {verification_url}

                If you did not create this account, click here to delete it: {delete_url}
                
                This link will expire in 24 hours.
                """
            html_body = f"""
            <html>
                <body>
                    <h2>Welcome to Gator Market!</h2>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{verification_url}" style="padding: 10px 20px; background-color: #FFCC00; color: #2E0854; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <hr style="margin: 20px 0; border: 1px solid #eee;">
                    <p style="color: #666;">If you didn't create an account with Gator Market, please click below to delete this account:</p>
                    <p><a href="{delete_url}" style="padding: 10px 20px; background-color: #ff4444; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">Delete Account</a></p>
                </body>
            </html>
            """
            
            success = send_email_ses(email, subject, text_body, html_body)
            
            if success:
                return jsonify({'message': 'Verification email sent'}), 200
            else:
                # Don't fail if email sending fails - just log it
                logger.warning(f"Email sending failed for {email}, but account was created")
                return jsonify({'message': 'Account created, but verification email failed. Please contact support.'}), 200
                
        except Exception as e:
            # Log the email error but don't make it a fatal error
            logger.error(f"Email error (non-fatal): {e}")
            return jsonify({'message': 'Account created, but verification email could not be sent. Please contact support.'}), 200

    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        # Return a user-friendly response that won't break the frontend
        return jsonify({'message': 'Registration processed but verification email could not be sent. Please contact support.'}), 200
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# AWS SES email sending function
def send_email_ses(to_email, subject, text_body, html_body=None):
    """
    Send email using AWS SES
    """
    try:
        sender = os.getenv("SES_FROM_EMAIL", "noreply@gator.market")
        
        # Create message container
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender
        message['To'] = to_email
        
        # Create plain text part
        text_part = MIMEText(text_body, 'plain')
        message.attach(text_part)
        
        # Create HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
        
        # Send email
        response = ses_client.send_raw_email(
            Source=sender,
            Destinations=[to_email],
            RawMessage={'Data': message.as_string()}
        )
        logger.info(f"Email sent to {to_email}. Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return False

# Other endpoint implementations (simplified versions that don't use conn.begin())
@email_bp.route('/confirm', methods=['GET'])
def confirm_verification():
    """Confirm email verification with token"""
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token is required'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Begin transaction
        cursor.execute("START TRANSACTION")
        
        # First get the user information for this token
        cursor.execute("""
            SELECT user_id, email, verification_status, verification_token_created_at 
            FROM users 
            WHERE verification_token = %s
            FOR UPDATE
        """, (token,))
        user = cursor.fetchone()
        
        if not user:
            conn.rollback()
            return jsonify({'error': 'Invalid token'}), 400
            
        # Store the email associated with this token
        token_email = user['email']
            
        # Check verification status
        if user['verification_status'] == 'verified':
            conn.rollback()
            return jsonify({'error': 'Email already verified'}), 400
            
        # Check token age
        token_time = user['verification_token_created_at']
        if token_time:
            now = datetime.now(timezone.utc)
            if token_time.tzinfo is None:
                token_time = token_time.replace(tzinfo=timezone.utc)
            
            age_seconds = (now - token_time).total_seconds()
            if age_seconds > 86400:  # 24 hours
                conn.rollback()
                return jsonify({'error': 'Token has expired'}), 400

        # Update verification status only if email matches the token's intended recipient
        cursor.execute("""
            UPDATE users 
            SET verification_status = 'verified',
                verification_token = NULL,
                verification_token_created_at = NULL
            WHERE verification_token = %s 
            AND email = %s
            AND verification_status = 'unverified'
            AND verification_token_created_at > NOW() - INTERVAL 24 HOUR
        """, (token, token_email))
        
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({'error': 'Verification failed'}), 400

        # If we get here, the update was successful
        conn.commit()
        logger.info(f"Email verification successful for {token_email}")
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error confirming verification: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@email_bp.route('/delete-account', methods=['GET'])
def delete_unverified_account():
    """Delete an unverified account using the verification token"""
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token is required'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Begin transaction with SQL command
        cursor.execute("START TRANSACTION")
        
        # Get user and token info in one query with row lock
        cursor.execute("""
            SELECT user_id, verification_status, verification_token_created_at 
            FROM users 
            WHERE verification_token = %s
            FOR UPDATE
        """, (token,))
        user = cursor.fetchone()

        if not user:
            conn.rollback()
            return jsonify({'error': 'Invalid or expired token'}), 400
            
        if user['verification_status'] == 'verified':
            conn.rollback()
            return jsonify({'error': 'Cannot delete verified accounts through this method'}), 403

        # Check token age
        token_time = user['verification_token_created_at']
        if token_time:
            now = datetime.now(timezone.utc)
            if token_time.tzinfo is None:
                token_time = token_time.replace(tzinfo=timezone.utc)
            
            age_seconds = (now - token_time).total_seconds()
            if age_seconds > 86400:  # 24 hours
                conn.rollback()
                return jsonify({'error': 'Token has expired'}), 400

        # Delete all related records in order to maintain referential integrity
        user_id = user['user_id']
        try:
            # 1. First, handle messages and conversations
            cursor.execute("""
                DELETE FROM messages 
                WHERE sender_id = %s OR 
                conversation_id IN (
                    SELECT c.conversation_id FROM conversations c
                    JOIN conversation_participants cp ON c.conversation_id = cp.conversation_id
                    WHERE cp.user_id = %s
                )
            """, (user_id, user_id))
            
            cursor.execute("DELETE FROM conversation_participants WHERE user_id = %s", (user_id,))
            
            # 2. Handle wishlist entries
            cursor.execute("DELETE FROM wishlist_tracking WHERE user_id = %s", (user_id,))
            
            # 3. Handle reports
            cursor.execute("DELETE FROM user_reports WHERE reporter_id = %s OR reported_user_id = %s", 
                          (user_id, user_id))
            
            # 4. Handle reviews
            cursor.execute("DELETE FROM reviews WHERE seller_id = %s", (user_id,))
            
            # 5. Handle products and images
            cursor.execute("""
                DELETE FROM product_images 
                WHERE product_id IN (SELECT product_id FROM products WHERE user_id = %s)
            """, (user_id,))
            
            cursor.execute("DELETE FROM products WHERE user_id = %s", (user_id,))
            
            # 6. Finally delete the user
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            
            # Commit the transaction
            conn.commit()
            logger.info(f"Unverified account {user_id} deleted successfully")
            return jsonify({'message': 'Account successfully deleted'}), 200
            
        except Exception as e:
            logger.error(f"Database error during account deletion: {e}")
            conn.rollback()
            return jsonify({'error': f"Failed to delete account: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@email_bp.route('/get-token', methods=['POST'])
def get_token_after_verification():
    """Get authentication token after email verification"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and is verified
        cursor.execute("""
            SELECT user_id, username, user_role, verification_status
            FROM users 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user['verification_status'] != 'verified':
            return jsonify({'error': 'Email not verified'}), 403
            
        # Generate token for verified user
        token = generate_token(user['user_id'], user['username'], user['user_role'])
        
        return jsonify({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'verification_status': 'verified',
                'role': user['user_role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting token after verification: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()