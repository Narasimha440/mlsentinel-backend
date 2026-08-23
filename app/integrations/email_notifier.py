import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

SEVERITY_LABELS = {
    "critical": "Critical",
    "warning": "Warning",
    "info": "Info",
}

NOTIFIABLE_SEVERITIES = {"critical", "warning"}

def send_alert_email(to_email: str, model_name: str, project_name: str, severity: str, message: str):
    if severity not in NOTIFIABLE_SEVERITIES:
        return

    if not resend.api_key:
        print("RESEND_API_KEY is not set broooo!!!")
        return

    label = SEVERITY_LABELS.get(severity, severity.title())

    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto;">
      <p style="color: #2563EB; font-size: 13px; font-weight: 500; margin-bottom: 4px;">MLSentinel Alert</p>
      <h2 style="color: #111827; font-size: 20px; margin: 0 0 16px 0;">{label} on {model_name}</h2>
      <p style="color: #6B7280; font-size: 14px; margin: 0 0 4px 0;">{project_name} / {model_name}</p>
      <p style="color: #111827; font-size: 15px; line-height: 1.5; margin: 16px 0;">{message}</p>
      <a href="https://www.mlsentinel.dev/dashboard/alerts"
         style="display: inline-block; background: #111827; color: white; padding: 10px 20px;
                border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 500; margin-top: 8px;">
        View in dashboard
      </a>
    </div>
    """


    try:
        resend.Emails.send({
            "from": "MLSentinel Alerts <alerts@mlsentinel.dev>",
            "to": to_email,
            "subject": f"{label} {model_name}",
            "html": html,
        })
    except Exception as e:
        print(f"Failed to send alert email: {e}")