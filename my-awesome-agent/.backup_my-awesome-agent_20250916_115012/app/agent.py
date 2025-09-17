# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests
from bs4 import BeautifulSoup

import google.auth
from google.adk.agents import Agent
import vertexai
from vertexai.generative_models import GenerativeModel

# --- Boilerplate Setup ---
# Initialize authentication and set environment variables for Google Cloud.
_, project_id = google.auth.default()
LOCATION = "us-central1"  # Specify a valid region for Vertex AI
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", LOCATION)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Initialize the Vertex AI SDK
vertexai.init(project=project_id, location=LOCATION)

# --- New Tool Definition ---
def fetch_and_summarize_url(url: str, session: dict) -> str:
    """
    Fetches content from a given URL, generates a summary, and saves it
    to the agent's session memory.

    Args:
        url: The web URL to fetch and summarize.
        session: The agent's session dictionary for storing data.

    Returns:
        A string confirming that the summary was saved or an error message.
    """
    print(f"Fetching content from: {url}")
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the HTML content and extract clean text
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)

        if not text_content:
            return "Could not extract any text from the provided URL."

        # Use a generative model to summarize the extracted text
        print("Generating summary...")
        summarization_model = GenerativeModel("gemini-1.5-flash")
        # Truncate content to fit within model context limits if necessary
        prompt = f"Provide a concise summary of the following content:\n\n{text_content[:8000]}"
        
        summary_response = summarization_model.generate_content(prompt)
        summary = summary_response.text

        # Save the summary and the source URL to the session dictionary
        session['url_summary'] = summary
        session['source_url'] = url

        print("Summary saved to session.")
        return "The summary has been successfully generated and saved to the session."

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to fetch the URL. Details: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# --- Agent Definition ---
# The agent is configured to use the new tool.
root_agent = Agent(
    name="root_agent",
    model="gemini-1.5-flash",
    instruction=(
        "You are a helpful AI assistant. Your primary function is to fetch "
        "and summarize content from web pages using the tools provided. "
        "When a user provides a URL, use the `fetch_and_summarize_url` tool "
        "to process it and save the result."
    ),
    tools=[fetch_and_summarize_url],
)