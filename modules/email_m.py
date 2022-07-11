import smtplib, ssl, json

with open("config/core.json", "r") as f:
    core = json.loads(f.read())

def send_email(from_, to, password, subject, content, smtp_server, smtp_port, debug = None):
    if isinstance(smtp_port, str):
        smtp_port = int(smtp_port)

    ssl_context = ssl.create_default_context()
    service = smtplib.SMTP_SSL(smtp_server, smtp_port, context = ssl_context)
    service.login(from_, password)

    if debug != None:
        content += "\n\nDebug info:\n"
        for i in debug.keys():
            content += f"{i}: {debug[i]}\n"

    service.sendmail(from_, to, f"{content}")

    service.quit()

def send_error_email(content, debug = None):
    if not core["email_when_error"]:
        return

    send_email(core["email_from"], core["email_to"], core["email_smtp_password"], "Mouser Bot Error!", content, core["email_smtp_server"], core["email_smtp_port"], debug)
