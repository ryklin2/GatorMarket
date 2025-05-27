import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import config from "../config";
import { toast } from "react-hot-toast";

const DeleteAccount = () => {
  const [params] = useSearchParams();
  const token = params.get("token");
  const navigate = useNavigate();
  const [deleteStatus, setDeleteStatus] = useState({
    loading: true,
    success: false,
    error: null
  });

  useEffect(() => {
    const deleteAccount = async () => {
      if (!token) {
        setDeleteStatus({
          loading: false,
          success: false,
          error: "No deletion token found in URL"
        });
        return;
      }

      try {
        // Attempt to delete with proper error handling
        const response = await axios.get(`${config.apiUrl}/verify/delete-account`, {
          params: { token }
        });
        
        // Only mark as success if the API call was successful
        setDeleteStatus({
          loading: false,
          success: true,
          error: null
        });
        
        // Clean up any pending verification data
        sessionStorage.removeItem("pendingVerificationEmail");
        
        // Show success message and redirect
        toast.success("Account successfully deleted!");
        setTimeout(() => {
          navigate('/register');
        }, 3000);
      } catch (err) {
        // Handle deletion errors properly
        console.error("Account deletion error:", err);
        const errorMessage = err.response?.data?.error || "Account deletion failed. Please try again.";
        
        setDeleteStatus({
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

    deleteAccount();
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Navbar />
      <main className="flex-grow flex items-center justify-center text-center p-8">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          {deleteStatus.loading ? (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 border-t-4 border-[#FFCC00] border-solid rounded-full animate-spin mb-4"></div>
              <h1 className="text-gray-700 text-2xl font-bold mb-2">Processing Request</h1>
              <p className="text-gray-600">Please wait while we process your account deletion request...</p>
            </div>
          ) : deleteStatus.success ? (
            <div>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-green-600 text-3xl">✅</span>
              </div>
              <h1 className="text-green-600 text-2xl font-bold mb-2">Account Deleted</h1>
              <p className="text-gray-600 mb-4">Your account has been successfully deleted.</p>
              <p className="text-gray-500">Redirecting you to registration page...</p>
            </div>
          ) : (
            <div>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-3xl">❌</span>
              </div>
              <h1 className="text-red-600 text-2xl font-bold mb-2">Deletion Failed</h1>
              <p className="text-gray-600 mb-4">{deleteStatus.error}</p>
              <p className="text-gray-500">Redirecting you to login page...</p>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default DeleteAccount;