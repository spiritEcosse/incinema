from unittest.mock import AsyncMock, call

from asynctest import TestCase, MagicMock, patch

from main import handler
from settings import STATE_MACHINE_ARN, HOST_API_TOKEN, HOST_API_URL, AWS_DEFAULT_REGION


@patch('boto3.client')
@patch('aioboto3.Session')
@patch('aiohttp.ClientSession')
class TestHandler(TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.item_id_1 = "tt4154756"
        self.item_id_2 = "tt0050825"
        self.item_id_3 = "tt15325794"
        self.item_id_4 = "tt1668746"
        self.string = f"Suspense, Survey .1.\n1.Вышка | {self.item_id_1} \n2.Джунгли | {self.item_id_2} \n3.Новое | {self.item_id_3}\n4.The Kingsroad | {self.item_id_4}\n"

    def test_success(self, *args):
        client_session, aioboto, boto = args
        self.video_id_1 = "vi2335949337"
        self.video_id_2 = "vi2335949338"

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
                    side_effect=[json_get_meta_data, json_get_videos, json_get_videos_2, json_get_playback, json_get_playback_2]
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
            **{"resource.return_value": MagicMock(
                **{"__aenter__.return_value": MagicMock(**{"Table.side_effect": AsyncMock(
                    side_effect=[table]
                )}, **{"batch_get_item.side_effect": AsyncMock(
                    side_effect=[{'Responses': {'item': [{'id': self.item_id_3}]}}, None]
                )}
                )}
            )}
        )

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
            call().resource('dynamodb', region_name=AWS_DEFAULT_REGION),
            call().resource().__aenter__(),
            call().resource().__aenter__().batch_get_item(
                RequestItems={'item': {
                    'Keys': [
                        {'id': self.item_id_1}, {'id': self.item_id_2}, {"id": self.item_id_3}, {'id': self.item_id_4}
                    ], "ProjectionExpression": "id"}
                }),
            call().resource().__aexit__(None, None, None),
            call(),
            call().resource('dynamodb', region_name=AWS_DEFAULT_REGION),
            call().resource().__aenter__(),
            call().resource().__aenter__().Table('item'),
            call().resource().__aexit__(None, None, None)
        ])
        self.assertListEqual(
            table.mock_calls, [
                call.batch_writer(),
                call.batch_writer().__aenter__(),
                call.batch_writer().__aenter__().put_item(
                    Item={'id': self.item_id_1, 'title': 'Avengers: Infinity War', 'titleType': 'movie', 'year': 2018, 'duration': 149,
                          'rating': '8.4', 'video': {'id': 'vi2335949337', 'url': 'https://url'}}),
                call.batch_writer().__aenter__().put_item(
                    Item={'id': self.item_id_2, 'title': 'Avengers: Infinity War 2', 'titleType': 'movie', 'year': 2019, 'duration': 169,
                          'rating': '9.4', 'video': {'id': 'vi2335949338', 'url': 'https://url'}}),
                call.batch_writer().__aenter__().put_item(
                    Item={'id': self.item_id_4, 'title': 'The Kingsroad', 'titleType': 'tvEpisode', 'year': 2011,
                          'duration': 56, 'rating': '9.4', 'video': None}),
                call.batch_writer().__aexit__(None, None, None)
            ]
        )

        self.assertListEqual(
            boto.mock_calls, [
                call('stepfunctions'),
                call().start_execution(stateMachineArn=STATE_MACHINE_ARN, input='{"id": "tt4154756"}'),
                call().start_execution(stateMachineArn=STATE_MACHINE_ARN, input='{"id": "tt0050825"}'),
                call().start_execution(stateMachineArn=STATE_MACHINE_ARN, input='{"id": "tt1668746"}')
            ]
        )
