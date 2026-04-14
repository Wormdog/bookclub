import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
const api = () => axios.create({
  headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
});
export default function Results() {
  const [round,   setRound]   = useState(null);
  const [status,  setStatus]  = useState(null);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    api().get("/api/rounds/current-public")
      .then(res => setStatus(res.data))
      .catch(() => {});
    api().get("/api/admin/rounds/latest-finished")
      .then(res => setRound(res.data))
      .catch(() => setMessage("No results available yet."));
  }, []);
  return (
    <div style={{ maxWidth:600, margin:"40px auto", fontFamily:"sans-serif", padding:"0 16px" }}>
      <h2>Book Club Results</h2>
      <div style={{ display:"flex", gap:12, marginBottom:20 }}>
        <button onClick={() => navigate("/nominate")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Nominate</button>
        <button onClick={() => navigate("/vote")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Vote</button>
      </div>
      {status?.status === "tiebreak" && (
        <div style={{ background:"#fff3cd", border:"1px solid #ffc107",
                      borderRadius:8, padding:16, marginBottom:20 }}>
          <strong>Tiebreak in progress!</strong>
          <p style={{ margin:"8px 0 0" }}>
            A tiebreak vote is open.
            {status.tiebreak_closes_at && (
              <> Closes: <strong>{new Date(status.tiebreak_closes_at).toLocaleString()}</strong></>
            )}
          </p>
          <button onClick={() => navigate("/vote")}
            style={{ marginTop:10, padding:"8px 16px", background:"#1E3A5F",
                     color:"#fff", border:"none", borderRadius:6, cursor:"pointer" }}>
            Go Vote Now
          </button>
        </div>
      )}
      {message && <p style={{ color:"#888" }}>{message}</p>}
      {round && (
        <div style={{ border:"1px solid #ddd", borderRadius:12, padding:24 }}>
          <p style={{ color:"#888", margin:"0 0 16px", fontSize:13 }}>Most Recent Result</p>
          <div style={{ display:"flex", gap:20, alignItems:"flex-start" }}>
            {round.winner_cover_url && (
              <img src={round.winner_cover_url} alt="cover"
                   style={{ width:80, borderRadius:4, flexShrink:0 }} />
            )}
            <div>
              <h3 style={{ margin:"0 0 4px", color:"#1E3A5F" }}>{round.winner_title}</h3>
              <p style={{ margin:"0 0 16px", color:"#555" }}>by {round.winner_author}</p>
              {round.meeting_date && (
                <p style={{ margin:"0 0 6px" }}>
                  <strong>Next Meeting:</strong> {round.meeting_date}
                </p>
              )}
              {round.meeting_location && (
                <p style={{ margin:0 }}>
                  <strong>Location:</strong> {round.meeting_location}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
