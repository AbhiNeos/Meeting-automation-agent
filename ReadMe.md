# 🧑‍💻 Meeting Automation Agent

## 📌 Overview

The **Meeting Automation Agent** is an AI-powered tool designed to
automate post-meeting workflows.\
It can:\
- Generate **Minutes of Meeting (MoM)** from transcripts.\
- Extract **action items** automatically.\
- Create **Jira tickets** from action items.\
- Send updates to **Slack** or **Email**.\
- **Schedule calls** and calendar invites directly.

This project was built for the **Agentic Era Hackathon** by **Abhishek
Chauhan (Neoites Team)**.

------------------------------------------------------------------------

## 🚀 Features

-   **Summarization** → Convert transcripts into concise MoM.\
-   **Action Item Detection** → Identify and list tasks.\
-   **Task Management** → Create Jira tickets directly.\
-   **Multi-channel Communication** → Share updates over Email and
    Slack.\
-   **Scheduling** → Automate follow-up calls or calendar invites.

------------------------------------------------------------------------

## 🛠️ Installation & Setup

1.  **Clone the repository**

    ``` bash
    git clone https://github.com/your-username/meeting-automation-agent.git
    cd meeting-automation-agent
    ```

2.  **Create and activate a virtual environment**

    ``` bash
    python -m venv venv
    source venv/bin/activate   # On macOS/Linux
    venv\Scripts\activate      # On Windows
    ```

3.  **Install dependencies**

    from pyproject.toml file

4.  **Set up the `.env` file**\
    ⚠️ For security reasons, the `.env` file that contained credentials
    has been **removed**.\
    To get this agent working, you must create a new `.env` file in the
    project root with the required environment variables:

    Example `.env`:

    ``` env
    SMTP_USERNAME=
    SMTP_HOST=
    SMTP_PORT=
    EMAIL_USERNAME=
    SMTP_PASSWORD=

    # Jira credentials
    JIRA_URL=
    JIRA_USERNAME=
    JIRA_API_TOKEN=

    # Slack credentials
    SLACK_API_TOKEN=
    SLACK_CHANNEL_ID= # A default channel for MoM
    
    # Email credentials (e.g., SendGrid or a local SMTP server)
    SENDER_EMAIL=
    EMAIL_SMTP_SERVER=
    EMAIL_SMTP_PORT=
    EMAIL_USERNAME=
    SENDER_PASSWORD=
    ```

5.  **Run the agent**

    ``` bash
    cd meeting-automation-agent
    make playground
    ```

------------------------------------------------------------------------

## 📂 Project Structure

    meeting-automation-agent/
    │── app.py              # Main application entry
    │── README.md           # Documentation
    │── .env (not included) # Environment variables (to be created by user)
    │── utils/              # Helper functions
    │── agents/             # Core agent logic
    │── integrations/       # Slack, Jira, Email, Calendar integrations

------------------------------------------------------------------------

## 🔮 Future Roadmap

-   Deploy as a **Web Agent & API server** for integration with any
    platform.\
-   Support for **Microsoft Teams** and **Google Chat**.\
-   Add **sentiment analysis** for meeting transcripts.\
-   Provide a **conversational interface** for querying past meetings.

------------------------------------------------------------------------

## 🙌 Acknowledgements

Developed by **Abhishek Chauhan (Neoites)** for the **Agentic Era
Hackathon** 🚀
