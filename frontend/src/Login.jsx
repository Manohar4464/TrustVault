
import { useState } from "react";
import {
  ShieldCheck,
  LockKeyhole,
  Mail,
  User,
  Eye,
  EyeOff,
} from "lucide-react";
import { loginUser, registerUser } from "./services/api";

function Login({ onLogin }) {
  const [isSignup, setIsSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const switchMode = () => {
    setIsSignup(!isSignup);
    setName("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (isSignup && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 12) {
      setError("Password must contain at least 12 characters.");
      return;
    }

    setLoading(true);

    try {
      if (isSignup) {
        await registerUser(name, email, password);

        setSuccess("Account created successfully! Please sign in.");
        setIsSignup(false);
        setName("");
        setPassword("");
        setConfirmPassword("");
      } else {
        const data = await loginUser(email, password);
        onLogin(data.user);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          (isSignup
            ? "Unable to create account. Please try again."
            : "Unable to login. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand-icon">
          <ShieldCheck size={34} />
        </div>

        <h1>TrustVault</h1>
        <p className="login-subtitle">Secure Document Management</p>

        <h2>{isSignup ? "Create Account" : "Welcome Back"}</h2>

        <p className="login-description">
          {isSignup
            ? "Create your secure TrustVault account."
            : "Sign in to access your secure workspace."}
        </p>

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <>
              <label>Full Name</label>
              <div className="login-input">
                <User size={18} />
                <input
                  type="text"
                  placeholder="Enter your full name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={100}
                  required
                />
              </div>
            </>
          )}

          <label>Email Address</label>
          <div className="login-input">
            <Mail size={18} />
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <label>Password</label>
          <div className="login-input">
            <LockKeyhole size={18} />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={12}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {isSignup && (
  <p className="password-hint">
    Password must contain:
    <br />
    • At least 12 characters
    <br />
    • At least one letter
    <br />
    • At least one number
    <br />
    • At least one special character (!@#$%)
  </p>
)}

          {isSignup && (
            <>
              <label>Confirm Password</label>
              <div className="login-input">
                <LockKeyhole size={18} />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            </>
          )}

          {error && <div className="login-error">{error}</div>}

          {success && (
            <div className="login-success">{success}</div>
          )}

          <button className="login-button" disabled={loading}>
            {loading
              ? isSignup
                ? "Creating account..."
                : "Signing in..."
              : isSignup
                ? "Create Account"
                : "Sign In"}
          </button>
        </form>

        <p className="auth-switch">
          {isSignup
            ? "Already have an account?"
            : "Don't have an account?"}{" "}
          <button type="button" onClick={switchMode}>
            {isSignup ? "Sign In" : "Sign Up"}
          </button>
        </p>

        <div className="login-security">
          <LockKeyhole size={15} />
          Protected with secure authentication
        </div>

        <p className="login-footer">
          © 2026 TrustVault. Secure your digital world.
        </p>
      </div>
    </div>
  );
}

export default Login;
