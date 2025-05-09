from notion_client import Client
import os

notion = Client(auth="")

page_id = "1ec84ade96ac803bbe86e258a017466b"

children = notion.blocks.children.list(block_id=page_id)
child_results = children.get("results")

for block in child_results:
    print(block["id"])
    btype = block["type"]
    print(block[btype])

# to find the block, I can use the id that I have
# blk_id = "1ee84ade-96ac-8083-bbf1-de55cacf319e"

# for block in child_results:
#     if block["id"] == blk_id:
#         print(block)
