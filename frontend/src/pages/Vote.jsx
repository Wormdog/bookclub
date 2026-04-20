import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
const api = () => axios.create({
  headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
});
export default function Vote() {
  const [nominations,  setNominations]  = useState([]);
  const [message,      setMessage]      = useState("");
  const [roundStatus,  setRoundStatus]  = useState(null);
  const navigate = useNavigate();
  useEffect(() => {
    api().get("/api/rounds/current-public")
      .then(res => setRoundStatus(res.data))
      .catch(() => {});
    api().get("/api/nominations")
      .then(res => setNominations(res.data))
      .catch(err => setMessage(err.response?.data?.detail || "Failed to load nominations."));
  }, []);
  const vote = async (nomination_id) => {
    try {
      await api().post("/api/votes", { nomination_id });
      setMessage("Your vote has been recorded!");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Error submitting vote.");
    }
  };
  return (
    <div style={{ maxWidth:700, margin:"40px auto", fontFamily:"sans-serif" }}>
      <h2>Vote for Next Book</h2>
      <div style={{ display:"flex", gap:12, marginBottom:16 }}>
        <button onClick={() => navigate("/nominate")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Nominate</button>
        <button onClick={() => navigate("/results")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Results</button>
      </div>
      {roundStatus?.status === "tiebreak" && (
        <div style={{ background:"#fff3cd", border:"1px solid #ffc107",
                      borderRadius:8, padding:12, marginBottom:16 }}>
          <strong>Tiebreak round!</strong> Only tied books shown below.
          {roundStatus.tiebreak_closes_at && (
            <> Closes: <strong>{new Date(roundStatus.tiebreak_closes_at).toLocaleString()}</strong></>
          )}
        </div>
      )}
      {message && <p style={{ color:"red" }}>{message}</p>}
      {nominations.length === 0 ? (
        <p>No nominations for this round yet.</p>
      ) : (
        <>
          <p style={{ marginBottom: 8, color: "#333", fontSize: 16, fontWeight: 500 }}>
            Cast your vote below for your favorite book!
          </p>
          
          <p style={{ marginBottom: 12, color: "#555", fontSize: 14 }}>
            Tip: Click a book's title to view more details.
          </p>

          {nominations.map((nom) => (
            <div
              key={nom.id}
              style={{
                display: "flex",
                gap: 12,
                alignItems: "center",
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: 10,
                marginBottom: 12
              }}
            >
              {nom.cover_url && (
                <img
                  src={nom.cover_url}
                  alt="cover"
                  style={{ width: 50, height: 70, objectFit: "cover" }}
                />
              )}

              <div style={{ flex: 1 }}>
                <a
                  href={`https://openlibrary.org/works/${nom.ol_work_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#1565c0", textDecoration: "none" }}
                  onMouseOver={(e) => (e.target.style.textDecoration = "underline")}
                  onMouseOut={(e) => (e.target.style.textDecoration = "none")}
                >
                  <strong>{nom.title}</strong>
                </a>
                <br />
                <span style={{ color: "#555" }}>{nom.author}</span>
                <br />
                <span style={{ color: "#888", fontSize: 13 }}>
                  {nom.vote_count} vote{nom.vote_count !== 1 ? "s" : ""}
                </span>
              </div>

              <button
                onClick={() => vote(nom.id)}
                style={{
                  padding: "6px 14px",
                  background: "#1565c0",
                  color: "#fff",
                  border: "none",
                  borderRadius: 6,
                  cursor: "pointer"
                }}
              >
                Vote
              </button>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
