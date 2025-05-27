import axios from 'axios';
import config from '../config';

/**
 * Send a verification email to the specified email address
 * @param {string} email - The email to send verification to
 * @returns {Promise} - Promise that resolves when email is sent
 */
export const sendVerificationEmail = async (email) => {
  try {
    // Set a timeout of 10 seconds for this request
    const response = await axios.post(
      `${config.apiUrl}/verify/send`, 
      { email },
      { timeout: 10000 } // 10 second timeout
    );
    
    return response.data;
  } catch (error) {
    console.error('Error sending verification email:', error);
    
    // Check if it's a timeout error
    if (error.code === 'ECONNABORTED') {
      throw new Error('Verification email request timed out. Please try again later.');
    }
    
    // Handle response errors
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorMessage = error.response.data?.error || 'Failed to send verification email';
      throw new Error(errorMessage);
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('No response from server. Please check your connection and try again.');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error('Error sending verification email: ' + error.message);
    }
  }
};

/**
 * Verify an email token
 * @param {string} token - The verification token
 * @returns {Promise} - Promise that resolves when token is verified
 */
export const verifyEmailToken = async (token) => {
  try {
    const response = await axios.get(`${config.apiUrl}/verify/confirm`, {
      params: { token }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error verifying email:', error);
    
    if (error.response) {
      const errorMessage = error.response.data?.error || 'Failed to verify email';
      throw new Error(errorMessage);
    } else if (error.request) {
      throw new Error('No response from server. Please check your connection and try again.');
    } else {
      throw new Error('Error verifying email: ' + error.message);
    }
  }
};

/**
 * Request token after email verification
 * @param {string} email - The verified email
 * @returns {Promise} - Promise that resolves with token data
 */
export const getTokenAfterVerification = async (email) => {
  try {
    const response = await axios.post(`${config.apiUrl}/verify/get-token`, { email });
    return response.data;
  } catch (error) {
    console.error('Error getting token:', error);
    
    if (error.response) {
      const errorMessage = error.response.data?.error || 'Failed to get authentication token';
      throw new Error(errorMessage);
    } else if (error.request) {
      throw new Error('No response from server. Please check your connection and try again.');
    } else {
      throw new Error('Error getting token: ' + error.message);
    }
  }
};

/**
 * Check verification status of a token
 * @param {string} token - The verification token to check
 * @returns {Promise} - Promise that resolves with verification status
 */
export const checkVerificationStatus = async (token) => {
  try {
    const response = await axios.post(`${config.apiUrl}/verify/get-verified-user`, { token });
    return response.data;
  } catch (error) {
    console.error('Error checking verification status:', error);
    
    if (error.response) {
      const errorMessage = error.response.data?.error || 'Failed to check verification status';
      throw new Error(errorMessage);
    } else {
      throw new Error('Error checking verification status: ' + (error.message || 'Unknown error'));
    }
  }
};

/**
 * Delete an unverified account
 * @param {string} token - The verification token
 * @returns {Promise} - Promise that resolves when account is deleted
 */
export const deleteUnverifiedAccount = async (token) => {
  try {
    const response = await axios.get(`${config.apiUrl}/verify/delete-account`, {
      params: { token }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error deleting account:', error);
    
    if (error.response) {
      const errorMessage = error.response.data?.error || 'Failed to delete account';
      throw new Error(errorMessage);
    } else {
      throw new Error('Error deleting account: ' + (error.message || 'Unknown error'));
    }
  }
};