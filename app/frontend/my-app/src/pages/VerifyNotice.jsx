import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { toast } from "react-hot-toast";
import { sendVerificationEmail } from "../services/verifyApi";
import { motion } from "framer-motion";

const VerifyNotice = () => {
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const navigate = useNavigate();
  
  useEffect(() => {
    // Get email from sessionStorage
    const pendingEmail = sessionStorage.getItem("pendingVerificationEmail");
    if (pendingEmail) {
      setEmail(pendingEmail);
    } else {
      // If no pending email, redirect to login
      navigate("/login");
    }
  }, [navigate]);
  
  // Handle countdown for resend button
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);
  
  const handleResendEmail = async () => {
    if (!email) {
      toast.error("No email address found");
      return;
    }
    
    if (countdown > 0) {
      toast.error(`Please wait ${countdown} seconds before requesting another email`);
      return;
    }
    
    setResending(true);
    try {
      await sendVerificationEmail(email);
      toast.success("Verification email resent. Please check your inbox.");
      // Set 90-second cooldown for resending
      setCountdown(90);
    } catch (err) {
      const errorMessage = err.response?.data?.error || "Failed to resend verification email";
      toast.error(errorMessage);
    } finally {
      setResending(false);
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col justify-between bg-gray-100">
      <Navbar />
      <main className="flex-grow flex items-center justify-center p-8">
        <motion.div 
          className="bg-white rounded-2xl border-2 border-[#2E0854] shadow-lg p-8 w-full max-w-md"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-2xl font-bold text-[#2E0854] mb-6 text-center">
            Verify Your Email
          </h2>
          
          <div className="mb-6 text-center">
            <svg className="w-16 h-16 mx-auto text-[#FFCC00]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          
          <p className="text-gray-700 mb-3 text-center">
            We've sent a verification email to:
          </p>
          <p className="text-[#2E0854] font-bold mb-5 text-center break-all">
            {email || "your SFSU email address"}
          </p>
          
          <p className="text-gray-600 mb-6 text-center">
            Please check your email inbox and click the verification link to activate your account.
            <br />
            <span className="text-sm mt-2 block">
              The verification link will expire in 24 hours.
            </span>
          </p>
          
          <div className="flex flex-col gap-4">
            <button
              onClick={handleResendEmail}
              className={`${
                countdown > 0 
                  ? "bg-gray-300 cursor-not-allowed" 
                  : "bg-[#FFCC00] hover:bg-yellow-300"
              } text-[#2E0854] py-3 rounded-full font-semibold transition flex items-center justify-center`}
              disabled={resending || countdown > 0}
            >
              {resending 
                ? "Sending..." 
                : countdown > 0 
                  ? `Resend Available in ${countdown}s` 
                  : "Resend Verification Email"}
            </button>
            
            <Link to="/login" className="text-center text-[#2E0854] font-medium hover:underline">
              Return to Login
            </Link>
          </div>
        </motion.div>
      </main>
      <Footer />
    </div>
  );
};

export default VerifyNotice;