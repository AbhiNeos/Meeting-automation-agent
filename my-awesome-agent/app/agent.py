# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import google.auth
from google.adk.agents import Agent
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
from app.utils.action_item_tools import (
    analyze_mom_for_actions,
    create_jira_ticket,
    schedule_call,
    send_to_slack,
)

# --- Boilerplate Setup ---
# Initialize authentication and set environment variables for Google Cloud.
_, project_id = google.auth.default()
LOCATION = "us-central1"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", LOCATION)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Initialize the Vertex AI SDK
vertexai.init(project=project_id, location=LOCATION)

# --- Tool Definitions ---
def fetch_and_process_url(url: str, session: dict) -> str:
    """
    Fetches content from a given URL, generates a summary and a "Minutes of Meeting" (MoM)
    in JSON format, and saves them to the agent's session memory.

    Args:
        url: The web URL to fetch and summarize.
        session: The agent's session dictionary for storing data.

    Returns:
        A string indicating the status of the operation.
    """
    print(f"[LOG] Starting to fetch and process URL: {url}")
    try:
        print("[LOG] Sending HTTP GET request...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("[LOG] Successfully fetched URL.")

        print("[LOG] Parsing HTML content...")
        text_content = response.content
        print("[LOG] Successfully parsed HTML.")

        if not text_content:
            print("[LOG] No text content found.")
            return "Could not extract any text from the provided URL."
        
        print("[LOG] Generating summary...")
        model = GenerativeModel("gemini-2.5-pro")
        prompt = f"""
    Please provide a concise summary of the following meeting transcript.
    
    Transcript:
    {text_content}
    """

        gemini_response = model.generate_content(prompt)
        summary = gemini_response.text.strip()
       
        print("[LOG] Successfully generated summary.")

        # Generate MoM in JSON format
        print("[LOG] Generating Minutes of Meeting (MoM) in JSON format...")
        model = GenerativeModel("gemini-2.5-pro")
        prompt = f""" You are an expert at creating professional Minutes of Meeting (MOM).
    From the following transcript, create a concise MOM in a JSON format.
    The JSON object must have the following keys:
    - "title": A brief title for the meeting.
    - "summary": A brief overview of the discussion.
    - "decisions": An array of strings, where each string is a decision made.
    - "action_items": An array of objects, where each object has keys "action", "owner", and "due_date".
    - "attendees": An array of strings with the names of attendees.

    Return only the JSON object, no other text.

    ---
        Text:
        {text_content}
        """
        response = model.generate_content(prompt)
        try:
            mom_json_str = response.text.strip().replace("```json", "").replace("```", "")
            mom = json.loads(mom_json_str)
        except json.JSONDecodeError:
            return "Error: Failed to decode the MoM JSON from the model's response."
        print("[LOG] Successfully generated MoM.")

        print("[LOG] Saving summary and MoM to session...")
        if "summaries" not in session:
            session["summaries"] = []
        session["summaries"].append({"url": url, "summary": summary})

        if "moms" not in session:
            session["moms"] = []
        session["moms"].append({"url": url, "mom": mom})
        print("[LOG] Successfully saved to session.")

        return f"Summary and MoM of {url} have been fetched and saved to session."

    except requests.exceptions.RequestException as e:
        error_message = f"Error: Failed to fetch the URL. Details: {e}"
        print(f"[LOG] {error_message}")
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(f"[LOG] {error_message}")
        return error_message


def send_email(to_email: str, session: dict) -> str:
    """
    Sends an email with a formatted "Minutes of Meeting" (MoM) from the session.

    Args:
        to_email: The recipient's email address.
        session: The agent's session dictionary for storing data.

    Returns:
        A string confirming that the email was sent or an error message.
    """
    print("[LOG] Starting to send email.")

    if "moms" not in session or not session["moms"]:
        return "Error: No Minutes of Meeting (MoM) found in the session."
    mom_json = session["moms"][-1]["mom"]

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender_name = 'NeosAlpha Meeting Support'

    if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
        return "Error: SMTP environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD) are not set."

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return "Error: SMTP_PORT must be an integer."

    sender_email = smtp_username

    message = MIMEMultipart()
    message["Subject"] = 'Minutes of Meeting: ' + mom_json.get('title', 'Untitled Meeting')
    message["From"] = sender_name
    message["To"] = to_email

    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                h2, h3 {{ color: #0056b3; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ padding: 12px; border: 1px solid #ccc; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3>Summary</h3>
                <p>{mom_json.get('summary', 'No summary provided.')}</p>
                <h3>Decisions</h3>
                <ul>
                    {''.join(f'<li>&#x2022; {d}</li>' for d in mom_json.get('decisions', []))}
                </ul>
                <h3>Action Items</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Action</th>
                            <th>Owner</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{a.get("action")}</td><td>{a.get("owner")}</td><td>{a.get("due_date", "TBD")}</td></tr>' for a in mom_json.get('action_items', []))}
                    </tbody>
                </table>
            </div>
        </body>
    </html>
    """

    part = MIMEText(html_body, "html")
    message.attach(part)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, to_email, message.as_string())
        return "Email sent successfully!"
    except smtplib.SMTPException as e:
        return f"An error occurred while sending the email: {e}"

    suggestions += "\nI can also send the MoM to a Slack channel."
    suggestions += "\nWhat would you like to do?"

    return suggestions
# --- Agent Definition ---
# The agent is configured to use the new tools.
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-pro",
    instruction=(
        "You are a helpful AI assistant. You have two primary functions:"
        "1. Fetch and summarize content from transcript using the `fetch_and_process_url` tool."
        "2. Send emails with an HTML body using the `send_email` tool."
        "When a user provides a URL, use the `fetch_and_process_url` tool to process it. "
        "After the summary is generated, you must present the summary to the user."
        "When a user asks to send an email, use the `send_email` tool. "
        "You can use data from the session to compose the email."
        "After processing a URL, you can analyze the MoM for action items using `analyze_mom_for_actions`."
        "Based on the user's request, you can then use `create_jira_ticket`, `schedule_call`, or `send_to_slack`."
    ),
    tools=[fetch_and_process_url, send_email, analyze_mom_for_actions, create_jira_ticket, schedule_call, send_to_slack],
)
