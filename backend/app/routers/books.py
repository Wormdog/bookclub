from fastapi import APIRouter, HTTPException
import httpx
 
router = APIRouter(prefix="/books", tags=["books"])
OL_SEARCH_URL = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "BookClubApp/1.0 (your@email.com)"}
 
@router.get("/search")
async def search_books(q: str, limit: int = 10):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            OL_SEARCH_URL,
            params={"q": q,
                    "fields": "key,title,author_name,cover_i,first_publish_year",
                    "limit": limit},
            headers=HEADERS, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(502, "Open Library unreachable")
    docs = resp.json().get("docs", [])
    return [
            {
                "ol_work_id": doc.get("key", "").replace("/works/", ""),
                "title":      doc.get("title"),
                "author":     ", ".join(doc.get("author_name", [])),
                # Use .get() here to avoid the KeyError crash
                "cover_url":  (f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg"
                            if doc.get("cover_i") else None),
                "year":       doc.get("first_publish_year")
            }
            for doc in docs
        ]
