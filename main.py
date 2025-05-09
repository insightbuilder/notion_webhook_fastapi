from fastapi import FastAPI, HTTPException
from notion_client import Client
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any, Union
from dotenv import load_dotenv
import httpx
import os

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
notion = Client(auth=os.environ["NOTION_TOKEN"])


class Author(BaseModel):
    id: str
    type: Literal["person"]


class Entity(BaseModel):
    id: str
    type: Literal["page"]


class Parent(BaseModel):
    id: str
    type: str  # could be "space", "page", etc.


class Data(BaseModel):
    parent: Parent
    updated_properties: List[str]


class NotionWebhookPayload(BaseModel):
    id: str
    timestamp: str
    workspace_id: str
    workspace_name: str
    subscription_id: str
    integration_id: str
    authors: List[Author]
    attempt_number: int
    entity: Entity
    type: str
    data: Data


# In-memory storage for verification token
verification_token_store = {}


class VerificationPayload(BaseModel):
    verification_token: str


app = FastAPI()


@app.get("/")
def read_root():
    logger.info(f"Testing Logger....")
    return {"Hello": "World"}


@app.post("/notion-webhook")
async def handle_notion_webhook(
    payload: Union[NotionWebhookPayload, VerificationPayload],
):
    logger.info(f"Received Notion Webhook Payload: {payload}")
    return {"message": "payload is recieved"}
    # if "verification_token" in payload:
    #     logger.info(f"Received VerificationPayload: {payload}")
    #     verification_token_store["token"] = payload["verification_token"]
    #     return {"message": "Verification token is stored"}
    # else:
    #     logger.info(f"Received Notion Webhook Payload: {payload}")
    #     # this payload is NotionWebhookPayload
    #     page_id = payload["id"]

    #     update_payload = {"properties": {"Status": {"select": {"name": "Completed"}}}}
    #     logger.info(update_payload)

    #     return {"message": f"Page {page_id} successfully recieved"}
