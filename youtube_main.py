import re
from fastapi import FastAPI, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Optional, Literal, Union
from pydantic import BaseModel
from notion_client import Client
from typing import Dict, Any
from googleapiclient.discovery import build
import os

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.environ["YOUTUBE_API_KEY"]
NOTION_KEY = os.environ["WYT_TOKEN"]


class Author(BaseModel):
    id: str
    type: Optional[Literal["person"]]


class Entity(BaseModel):
    id: str
    type: Optional[Literal["page"]]


class Parent(BaseModel):
    id: str
    type: Optional[str]


class Blocks(BaseModel):
    id: str
    type: str


class Data(BaseModel):
    parent: Optional[Parent]
    updated_properties: Optional[List[str]]
    updated_blocks: Optional[List[Blocks]]


class WebhookPayload(BaseModel):
    verification_token: Optional[str]
    id: str
    timestamp: str
    workspace_id: Optional[str]
    workspace_name: Optional[str]
    subscription_id: Optional[str]
    integration_id: Optional[str]
    authors: Optional[List[Author]]
    attempt_number: Optional[int]
    entity: Optional[Entity]
    type: Optional[str]
    data: Optional[Data]


### ✅ Create a Page from YouTube Search Data inside yt_vid_analysis DB only
def create_page_from_yt(database_id, yt_data):
    """The properties used below are specific to databases"""
    logger.info(f"Creating new page in {database_id} database")
    new_page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"rich_text": [{"text": {"content": yt_data["title"]}}]},
            "vid": {"rich_text": [{"text": {"content": yt_data["video_id"]}}]},
            "channel": {"rich_text": [{"text": {"content": yt_data["channel"]}}]},
            "channelId": {"rich_text": [{"text": {"content": yt_data["channel_id"]}}]},
            "Description": {
                "rich_text": [{"text": {"content": yt_data["description"]}}]
            },
            "URL": {"title": [{"text": {"content": yt_data["url"]}}]},
            "views": {"number": int(yt_data["views"])},
            "likes": {"number": int(yt_data["likes"])},
        },
    )
    logger.info(f"Page created for {yt_data['title']}")
    return f"Page created for {yt_data['title']}"


def extract_video_id(yt_url):
    """Extracts Video ID from a YouTube URL"""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, yt_url)
    return match.group(1) if match else None


def get_youtube_video_details(yt_url):
    """Fetches video details (Title, ID, Channel, Channel ID, Description) from YouTube API"""
    video_id = extract_video_id(yt_url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        # Fetch video details
        youtube = build("youtube", "v3", developerKey=API_KEY)
        response = (
            youtube.videos().list(part="snippet, statistics", id=video_id).execute()
        )
        # print(response)
        if "items" not in response or not response["items"]:
            return {"error": "Video not found"}

        video_data = response["items"][0]["snippet"]
        video_stats = response["items"][0]["statistics"]
        try:
            return {
                "video_id": video_id,
                "title": video_data["title"],
                "channel": video_data["channelTitle"],
                "channel_id": video_data["channelId"],
                "description": video_data["description"][:1000],
                # "tags": video_data["tags"],
                "likes": video_stats["likeCount"],
                "views": video_stats["viewCount"],
            }
        except Exception as e:
            return {"error in video data": str(e)}

    except Exception as e:
        return {"error in fetching response": str(e)}


app = FastAPI()

notion = Client(auth=NOTION_KEY)


# In-memory storage for verification token
verification_token_store = {}


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Error Body: {exc.body}")
    logger.error(f"Error Detail: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.get("/")
def read_root():
    logger.info("Testing Logger....")
    return {"Hello": "World"}


@app.post("/notion-webhook")
async def handle_notion_webhook(payload: WebhookPayload):
    logger.info(f"Received Notion Webhook Payload: {payload}")

    if payload.verification_token:
        logger.info(f"Received VerificationPayload: {payload}")
        return {"message": "Verification token is stored"}
    else:
        # Here the actual payload will be received
        logger.info("Received Data Payload: {payload}")
        source_db = "1f05132d889c80649a98dfda5d138dbb"

        update_type = payload.type

        logger.info(f"Payload parsed: {update_type}")

        return {"message": "Update to db successfully completed"}
