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


class MixinDynamoTable:
    @classmethod
    def table(cls):
        return cls.__name__.lower()

    @classmethod
    async def save(cls, items: List):
        session = aioboto3.Session()
        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(cls.table())

            async with table.batch_writer() as batch:
                for item in items:
                    await batch.put_item(Item=item.to_dict())

    @classmethod
    async def get_existing_ids(cls) -> Set[str]:
        """Get all existing IDs from the DynamoDB table"""
        existing_ids = set()
        session = aioboto3.Session()

        async with session.resource('dynamodb') as dynamo_resource:
            table = await dynamo_resource.Table(cls.table())

            # Scan the table to get all IDs
            response = await table.scan(ProjectionExpression="id")
            for item in response.get('Items', []):
                existing_ids.add(item['id'])

            # Handle pagination for large tables
            while 'LastEvaluatedKey' in response:
                response = await table.scan(
                    ProjectionExpression="id",
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for item in response.get('Items', []):
                    existing_ids.add(item['id'])

        return existing_ids


@dataclass
class Movie(MixinDynamoTable, DataClassJSONSerializer):
    id: str
    title: Title
    year: str
    genres: List[str]
    type: str
    popularity: int
    rating: Decimal
    runtime: Decimal
    votes: int
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
