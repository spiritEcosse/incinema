from _decimal import Decimal
from dataclasses import dataclass
from typing import List

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
    url: str = ""

    @classmethod
    def _post_deserialize_id(cls, obj):
        """
        >>> Video._post_deserialize_id(Video(id="vi2335949337"))
        >>> Video._post_deserialize_id(Video("string"))
        Traceback (most recent call last):
        AssertionError: Not starting with vi
        """
        assert obj.id.startswith('vi'), "Not starting with vi"


@dataclass
class Item(DataClassJSONSerializer):
    """A class representing an item

    >>> video = Video('vid1', 'http://example.com/video1.mp4')
    >>> item = Item('it1', 'Funny Video', "movie", 2020, 120, 4.5, video)
    >>> item.id
    'it1'
    >>> item.title
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
    title: str
    titleType: str
    year: int
    duration: int
    rating: Decimal
    video: Video = None

    def to_string(self):
        """
        >>> Item(
        ...    id="tt4154756", title='Avengers: Infinity War', titleType="movie", year=2018, duration=149, rating=8.4,
        ...    video=Video(id="vi2335949337", url='https://url')
        ... ).to_string()
        Назва\: Avengers: Infinity War
        Рік\: 2018
        Тривалість\: 149 хв
        Рейтинг IMDB\: 8.4/10

        :return: str
        """
        print(f"Назва\: {self.title}\nРік\: {self.year}\nТривалість\: {self.duration} хв\nРейтинг IMDB\: {self.rating}/10")

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
                cls.table():  {
                    "Keys": ids,
                    "ProjectionExpression": "id"
                }
            })
