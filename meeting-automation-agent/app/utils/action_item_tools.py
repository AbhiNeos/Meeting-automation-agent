import json
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import datetime
import os
import uuid
import base64
from requests.auth import HTTPBasicAuth
import requests
from googleapiclient.discovery import build
import google.auth

def analyze_mom_for_actions(session: dict) -> str:
    """
    Analyzes the 'Minutes of Meeting' (MoM) from the session and suggests potential actions based on keywords.

    Args:
        session: The agent's session dictionary.

    Returns:
        A string with suggested actions, or a message if no MoM is found.
    """
    if "moms" not in session or not session["moms"]:
        return "No Minutes of Meeting (MoM) found in the session to analyze."

    mom_json = session["moms"][-1]["mom"]
    action_items = mom_json.get("action_items", [])

    if not action_items:
        return "No action items found in the latest MoM."

    jira_items = []
    schedule_items = []
    for item in action_items:
        action_text = item.get("action", "").lower()
        if "jira" in action_text or "create ticket" in action_text:
            jira_items.append(item.get("action"))
        if "schedule" in action_text or "invite" in action_text or "call" in action_text:
            schedule_items.append(item.get("action"))

    suggestions = "Based on the latest MoM, I found the following potential actions:\n"
    found_actions = False

    if jira_items:
        suggestions += "\n- I can create JIRA tickets for the following items:\n"
        for item in jira_items:
            suggestions += f"  - '{item}'\n"
        found_actions = True

    if schedule_items:
        suggestions += "\n- I can schedule calls for the following items:\n"
        for item in schedule_items:
            suggestions += f"  - '{item}'\n"
        found_actions = True

    if not found_actions:
        suggestions = "I analyzed the MoM but did not find any specific action items for creating JIRA tickets or scheduling calls."

    suggestions += "\nI can also send the MoM to a Slack channel. What would you like to do?"
    return suggestions

def create_jira_ticket(session: dict) -> str:
    """
    Creates a JIRA ticket.

    Args:
        summary: The summary of the JIRA ticket.
        description: The description of the JIRA ticket.
        project: The JIRA project key.

    Returns:
        A string confirming the ticket creation or an error message.
    """
    if "moms" not in session or not session["moms"]:
        return "No Minutes of Meeting (MoM) found in the session to analyze."

    mom_json = session["moms"][-1]["mom"]
    action_items = mom_json.get("action_items", [])

    if not action_items:
        return "No action items found in the latest MoM."

    suggestions = "Based on the latest MoM, I can help with the following:\n"
    jira_items = []
    for item in action_items:
        action_text = item.get("action", "").lower()
        if re.search(r'\b(Jira|JIRA|ticket|create ticket)\b', action_text, re.IGNORECASE):
            summary = f"Meeting Action: {action_text}"
            description = f"Action from MOM:\n{action_text}\n\nOwner: {item.get('owner', 'N/A')}\nDue Date: {item.get('due_date', 'N/A')}"
            project = "KAN" # <<-- UPDATE THIS WITH YOUR KEY

            print(f"Detected Jira action. Calling create_jira_ticket for: {action_text}")
            

            JIRA_URL = os.environ.get("JIRA_URL")
            API_ENDPOINT = f"{JIRA_URL}/rest/api/3/issue"
            EMAIL = os.environ.get("JIRA_USERNAME")
            API_TOKEN = os.environ.get("JIRA_API_TOKEN")

            if not all([JIRA_URL, EMAIL, API_TOKEN]):
                return "Error: JIRA environment variables are not fully set."

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "fields": {
                    "project": {
                        "key": project
                    },
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "text": description,
                                        "type": "text"
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "id": "10001"
                    }
                }
            }

            try:
                response = requests.post(
                    API_ENDPOINT,
                    headers=headers,
                    auth=HTTPBasicAuth(EMAIL, API_TOKEN),
                    data=json.dumps(payload)
                )
                response.raise_for_status()
                
                ticket_data = response.json()
                ticket_id = ticket_data.get("key")
                ticket_url = f"{JIRA_URL}/browse/{ticket_id}"
                return f"Simulated JIRA ticket creation: Ticket ID '{ticket_id}', Ticket URL '{ticket_url}'"
            except requests.exceptions.RequestException as e:
                return f"Failed to create Jira ticket: {e}"
            except Exception as e:
                return f"An unexpected error occurred: {e}"


