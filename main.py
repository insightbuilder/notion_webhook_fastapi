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

    if "verification_token" in payload:
        logger.info(f"Received VerificationPayload: {payload}")
        verification_token_store["token"] = payload["verification_token"]
        return {"message": "Verification token is stored"}
    else:
        # Here the actual payload will be received
        source_page = "1ec84ade96ac803bbe86e258a017466b"
        # every time the payload is recieved, need to check if it is from source_page else discard it
        page_id = payload["entity"]["id"].replace("-", "")

        if page_id != source_page:
            logger.info(
                f"Payload from child page, not processing: {payload['entity']['id']}"
            )
            # do an early return
            return {"message": "Payload from child page, not processing"}

        if payload["data"]["updated_blocks"][-1]["type"] == "page":
            logger.info("Content Updated is a Page, should not process")
            # do an early return
            return {"message": "Page created as content, not processing"}

        if payload["data"]["updated_blocks"][-1]["type"] == "title":
            logger.info("Content Updated is page title, Nothing to process")
            # do an early return
            return {"message": "Page title changed, not processing"}

        update_type = payload["type"]

        if update_type == "page.deleted":
            logger.info("Page deleted, nothing to process.")
            # do an early return
            return {"message": "Page deleted, nothing to process."}

        blk_id = payload["data"]["updated_blocks"][-1]["id"]

        logger.info(
            f"The page id: {page_id} and the blk id: {blk_id} with update_type is {update_type}"
        )
        children = notion.blocks.children.list(block_id=page_id)

        child_results = children.get("results")
        last_updt = child_results[-1]

        btype = last_updt["type"]

        if (
            update_type == "page.content_updated"
            and len(last_updt[btype]["rich_text"]) > 0
        ):
            logger.info("Processing the last update by user.")

            query = last_updt[btype]["rich_text"][0]["text"]["content"]

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
            # Stripping the question mark from query if present
            if "?" in query:
                query = query.replace("?", "")

            # Adding the reply part to the query
            query = f"Reply to {query}"

            notion.pages.update(
                created_page["id"],
                properties={
                    "title": {"title": [{"type": "text", "text": {"content": query}}]}
                },
            )

            # Iterate through the parsed Markdown blocks and append them to the created page
            for block in parse_md(markdown_text):
                notion.blocks.children.append(created_page["id"], children=[block])

            logger.info(f"Update in page with {source_page} successfully completed")
        else:
            logger.info(
                "The last paragraph is empty. Remove it.",
                f"The page with {last_updt['parent']['page_id']} is not updated",
            )

        return {"message": f"Update in page with {source_page} successfully completed"}
