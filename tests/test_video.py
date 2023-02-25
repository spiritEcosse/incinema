# import aioboto3
# import pytest
# from unittest.mock import MagicMock, patch
# from models.video import Item
#
#
# @pytest.fixture
# async def table():
#     async with aioboto3.resource('dynamodb') as dynamodb:
#         table_name = Item.table()
#         table = await dynamodb.create_table(
#             TableName=table_name,
#             KeySchema=[
#                 {'AttributeName': 'id', 'KeyType': 'HASH'}
#             ],
#             AttributeDefinitions=[
#                 {'AttributeName': 'id', 'AttributeType': 'S'}
#             ],
#             ProvisionedThroughput={
#                 'ReadCapacityUnits': 5,
#                 'WriteCapacityUnits': 5
#             }
#         )
#         yield table
#         await table.delete()
#
#
# @pytest.mark.asyncio
# async def test_delete_all_items(table):
#     # Insert some items into the table
#     await table.put_item(Item={'id': '1', 'name': 'Alice'})
#     await table.put_item(Item={'id': '2', 'name': 'Bob'})
#     await table.put_item(Item={'id': '3', 'name': 'Charlie'})
#
#     # Delete all items from the table
#     await Item.delete_all_items()
#
#     # Verify that the table is now empty
#     items = await table.scan()['Items']
#     assert len(items) == 0
