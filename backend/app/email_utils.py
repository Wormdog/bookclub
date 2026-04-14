import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
from .config import settings
 
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
 
def generate_verify_token(email: str) -> str:
    return _serializer.dumps(email, salt="email-verify")
 
def confirm_verify_token(token: str, max_age: int = 86400):
    return _serializer.loads(token, salt="email-verify", max_age=max_age)
 
def _send(to_emails: list, subject: str, text_body: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.MAIL_FROM
    msg["To"]      = ", ".join(to_emails)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_USER, to_emails, msg.as_string())
 
def send_verification_email(to_email: str, token: str) -> None:
    verify_url = f"{settings.APP_BASE_URL}/api/auth/verify?token={token}"
    text = (f"Welcome to Book Club!\n\nConfirm your email:\n{verify_url}\n\n"
            "This link expires in 24 hours.")
    html = (f"<html><body style='font-family:sans-serif;max-width:480px;margin:40px auto'>"
            f"<h2>Welcome to Book Club!</h2>"
            f"<p><a href='{verify_url}' style='padding:12px 24px;background:#1E3A5F;"
            f"color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;"
            f"display:inline-block'>Confirm Email Address</a></p>"
            f"<p style='color:#888;font-size:13px'>Link expires in 24 hours.</p>"
            f"</body></html>")
    _send([to_email], "Confirm your Book Club account", text, html)
 
def send_results_email(to_emails: list, winner_title: str, winner_author: str,
                       winner_cover_url: str, meeting_date: str,
                       meeting_location: str) -> None:
    subject = f"Next Book Club Pick: {winner_title}!"
    text = (f"The votes are in!\n\nOur next book: {winner_title} by {winner_author}\n\n"
            f"Next meeting: {meeting_date}\nLocation: {meeting_location}\n\nSee you there!")
    cover = (f"<img src='{winner_cover_url}' style='width:80px;margin-bottom:12px'><br>"
             if winner_cover_url else "")
    html = (f"<html><body style='font-family:sans-serif;max-width:480px;margin:40px auto'>"
            f"<h2>The votes are in!</h2>{cover}"
            f"<h3>Our next book is:</h3>"
            f"<p style='font-size:20px;font-weight:bold'>{winner_title}</p>"
            f"<p style='color:#555'>by {winner_author}</p><hr style='margin:20px 0'>"
            f"<p><strong>Next Meeting:</strong> {meeting_date}</p>"
            f"<p><strong>Location:</strong> {meeting_location}</p>"
            f"<a href='{settings.APP_BASE_URL}' style='display:inline-block;margin-top:16px;"
            f"padding:12px 24px;background:#1E3A5F;color:#fff;text-decoration:none;"
            f"border-radius:6px;font-weight:bold'>View on Book Club Site</a>"
            f"</body></html>")
    _send(to_emails, subject, text, html)
 
def send_tiebreak_email(to_emails: list, tied_books: list,
                        tiebreak_closes_at: str) -> None:
    book_list_text = "\n".join([f"  - {b['title']} by {b['author']}" for b in tied_books])
    book_list_html = "".join([f"<li><strong>{b['title']}</strong> by {b['author']}</li>"
                              for b in tied_books])
    subject = "It's a tie! Your tiebreak vote is needed"
    text = (f"We have a tie!\n\nTied books:\n{book_list_text}\n\n"
            f"Vote before: {tiebreak_closes_at}\nVisit: {settings.APP_BASE_URL}")
    html = (f"<html><body style='font-family:sans-serif;max-width:480px;margin:40px auto'>"
            f"<h2>It's a tie!</h2><p>The following books are tied:</p>"
            f"<ul>{book_list_html}</ul>"
            f"<p>Vote before: <strong>{tiebreak_closes_at}</strong></p>"
            f"<a href='{settings.APP_BASE_URL}' style='display:inline-block;padding:12px 24px;"
            f"background:#1E3A5F;color:#fff;text-decoration:none;border-radius:6px;"
            f"font-weight:bold'>Cast Your Tiebreak Vote</a>"
            f"<p style='color:#888;font-size:13px;margin-top:16px'>"
            f"Note: Nominators of tied books are not eligible to vote.</p>"
            f"</body></html>")
    _send(to_emails, subject, text, html)
 
def send_tiebreak_ineligible_email(to_emails: list, tied_books: list) -> None:
    book_list_html = "".join([f"<li><strong>{b['title']}</strong></li>"
                              for b in tied_books])
    subject = "Tiebreak in progress — you are not eligible to vote"
    text = ("There is a tiebreak in progress. Because you nominated one of the tied books "
            "you are not eligible to vote. We will notify you of the result!")
    html = (f"<html><body style='font-family:sans-serif;max-width:480px;margin:40px auto'>"
            f"<h2>Tiebreak in progress</h2><p>Tied books:</p><ul>{book_list_html}</ul>"
            f"<p>Because you nominated one of the tied books you are not eligible to vote "
            f"in the tiebreak — but we will email you the result!</p></body></html>")
    _send(to_emails, subject, text, html)
