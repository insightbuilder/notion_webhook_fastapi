# FastAPI Webhook Server for Notion Integration

Repo contains the code for FastAPI app that
receives and processes the Notion Events through
the Webhook integration.

The app is deployed in
[Railway](https://railway.app/) after signing up
and connecting github account to it.

Process of Deployment:

1. Fork the repo. This will get the repo and the
   code into your github account.

2. Signup in Railway App and connect your Github.

3. Create a new project.

4. Add a new service to the project using Github.

5. Select the notion_webhook_fastapi repo from the
   list.

Build Process:

The app is built with uv package managment, so the
build process is automatically taken care by the
railway app.

The start command for the app is:

uv run uvicorn main:app --host 0.0.0.0 --reload

You have to Generate a Domain in the Settings of
the project in Railway app. That will give you a
https link, which is required for the webhook
integration.
