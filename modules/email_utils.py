"""
email_utils.py — Envio de emails e gestão de subscribers.
Altere aqui: configuração SMTP, templates de boas-vindas, validação de email.
"""
import json
import re
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from modules.config import GMAIL_USER, GMAIL_PASS, SUBSCRIBERS_FILE


def email_valido(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email.strip()))


def carregar_subscribers():
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def salvar_subscribers(lista):
    try:
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False)
        return True
    except:
        return False


def enviar_email(assunto, corpo, to=None):
    if not GMAIL_USER or not GMAIL_PASS:
        return False
    destinatario = to or GMAIL_USER
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = GMAIL_USER
        msg["To"]      = destinatario
        msg.attach(MIMEText(corpo, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, destinatario, msg.as_string())
        return True
    except:
        return False
