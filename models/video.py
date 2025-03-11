import re
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

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


@dataclass
class Item(DataClassJSONSerializer):
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
    titleType: str
    year: int
    duration: int
    rating: Decimal
    background_audio: str
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
