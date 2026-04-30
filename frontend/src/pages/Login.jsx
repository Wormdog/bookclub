import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
export default function Login() {
  const [mode,       setMode]       = useState("login");
  const [email,      setEmail]      = useState("");
  const [username,   setUsername]   = useState("");
  const [password,   setPassword]   = useState("");
  const [confirm,    setConfirm]    = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error,      setError]      = useState("");
  const [success,    setSuccess]    = useState("");
  const navigate = useNavigate();
  const reset = () => {
    setEmail(""); setUsername(""); setPassword("");
    setConfirm(""); setInviteCode(""); setError(""); 
    // setSuccess("");
  };
  const handleSubmit = async (e) => {
    e.preventDefault(); setError(""); setSuccess("");
    if (mode === "register") {
      if (password !== confirm) { setError("Passwords do not match."); return; }
      if (password.length < 8)  { setError("Password must be at least 8 characters."); return; }
      try {
        await axios.post("/api/auth/register", {
          email, username, password, invite_code: inviteCode,
        });
        setMode("login"); 
        setSuccess("Account created! Please check your email and click the confirmation link before logging in.");
        reset();
      } catch (err) {
        setError(err.response?.data?.detail || "Registration failed.");
      }
    } else {
      try {
        const form = new URLSearchParams();
        form.append("username", username);
        form.append("password", password);
        const res = await axios.post("/api/auth/token", form);
        localStorage.setItem("token", res.data.access_token);
        navigate("/nominate");
      } catch (err) {
        setError(err.response?.data?.detail || "Invalid username or password.");
      }
    }
  };
  const toggleMode = () => { setMode(m => m === "login" ? "register" : "login"); reset(); };
  return (
    <div style={{ maxWidth:420, margin:"80px auto", fontFamily:"sans-serif", padding:"0 16px" }}>
      <h2>Bridgeport Book Club</h2>
      <h3 style={{ color:"#1E3A5F", marginBottom:20 }}>
        {mode === "login" ? "Sign In" : "Create Account"}
      </h3>
      <form onSubmit={handleSubmit} style={{ display:"flex", flexDirection:"column", gap:12 }}>
        {mode === "register" && (
          <input placeholder="Email Address" type="email" value={email}
            onChange={e => setEmail(e.target.value)} required style={inputStyle} />
        )}
        <input placeholder="Username" value={username}
          onChange={e => setUsername(e.target.value)} required style={inputStyle} />
        <input placeholder="Password" type="password" value={password}
          onChange={e => setPassword(e.target.value)} required style={inputStyle} />
        {mode === "register" && (
          <>
            <input placeholder="Confirm Password" type="password" value={confirm}
              onChange={e => setConfirm(e.target.value)} required style={inputStyle} />
            <input placeholder="Invite Code" value={inviteCode}
              onChange={e => setInviteCode(e.target.value)} required style={inputStyle} />
          </>
        )}
        {error   && <p style={{ color:"red",   margin:0 }}>{error}</p>}
        {success && <p style={{ color:"green", margin:0, lineHeight:1.5 }}>{success}</p>}
        <button type="submit" style={btnStyle("#1E3A5F")}>
          {mode === "login" ? "Log In" : "Create Account"}
        </button>
      </form>
      <p style={{ marginTop:20, textAlign:"center", color:"#555" }}>
        {mode === "login" ? "New here? " : "Already have an account? "}
        <span onClick={toggleMode}
          style={{ color:"#1E3A5F", cursor:"pointer", fontWeight:"bold", textDecoration:"underline" }}>
          {mode === "login" ? "Create an account" : "Sign in"}
        </span>
      </p>
    </div>
  );
}
const inputStyle = { padding:10, fontSize:15, border:"1px solid #ccc", borderRadius:6 };
const btnStyle = (bg) => ({
  padding:12, fontSize:15, background:bg, color:"#fff",
  border:"none", borderRadius:6, cursor:"pointer", fontWeight:"bold"
});
