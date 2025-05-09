from fastapi import FastAPI, HTTPException
from md2notionpage.core import parse_md
from notion_client import Client
from typing import Dict, Any
from dotenv import load_dotenv
from anthropic import Anthropic
import os

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
notion = Client(auth=os.environ["NOTION_TOKEN"])
anthropic = Anthropic()


# In-memory storage for verification token
verification_token_store = {}


app = FastAPI()


@app.get("/")
def read_root():
    logger.info(f"Testing Logger....")
    return {"Hello": "World"}


@app.post("/notion-webhook")
async def handle_notion_webhook(
    payload: Dict[str, Any],
):
    logger.info(f"Received Notion Webhook Payload: {payload}")
    # return {"message": "payload is recieved"}
    if "verification_token" in payload:
        logger.info(f"Received VerificationPayload: {payload}")
        verification_token_store["token"] = payload["verification_token"]
        return {"message": "Verification token is stored"}
    else:
        # this payload is NotionWebhookPayload
        page_id = payload["entity"]["id"]
        update_type = payload["type"]
        blk_id = payload["data"]["updated_blocks"][-1]["id"]

        logger.info(
            f"The page id: {page_id} and the blk id: {blk_id} with update_type is {update_type}"
        )
        children = notion.blocks.children.list(block_id=page_id)

        child_results = children.get("results")

        for block in child_results:
            if block["id"] == blk_id:
                print(block["type"])
                btype = block["type"]

                print(f"The content in {blk_id}")

                print(block[btype]["rich_text"][0]["text"]["content"])

                query = block[btype]["rich_text"][0]["text"]["content"]

                messages = [{"role": "user", "content": query}]

                # Initial Claude API call
                response = anthropic.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=1000,
                    messages=messages,
                )

                markdown_text = response.content[0].text

                logger.info(f"Markdown text: {markdown_text}")

                created_page = notion.pages.create(
                    parent={"type": "page_id", "page_id": page_id},
                    properties={},
                    children=[],
                )

                notion.pages.update(
                    created_page["id"],
                    properties={
                        "title": {
                            "title": [{"type": "text", "text": {"content": query}}]
                        }
                    },
                )

                # Iterate through the parsed Markdown blocks and append them to the created page
                for block in parse_md(markdown_text):
                    notion.blocks.children.append(created_page["id"], children=[block])

        return {"message": f"Page {page_id} successfully recieved"}
