from notion_client import Client
from youtube_main import get_youtube_video_details, update_page, extract_video_id
import os

notion = Client(auth=os.environ["YTDEMO_TOKEN"])

page_id = "1f05132d889c80af985be79654334a89"
source_db = "1f05132d889c80649a98dfda5d138dbb"

# children = notion.blocks.children.list(block_id=source_db)
# child_results = children.get("results")

# for block in child_results:
#     print(block["id"])
#     btype = block["type"]
#     print(block[btype])

# to find the block, I can use the id that I have
# blk_id = "1ee84ade-96ac-8083-bbf1-de55cacf319e"

# for block in child_results:
#     if block["id"] == blk_id:
#         print(block)

# able to update

# new_page = notion.pages.update(
#     page_id=page_id,
#     properties={
#         "Name": {"rich_text": [{"text": {"content": "title"}}]},
#     },
# )

# pages_results = notion.databases.query(
#     database_id=source_db,
#     sorts=[{"property": "created_time", "direction": "descending"}],
# )

# edited_page = pages_results.get("results", [])[0]
# # 'URL': {'id': 'title', 'type': 'title', 'title': [{'type': 'text', 'text': {'content': 'another test', 'link': None}
# print(edited_page["properties"]["URL"]["title"][0]["text"]["content"])

# print(edited_page["id"])

# # testing the functions
video_id = extract_video_id(yt_url="https://youtu.be/pJo169NVMTw?si=2dxDKR8ShChfxO1g")
yt_data = get_youtube_video_details(video_id=video_id)
print(yt_data)
update_page(page_id, yt_data)
