import email
from email.utils import parseaddr, parsedate_to_datetime
from hashlib import sha256
from sqlite3 import connect
from email.header import decode_header, make_header


def parse_email(raw_email_bytes):
    con = connect("attachments.db")
    cur = con.cursor()
    msg = email.message_from_bytes(raw_email_bytes)

    def decode_header_value(value):
        if not value:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except Exception:
            return value

    message_id = msg.get("Message-ID", "")
    if message_id.startswith("<") and message_id.endswith(">"):
        message_id = message_id[1:-1]

    from_name, from_addr = parseaddr(msg.get("From", ""))
    to_name, to_addr = parseaddr(msg.get("To", ""))
    subject = decode_header_value(msg.get("Subject", ""))
    date = msg.get("Date", "")
    try:
        date = parsedate_to_datetime(date).strftime("%d/%m/%y, %H:%M")
    except Exception:
        date = ""

    html_body = ""
    plain_body = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            content_id = part.get("Content-ID", "")
            if content_id.startswith("<") and content_id.endswith(">"):
                content_id = content_id[1:-1]

            if "attachment" in content_disposition or content_id:
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                else:
                    filename = content_id or ""

                data = part.get_payload(decode=True)
                file_hash = sha256(data).hexdigest()
                res = cur.execute(f"select id from attachments where hash = '{file_hash}'").fetchone()
                if res:
                    file_id = res[0]
                else:
                    cur.execute(f"insert into attachments(data, hash, content_type) values(?, ?, ?)", (data, file_hash, content_type))
                    con.commit()
                    file_id = cur.execute(f"select id from attachments where hash = '{file_hash}'").fetchone()[0]
                attachments.append({
                    "filename": filename,
                    "file_id": file_id
                })
                continue

            if content_type == "text/html":
                html_body = part.get_payload(decode=True).decode(part.get_content_charset("utf-8"), errors="ignore")
            elif content_type == "text/plain" and not html_body:
                plain_body = part.get_payload(decode=True).decode(part.get_content_charset("utf-8"), errors="ignore")
    else:
        content_type = msg.get_content_type()
        if content_type == "text/html":
            html_body = msg.get_payload(decode=True).decode(msg.get_content_charset("utf-8"), errors="ignore")
        elif content_type == "text/plain":
            plain_body = msg.get_payload(decode=True).decode(msg.get_content_charset("utf-8"), errors="ignore")
    
    return {
        "message_id": message_id,
        "from": from_addr,
        "name": decode_header_value(from_name),
        "to": to_addr,
        "subject": subject,
        "date": date,
        "body": html_body or plain_body,
        "attachments": attachments,
    }
