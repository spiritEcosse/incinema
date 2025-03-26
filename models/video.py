import asyncio
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Set

import aioboto3

from serializer import DataClassJSONSerializer


@dataclass
class Video(DataClassJSONSerializer):
    """A class representing a video

    >>> video = Video('vid1', 'http://example.com/video1.mp4')
    >>> video.id
    'vid1'
    >>> video.url
    'http://example.com/video1.mp4'
    """
    id: str
    url: str


@dataclass
class Description(DataClassJSONSerializer):
    ru: str = ""
    en: str = ""


@dataclass
class Title(DataClassJSONSerializer):
    en: str
    ru: str = ""


# Add this new method to the MixinDynamoTable class
class MixinDynamoTable:
    @classmethod
    def table(cls):
        return cls.__name__.lower()

    @classmethod
    async def get_by_id(cls, id_value):
        """
        Get an item from the DynamoDB table by its ID.

        Parameters:
        -----------
        id_value : str
            The ID value to search for

        Returns:
        --------
        dict or None
            The item if found, None otherwise
        """
        table_name = cls.table()
        session = aioboto3.Session()

        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(table_name)

            # Get the item by ID
            response = await table.get_item(
                Key={'id': id_value}
            )

            # Return the item if it exists
            data = response.get('Item')
            print(f"Item found: {data}")
            return data

    @classmethod
    async def get_dynamo_count(cls, index_name=None, filter_expression=None):
        """
        Get the count of items in a DynamoDB table.

        Parameters:
        -----------
        index_name : str, optional
            The name of a global secondary index to use
        filter_expression : boto3.dynamodb.conditions.ConditionBase, optional
            Filter expression to apply

        Returns:
        --------
        int
            The count of items in the table
        """
        table_name = cls.table()
        session = aioboto3.Session()

        async with session.resource('dynamodb') as dynamo_resource:
            # Get the table
            table = await dynamo_resource.Table(table_name)

            # Parameters for the scan operation
            scan_params = {
                'Select': 'COUNT'
            }

            # Add index_name if provided
            if index_name:
                scan_params['IndexName'] = index_name

            # Add filter_expression if provided
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression

            # Get total count with pagination
            total_count = 0
            last_evaluated_key = None

            print(f"Counting items in table '{table_name}'...")

            # Continue scanning until all items have been counted
            while True:
                # Include the ExclusiveStartKey if we're continuing from a previous scan
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key

                # Perform the scan
                response = await table.scan(**scan_params)

                # Add the count from this page
                total_count += response['Count']

                # Get the key for the next page, if any
                last_evaluated_key = response.get('LastEvaluatedKey')

                # If there's no more data, break
                if not last_evaluated_key:
                    break

                print(f"Counted {total_count} items so far...")

            print(f"Total count: {total_count} items")
            return total_count

    @classmethod
    async def save(cls, items: List):
        session = aioboto3.Session()
        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(cls.table())

            async with table.batch_writer() as batch:
                for item in items:
                    await batch.put_item(Item=item.to_dict())

    @classmethod
    async def scan_all(cls):
        """
        Scan all items from the DynamoDB table

        Returns:
        --------
        List
            List of all items as model objects
        """
        table_name = cls.table()
        session = aioboto3.Session()
        results = []

        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(table_name)

            # Scan with pagination
            last_evaluated_key = None

            while True:
                scan_kwargs = {}
                if last_evaluated_key:
                    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

                response = await table.scan(**scan_kwargs)
                items = response.get('Items', [])

                # Convert items to objects
                for item in items:
                    obj = cls.from_dict(item)
                    results.append(obj)

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

            return results

    @classmethod
    async def get_existing_ids(cls) -> Set[str]:
        """
        Get all existing IDs from the DynamoDB table

        Returns:
        --------
        Set[str]
            Set of all existing IDs
        """
        table_name = cls.table()
        session = aioboto3.Session()
        ids = set()

        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(table_name)

            # Use ProjectionExpression to only get the ID field
            scan_kwargs = {
                'ProjectionExpression': 'id'
            }

            # Scan with pagination
            last_evaluated_key = None

            while True:
                if last_evaluated_key:
                    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

                response = await table.scan(**scan_kwargs)
                items = response.get('Items', [])

                # Extract IDs
                for item in items:
                    ids.add(item.get('id'))

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

            return ids


@dataclass
class Movie(MixinDynamoTable, DataClassJSONSerializer):
    id: str
    title: Title
    genres: List[str]
    popularity: int
    rating: Decimal
    runtime: Decimal
    votes: int
    production_status: Optional[str] = ""
    year: Optional[str] = ""
    audience: Optional[str] = ""
    overview: Optional[str] = ""
    directors: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    imdb_type: Optional[str] = ""
    video: Optional[Video] = None
    description: Optional[Description] = None
    end_year: Optional[str] = ""


@dataclass
class Item(MixinDynamoTable, DataClassJSONSerializer):
    """A class representing an item

    >>> video = Video('vid1', 'http://example.com/video1.mp4')
    >>> title = Title(en='Funny Video')
    >>> description = Description(en="Description")
    >>> item = Item('it1', title, "movie", 2020, 120, 4.5, description, video)
    >>> item.id
    'it1'
    >>> item.title.en
    'Funny Video'
    >>> item.titleType
    'movie'
    >>> item.year
    2020
    >>> item.duration
    120
    >>> item.rating
    4.5
    >>> item.video
    Video(id='vid1', url='http://example.com/video1.mp4')
    """

    id: str
    title: Title
    titleType: Optional[str] = ""
    duration: Optional[int] = 0
    rating: Optional[Decimal] = Decimal("0.0")
    background_audio: Optional[str] = ""
    year: Optional[int] = 0
    description: Optional[Description] = None
    video: Optional[Video] = None

    def title_to_dir(self) -> str:
        return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', self.title.en).lower()

    def to_string(self):
        """
        >>> Item(
        ...    id="tt4154756", title=Title(en='Avengers: Infinity War'), titleType="movie", year=2018, duration=149, rating=8.4,
        ...    video=Video(id="vi2335949337", url='https://url')
        ... ).to_string()
        Title: Avengers: Infinity War
        Year: 2018
        Duration: 149 min
        IMDB: 8.4/10

        :return: str
        """
        return f"Title: {self.title.en}\nYear: {self.year}\nDuration: {self.duration} min\nIMDB: {self.rating}/10".replace(
            ":", "\\:")

    @classmethod
    async def delete_all_items(cls) -> None:
        """
        Deletes all items from a DynamoDB table using batch writes.

        :raises botocore.exceptions.ClientError: If any error occurs while deleting items.
        :return: None
        """
        session = aioboto3.Session()
        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(cls.table())
            scan = await table.scan()
            async with table.batch_writer() as batch:
                # Delete each item in a batch
                for each in scan['Items']:
                    await batch.delete_item(Key={"id": each['id']})

    @classmethod
    async def batch_get_item(cls, ids: List):
        session = aioboto3.Session()
        async with session.resource('dynamodb') as dynamo_resource:
            return await dynamo_resource.batch_get_item(RequestItems={
                cls.table(): {
                    "Keys": ids,
                }
            })


# Run the example
if __name__ == "__main__":
    from settings import HOST_API_URL

    print(HOST_API_URL)
    asyncio.run(Movie.get_by_id("tt31806037"))
