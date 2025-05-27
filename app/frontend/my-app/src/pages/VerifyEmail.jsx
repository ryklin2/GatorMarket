import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import config from "../config";
import { toast } from "react-hot-toast";

const VerifyEmail = () => {
  const [params] = useSearchParams();
  const token = params.get("token");
  const navigate = useNavigate();
  const [verificationStatus, setVerificationStatus] = useState({
    loading: true,
    success: false,
    error: null
  });

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setVerificationStatus({
          loading: false,
          success: false,
          error: "No verification token found in URL"
        });
        return;
      }

      try {
        // Attempt to verify with proper error handling
        const response = await axios.get(`${config.apiUrl}/verify/confirm`, {
          params: { token }
        });
        
        // Only mark as success if the API call was successful
        setVerificationStatus({
          loading: false,
          success: true,
          error: null
        });
        
        // Clean up any pending verification data
        sessionStorage.removeItem("pendingVerificationEmail");
        
        // Show success message and redirect
        toast.success("Email verified successfully!");
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } catch (err) {
        // Handle verification errors properly
        console.error("Verification error:", err);
        const errorMessage = err.response?.data?.error || "Verification failed. Please try again.";
        
        setVerificationStatus({
          loading: false,
          success: false,
          error: errorMessage
        });
        
        toast.error(errorMessage);
        
        // Redirect after showing the error
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    };

    verify();
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Navbar />
      <main className="flex-grow flex items-center justify-center text-center p-8">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          {verificationStatus.loading ? (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 border-t-4 border-[#FFCC00] border-solid rounded-full animate-spin mb-4"></div>
              <h1 className="text-gray-700 text-2xl font-bold mb-2">Verifying Email</h1>
              <p className="text-gray-600">Please wait while we verify your email...</p>
            </div>
          ) : verificationStatus.success ? (
            <div>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-green-600 text-3xl">✅</span>
              </div>
              <h1 className="text-green-600 text-2xl font-bold mb-2">Email Verified</h1>
              <p className="text-gray-600 mb-4">Your email has been successfully verified!</p>
              <p className="text-gray-500">Redirecting you to login page...</p>
            </div>
          ) : (
            <div>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-3xl">❌</span>
              </div>
              <h1 className="text-red-600 text-2xl font-bold mb-2">Verification Failed</h1>
              <p className="text-gray-600 mb-4">{verificationStatus.error}</p>
              <p className="text-gray-500">Redirecting you to login page...</p>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default VerifyEmail;
