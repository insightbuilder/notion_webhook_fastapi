from fastapi import FastAPI, HTTPException,
from notion_client import Client
from pydantic import BaseModel
from typing import List, Optional, Literal
from dotenv import load_dotenv
import httpx
import os

load_dotenv()

app = FastAPI()
notion = Client(auth=os.environ["NOTION_TOKEN"])


class PersonRef(BaseModel):
    id: str
    type: Literal["person"]


class BotRef(BaseModel):
    id: str
    type: Literal["bot"]


class PageRef(BaseModel):
    id: str
    type: Literal["page"]


class Entity(BaseModel):
    id: str
    type: Literal["page"]


class NotionWebhookPayload(BaseModel):
    id: str
    timestamp: str
    workspace_id: str
    workspace_name: str
    subscription_id: str
    integration_id: str
    type: str
    authors: List[PersonRef]
    accessible_by: List[PersonRef | BotRef]
    attempt_number: int
    entity: Entity
    data: dict

# In-memory storage for verification token
verification_token_store = {}

class VerificationPayload(BaseModel):
    verification_token: str

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/notion-webhook")
async def handle_notion_webhook(payload: NotionWebhookPayload | VerificationPayload):
    if isinstance(payload, VerificationPayload):
        verification_token_store["token"] = payload.verification_token
        return {"message": f"Verification token is {payload.verification_token} is stored"}
    else:
        # this payload is NotionWebhookPayload
        page_id = payload.entity.id

        update_payload = {"properties": {"Status": {"select": {"name": "Completed"}}}}
        print(update_payload)


        return {"message": f"Page {page_id} updated successfully"}
