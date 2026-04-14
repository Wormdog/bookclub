import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
const api = () => axios.create({
  headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
});
export default function Nominate() {
  const [query,       setQuery]       = useState("");
  const [results,     setResults]     = useState([]);
  const [message,     setMessage]     = useState("");
  const [roundStatus, setRoundStatus] = useState(null);
  const navigate = useNavigate();
  useEffect(() => {
    api().get("/api/rounds/current-public")
      .then(res => setRoundStatus(res.data))
      .catch(() => {});
  }, []);
  const search = async (e) => {
    e.preventDefault();
    const res = await api().get(`/api/books/search?q=${encodeURIComponent(query)}`);
    setResults(res.data);
  };
  const nominate = async (book) => {
    try {
      await api().post("/api/nominations", {
        ol_work_id: book.ol_work_id, title: book.title,
        author: book.author, cover_url: book.cover_url,
      });
      setMessage(`Nominated: "${book.title}" successfully!`);
      setResults([]);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Error submitting nomination.");
    }
  };
  return (
    <div style={{ maxWidth:700, margin:"40px auto", fontFamily:"sans-serif" }}>
      <h2>Nominate a Book</h2>
      <div style={{ display:"flex", gap:12, marginBottom:16 }}>
        <button onClick={() => navigate("/vote")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Vote Page</button>
        <button onClick={() => navigate("/results")}
          style={{ padding:"6px 14px", cursor:"pointer" }}>Results</button>
      </div>
      {roundStatus?.status === "tiebreak" && (
        <div style={{ background:"#fff3cd", border:"1px solid #ffc107",
                      borderRadius:8, padding:12, marginBottom:16 }}>
          <strong>Tiebreak in progress</strong> — nominations are closed for this round.
          <button onClick={() => navigate("/vote")}
            style={{ marginLeft:12, padding:"4px 12px", background:"#1E3A5F",
                     color:"#fff", border:"none", borderRadius:4, cursor:"pointer" }}>
            Go Vote
          </button>
        </div>
      )}
      {roundStatus?.status === "no_active_round" && (
        <div style={{ background:"#f8d7da", border:"1px solid #f5c6cb",
                      borderRadius:8, padding:12, marginBottom:16 }}>
          No voting round is currently active.
        </div>
      )}
      <form onSubmit={search} style={{ display:"flex", gap:8, marginBottom:20 }}>
        <input placeholder="Search by title or author..." value={query}
          onChange={e => setQuery(e.target.value)}
          style={{ flex:1, padding:8, fontSize:15 }} />
        <button type="submit"
          style={{ padding:"8px 16px", background:"#1E3A5F", color:"#fff",
                   border:"none", borderRadius:6, cursor:"pointer" }}>
          Search
        </button>
      </form>
      {message && <p style={{ color:"green" }}>{message}</p>}
      <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
        {results.map((book) => (
          <div key={book.ol_work_id}
            style={{ display:"flex", gap:12, alignItems:"center",
                     border:"1px solid #ddd", borderRadius:8, padding:10 }}>
            {book.cover_url && <img src={book.cover_url} alt="cover"
              style={{ width:50, height:70, objectFit:"cover" }} />}
            <div style={{ flex:1 }}>
              <strong>{book.title}</strong><br />
              <span style={{ color:"#555" }}>{book.author} {book.year ? `(${book.year})` : ""}</span>
            </div>
            <button onClick={() => nominate(book)}
              style={{ padding:"6px 14px", background:"#2e7d32", color:"#fff",
                       border:"none", borderRadius:6, cursor:"pointer" }}>
              Nominate
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}



