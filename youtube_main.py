import re
from fastapi import FastAPI, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Optional, Literal
from pydantic import BaseModel
from notion_client import Client
from googleapiclient.discovery import build
import os

import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.environ["YOUTUBE_API_KEY"]
NOTION_KEY = os.environ["YTDEMO_TOKEN"]


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
    parent: Optional[Parent] = None
    updated_properties: Optional[List[str]] = None
    updated_blocks: Optional[List[Blocks]] = None


class WebhookPayload(BaseModel):
    verification_token: Optional[str] = None
    id: Optional[str] = None
    timestamp: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    subscription_id: Optional[str] = None
    integration_id: Optional[str] = None
    authors: Optional[List[Author]] = None
    attempt_number: Optional[int] = None
    entity: Optional[Entity] = None
    type: Optional[str] = None
    data: Optional[Data] = None


### ✅ Create a Page from YouTube Search Data inside yt_vid_analysis DB only
def update_page(page_id, yt_data):
    """The properties are update on the given page id"""
    logger.info(f"Entering update page function with {page_id}")
    new_page = notion.pages.update(
        page_id=page_id,
        properties={
            "Name": {"rich_text": [{"text": {"content": yt_data["title"]}}]},
            "vid": {"rich_text": [{"text": {"content": yt_data["video_id"]}}]},
            "channel": {"rich_text": [{"text": {"content": yt_data["channel"]}}]},
            "channelId": {"rich_text": [{"text": {"content": yt_data["channel_id"]}}]},
            "Description": {
                "rich_text": [{"text": {"content": yt_data["description"]}}]
            },
            # "URL": {"title": [{"text": {"content": yt_data["url"]}}]},
            "views": {"number": int(yt_data["views"])},
            "likes": {"number": int(yt_data["likes"])},
        },
    )
    logger.info(f"Page update for {yt_data['title']}")
    return f"Page updated for {yt_data['title']}"


def extract_video_id(yt_url):
    """Extracts Video ID from a YouTube URL"""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, yt_url)
    return match.group(1) if match else None


def get_youtube_video_details(video_id):
    """Fetches video details (Title, ID, Channel, Channel ID, Description) from YouTube API"""
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
        source_db = ""
        logger.info(f"Received Data Payload: {payload}")

        if payload.type != "page.created":
            logger.info("Change in db is not page creation, not processing")
            return {"message": "No process"}

        logger.info("Page created payload recieved.")

        if payload.data.parent.type == "database":
            source_db = payload.data.parent.id
        else:
            logger.info("Parent of data change is not a database. Aborting process.")
            return {"message": "Parent of data change is not a database."}

        # get the list of pages in db
        pages_results = notion.databases.query(
            database_id=source_db,
            sorts=[{"property": "created_time", "direction": "descending"}],
        )

        added_page = pages_results.get("results", [])[0]
        logger.info(f"Page id is {added_page['id']}.")
        # get the url property of the page

        extracted_url = added_page["properties"]["URL"]["title"][0]["text"]["content"]
        logger.info(f"extracted_url is {extracted_url}.")

        try:
            video_id = extract_video_id(extracted_url)

            # get yt details of the url
            yt_details = get_youtube_video_details(video_id)
            logger.info(f"Got YT Details: {yt_details}")

            # update the page with yt_details
            update_status = update_page(added_page["id"], yt_details)
            logger.info(f"Payload parsed: {update_status}")

            return {"message": "Update to db successfully completed"}

        except Exception as e:
            logger.info(f"{extracted_url} had the issue:. {e}")
            return {"Message": "Check Page URL property"}