def schedule_call(session: dict) -> str:
    """
    Schedules a Google Meet call and sends invites to attendees.

    Args:
        attendees: A list of attendee email addresses.
        session: The agent's session dictionary.

    Returns:
        A string with the Google Meet link or an error message.
    """
    if "moms" not in session or not session["moms"]:
        return "Error: No MoM found in session to create a call from."
    mom = session["moms"][-1]["mom"]
    action_items = mom.get("action_items", [])


    for item in action_items:
        action_text = item.get("action", "").lower()
        if re.search(r'\b(schedule a call|set up a meeting|gmeet invite|calendar invite|meeting)\b', action_text, re.IGNORECASE):
            print("Scheduling conversation detected. Preparing to send iCalendar invite.")
            
            # NOTE: You will need to extract these details from the transcript
            invite_summary = "Follow-up Meeting"
            email = "abhishek.chauhan@neosalpha.com"
            start_time = datetime.datetime.now(datetime.timezone.utc)
            end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
            invite_description = "Follow-up discussion from the previous meeting's transcript."

            sender_email = os.environ.get("SENDER_EMAIL")
            sender_password = os.environ.get("SENDER_PASSWORD")
            
            if not sender_email or not sender_password:
                return "Error: Email credentials not configured in environment variables."

            try:
                # Generate iCalendar content for the invite
                ical_content = f"""BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:-//MyCompany//NONSGML Meeting Invite//EN
        CALSCALE:GREGORIAN
        METHOD:REQUEST
        BEGIN:VEVENT
        UID:{str(uuid.uuid4())}
        DTSTAMP:{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}
        DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}
        DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}
        SUMMARY:{invite_summary}
        DESCRIPTION:{invite_description}
        ORGANIZER;CN=Organizer:mailto:{sender_email}
        ATTENDEE;ROLE=REQ-PARTICIPANT;RSVP=TRUE:mailto:{email}
        END:VEVENT
        END:VCALENDAR
        """

                # Generate the HTML body for the email
                html_body = f"""
                <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                            h2, h3 {{ color: #0056b3; }}
                            p {{ margin-bottom: 10px; }}
                            .button {{
                                background-color: #0056b3;
                                color: white;
                                padding: 10px 20px;
                                text-align: center;
                                text-decoration: none;
                                display: inline-block;
                                border-radius: 5px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h2>Meeting Invitation: {invite_summary}</h2>
                            <h3>Event Details</h3>
                            <p><strong>Date:</strong> {start_time.strftime('%B %d, %Y')}</p>
                            <p><strong>Time:</strong> {start_time.strftime('%H:%M %p')} - {end_time.strftime('%H:%M %p')}</p>
                            <p><strong>Description:</strong><br>{invite_description}</p>
                            <p>This event can be added to your calendar automatically by accepting the invitation. Thank you!</p>
                        </div>
                    </body>
                </html>
                """
                sender_name = 'Meeting Invitation'
                # Main message container, using 'mixed' to support both body and attachment
                msg = MIMEMultipart('mixed')
                msg['Subject'] = invite_summary
                msg['From'] = sender_name
                msg['To'] = email

                # Create a container for the plain text and HTML parts of the body
                msg_body = MIMEMultipart()
                msg_body.attach(MIMEText(invite_description, 'plain'))
                msg_body.attach(MIMEText(html_body, 'html'))
                msg.attach(msg_body)

                # Attach the iCalendar file part
                ical_part = MIMEText(ical_content, 'calendar')
                ical_part.add_header('Content-Type', 'text/calendar; method=REQUEST; charset=UTF-8')
                ical_part.add_header('Content-Transfer-Encoding', 'base64')
                ical_part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
                
                encoded_ical = base64.b64encode(ical_content.encode('utf-8')).decode('utf-8')
                ical_part.set_payload(encoded_ical)
                msg.attach(ical_part)

                # Send the email
                port = 465
                smtp_server = "smtp.gmail.com"
                context = ssl.create_default_context()

                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, email, msg.as_string())
                
                print("Meeting invite with HTML body and iCalendar sent successfully via SMTP.")
                return "Meeting invite sent successfully via SMTP with an HTML body and calendar attachment."
            except Exception as e:
                print(f"Failed to send email invite: {e}")
                return f"Failed to send email invite: {e}"
    

    
    

def send_to_slack(channel: str, session: dict) -> str:
    """
    Sends the MoM to a Slack channel.

    Args:
        channel: The Slack channel ID to send the message to.
        session: The agent's session dictionary.

    Returns:
        A string confirming the message was sent or an error.
    """
    if "moms" not in session or not session["moms"]:
        return "No Minutes of Meeting (MoM) found in the session to analyze."

    mom_data = session["moms"][-1]["mom"]
    SLACK_BOT_TOKEN = os.environ.get("SLACK_API_TOKEN")

    if not SLACK_BOT_TOKEN:
        return "Error: SLACK_API_TOKEN environment variable not set."

    title = mom_data.get('title', 'Meeting Minutes')
    summary = mom_data.get('summary', 'No summary provided.')
    decisions = "\n".join([f"- • {d}" for d in mom_data.get('decisions', [])])
    action_items = "\n".join([
        f"- *Action:* {a.get('action')}\n  - *Owner:* {a.get('owner', 'N/A')}\n  - *Due Date:* {a.get('due_date', 'N/A')}"
        for a in mom_data.get('action_items', [])
    ])
    
    slack_message_text = (
        f"📌 *Minutes of Meeting: {title}*\n\n"
        f"*Summary*\n{summary}\n\n"
        f"*Decisions*\n{decisions}\n\n"
        f"*Action Items*\n{action_items}"
    )

    payload = {
        "channel": channel,
        "text": slack_message_text,
    }

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        if response_json.get("ok"):
            return f"MOM successfully posted to Slack channel {channel}."
        else:
            return f"Failed to post to Slack: {response_json.get('error')}"
    except requests.exceptions.RequestException as e:
        return f"Failed to send message to Slack: {e}"