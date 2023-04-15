import os
from pathlib import Path
from unittest.mock import AsyncMock, call

from asynctest import TestCase, MagicMock, patch

from main import handler
from settings import HOST_API_TOKEN, HOST_API_URL, BUCKET_VIDEO
from unittest.mock import patch, mock_open

opener = mock_open()


@patch('api.video_editor.glob')
@patch('api.video_editor.AudioAPI')
@patch('api.get_meta_data.Pool')
@patch('api.get_meta_data.subprocess')
@patch('boto3.client')
@patch('aioboto3.Session')
@patch('aiohttp.ClientSession')
class TestHandler(TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.item_id_1 = "tt4154756"
        self.item_id_2 = "tt0050825"
        self.item_id_3 = "tt15325794"
        self.title_3 = "Fall_test"
        self.item_id_4 = "tt1668746"
        self.string = f"Suspense, Survey .1.#1.Вышка | {self.item_id_1} | background_audio | Text#2.Джунгли | {self.item_id_2} | background_audio | Text#3.Новое | {self.item_id_3} | background_audio | Text#4.The Kingsroad | {self.item_id_4} | background_audio | Text"
        self.video_id_1 = "vi2335949337"
        self.video_id_2 = "vi2335949338"
        self.video_id_3 = "vi2335949334"
        self.url_3 = f"https://www.imdb.com/video/{self.video_id_3}"

    def mocked_open(self, *args, **kwargs):
        return opener(self, *args, **kwargs)

    def test_success(self, *args):
        os.environ["DETECT_SCENES"] = "True"
        client_session, aioboto, boto, subprocess, Pool, glob, AudioAPI = args
        json_get_meta_data = {
            self.item_id_1: {
                "title":
                {
                    "id": f"/title/{self.item_id_1}/",
                    "runningTimeInMinutes": 149,
                    "title": "Avengers: Infinity War",
                    "titleType": "movie",
                    "year": 2018
                },
                "ratings":
                {
                    "id": f"/title/{self.item_id_1}/",
                    "rating": 8.4,
                }
            },
            self.item_id_2: {
                "title":
                {
                    "id": f"/title/{self.item_id_2}/",
                    "runningTimeInMinutes": 169,
                    "title": "Avengers: Infinity War 2",
                    "titleType": "movie",
                    "year": 2019
                },
                "ratings":
                {
                    "id": f"/title/{self.item_id_2}/",
                    "rating": 9.4,
                }
            },
            self.item_id_4: {
                "title":
                {
                    "id": f"/title/{self.item_id_4}/",
                    "runningTimeInMinutes": 56,
                    "title": "The Kingsroad",
                    "titleType": "tvEpisode",
                    "year": 2011
                },
                "ratings":
                {
                    "id": f"/title/{self.item_id_4}/",
                    "rating": 9.4,
                }
            },
        }
        json_get_videos = {
            "resource": {
                "videos": [
                    {
                        "id": f"/videoV2/{self.video_id_1}"
                    }
                ]
            }
        }
        json_get_videos_2 = {
            "resource": {
                "videos": [
                    {
                        "id": f"/videoV2/{self.video_id_2}"
                    }
                ]
            }
        }
        json_get_playback = {
            "resource": {
                "encodings": [
                    {
                        "mimeType": 'other',
                        "definition": '1080p',
                        "playUrl": 'https://url/other',
                    },
                    {
                        "mimeType": 'video/mp4',
                        "definition": '1080p',
                        "playUrl": 'https://url',
                    },
                ]
            }
        }
        json_get_playback_2 = {
            "resource": {
                "encodings": [
                    {
                        "mimeType": 'video/mp4',
                        "definition": '720p',
                        "playUrl": 'https://url',
                    }
                ]
            }
        }

        client_session.return_value = MagicMock(
            **{"__aenter__.return_value.get.return_value":
                MagicMock(**{"__aenter__.return_value.json.side_effect": AsyncMock(
                    side_effect=[
                        json_get_meta_data,
                        json_get_videos,
                        json_get_videos_2,
                        json_get_playback,
                        json_get_playback_2
                    ]
                )})
            }
        )

        table = MagicMock(
            **{"batch_writer.return_value": MagicMock(
                **{"__aenter__.return_value.put_item.side_effect": AsyncMock(
                    side_effect=[None, None, None]
                )}
            )}
        )
        aioboto.return_value = MagicMock(
            **{"client.return_value": AsyncMock(

            )},
            **{"resource.return_value": MagicMock(
                **{"__aenter__.return_value": MagicMock(**{"Table.side_effect": AsyncMock(
                    side_effect=[table]
                )}, **{"batch_get_item.side_effect": AsyncMock(
                    side_effect=[{'Responses': {'item': [
                        {
                            'id': self.item_id_3,
                            "title": {
                                "ru": self.title_3,
                                "en": "En version",
                            },
                            "background_audio": "background_audio",
                            "titleType": "movie",
                            "year": 2016,
                            "duration": 180,
                            "rating": 5.6,
                            "description": {
                                "ru": "Текст"
                            },
                            "video": {
                                "id": self.video_id_3,
                                "url": self.url_3
                            }
                        }
                    ]}}, None]
                )}
                )}
            )}
        )

        with patch.object(Path, 'open', opener):
            handler({"body": self.string}, {})

        self.assertListEqual(client_session.mock_calls, [
            call(f'https://{HOST_API_URL}', headers={
                'X-RapidAPI-Key': HOST_API_TOKEN,
                'X-RapidAPI-Host': HOST_API_URL
            }),
            call().__aenter__(),
            call().__aenter__().get(f'/title/get-meta-data?ids={self.item_id_1}&ids={self.item_id_2}&ids={self.item_id_4}'),
            call().__aenter__().get().__aenter__(),
            call().__aenter__().get().__aenter__().json(),
            call().__aenter__().get().__aexit__(None, None, None),
            call().__aexit__(None, None, None),
            call(f'https://{HOST_API_URL}', headers={
                'X-RapidAPI-Key': HOST_API_TOKEN,
                'X-RapidAPI-Host': HOST_API_URL
            }),
            call().__aenter__(),
            call().__aenter__().get(f'/title/get-videos?tconst={self.item_id_1}'),
            call().__aenter__().get().__aenter__(),
            call().__aenter__().get().__aenter__().json(),
            call().__aenter__().get().__aexit__(None, None, None),
            call().__aenter__().get(f'/title/get-videos?tconst={self.item_id_2}'),
            call().__aenter__().get().__aenter__(),
            call().__aenter__().get().__aenter__().json(),
            call().__aenter__().get().__aexit__(None, None, None),
            call().__aexit__(None, None, None),
            call(f'https://{HOST_API_URL}', headers={
                'X-RapidAPI-Key': HOST_API_TOKEN,
                'X-RapidAPI-Host': HOST_API_URL
            }),
            call().__aenter__(),
            call().__aenter__().get(f'/title/get-video-playback?viconst={self.video_id_1}'),
            call().__aenter__().get().__aenter__(),
            call().__aenter__().get().__aenter__().json(),
            call().__aenter__().get().__aexit__(None, None, None),
            call().__aenter__().get(f'/title/get-video-playback?viconst={self.video_id_2}'),
            call().__aenter__().get().__aenter__(),
            call().__aenter__().get().__aenter__().json(),
            call().__aenter__().get().__aexit__(None, None, None),
            call().__aexit__(None, None, None),
        ])

        self.assertListEqual(aioboto.mock_calls, [
            call(),
            call().resource('dynamodb'),
            call().resource().__aenter__(),
            call().resource().__aenter__().batch_get_item(
                RequestItems={'item': {
                    'Keys': [
                        {'id': self.item_id_1}, {'id': self.item_id_2}, {"id": self.item_id_3}, {'id': self.item_id_4}
                    ]}
                }),
            call().resource().__aexit__(None, None, None),
            call(),
            call().resource('dynamodb'),
            call().resource().__aenter__(),
            call().resource().__aenter__().Table('item'),
            call().resource().__aexit__(None, None, None)
        ])
        self.assertListEqual(
            table.mock_calls, [
                call.batch_writer(),
                call.batch_writer().__aenter__(),
                call.batch_writer().__aenter__().put_item(
                    Item={'id': self.item_id_1, 'title': {"ru": "Вышка", "en": 'Avengers: Infinity War'}, 'titleType': 'movie', 'background_audio': 'background_audio', 'year': 2018, 'duration': 149,
                          'rating': '8.4', 'description': {"ru": "Text"}, 'video': {'id': 'vi2335949337', 'url': 'https://url'}}),
                call.batch_writer().__aenter__().put_item(
                    Item={'id': self.item_id_2, 'title': {"ru": "Джунгли", "en": 'Avengers: Infinity War 2'}, 'titleType': 'movie', 'background_audio': 'background_audio', 'year': 2019, 'duration': 169,
                          'rating': '9.4', 'description': {"ru": "Text"}, 'video': {'id': 'vi2335949338', 'url': 'https://url'}}),
                call.batch_writer().__aexit__(None, None, None)
            ]
        )
