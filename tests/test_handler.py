from unittest.mock import call, patch, AsyncMock

from main import handler
from settings import HOST_API_TOKEN, HOST_API_URL
from tests.base import BaseTest


@patch('boto3.client')
@patch('aioboto3.Session')
@patch('aiohttp.ClientSession')
class TestHandler(BaseTest):
    maxDiff = None

    def setUp(self) -> None:
        self.item_id_1 = "tt1860357"
        self.item_id_2 = "tt3758172"
        self.item_id_3 = "tt13223398"
        self.item_id_4 = "tt6805938"
        self.data = {
            "title": "Survival",
            "items": [
                {
                    "description": "A gripping retelling of the 2010 oil rig disaster, focusing on the heroic efforts of workers to survive the catastrophic explosion and ensuing oil spill.",
                    "title": "Deepwater Horizon",
                    "id": self.item_id_1
                }, {
                    "description": "A group of friends trek through the Amazon jungle, facing dangerous wildlife and life-threatening situations, testing their limits and survival instincts.",
                    "title": "Jungle",
                    "id": self.item_id_2
                },
                # {
                #     "description": "Idris Elba stars as a father fighting to protect his daughters from a relentless lion in South Africa's wilderness, blending action with survival.",
                #     "title": "Beast",
                #     "id": self.item_id_3
                # },
                {
                    "description": "After witnessing a murder, a woman finds herself on a cliff ledge, facing life-or-death decisions while being hunted by her attackers in a deadly game.",
                    "title": "The Ledge",
                    "id": self.item_id_4
                }
            ]
        }

    async def test_success(self, *args):
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

        client_session.return_value = AsyncMock(
            **{"__aenter__.return_value.get.return_value":
                   AsyncMock(**{"__aenter__.return_value.json.side_effect": AsyncMock(
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

        table = AsyncMock(
            **{"batch_writer.return_value": AsyncMock(
                **{"__aenter__.return_value.put_item.side_effect": AsyncMock(
                    side_effect=[None, None, None]
                )}
            )}
        )
        # aioboto.return_value = AsyncMock(
        #     **{"resource.return_value": AsyncMock(
        #         **{"__aenter__.return_value": AsyncMock(**{"Table.side_effect": AsyncMock(
        #             side_effect=[table]
        #         )}, **{"batch_get_item.side_effect": AsyncMock(
        #             side_effect=[{'Responses': {'item': [{'id': self.item_id_3}]}}, None]
        #         )})}
        #     )}
        # )

        await handler(self.data)

        self.assertListEqual(client_session.mock_calls, [
            call(f'https://{HOST_API_URL}', headers={
                'X-RapidAPI-Key': HOST_API_TOKEN,
                'X-RapidAPI-Host': HOST_API_URL
            }),
            call().__aenter__(),
            call().__aenter__().get(
                f'/title/get-meta-data?ids={self.item_id_1}&ids={self.item_id_2}&ids={self.item_id_4}'),
            call().__aenter__().get().json(),
            call().__aexit__(None, None, None),
            call().__aenter__().get().json().items(),
            call().__aenter__().get().json().items().__iter__(),
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

        # self.assertListEqual(aioboto.mock_calls, [
        #     call(),
        #     call().resource('dynamodb'),
        #     call().resource().__aenter__(),
        #     call().resource().__aenter__().batch_get_item(
        #         RequestItems={'item': {
        #             'Keys': [
        #                 {'id': self.item_id_1}, {'id': self.item_id_2}, {"id": self.item_id_3}, {'id': self.item_id_4}
        #             ], "ProjectionExpression": "id"}
        #         }),
        #     call().resource().__aexit__(None, None, None),
        #     call(),
        #     call().resource('dynamodb'),
        #     call().resource().__aenter__(),
        #     call().resource().__aenter__().Table('item'),
        #     call().resource().__aexit__(None, None, None)
        # ])
        # self.assertListEqual(
        #     table.mock_calls, [
        #         call.batch_writer(),
        #         call.batch_writer().__aenter__(),
        #         call.batch_writer().__aenter__().put_item(
        #             Item={'id': self.item_id_1, 'title': 'Avengers: Infinity War', 'titleType': 'movie', 'year': 2018,
        #                   'duration': 149,
        #                   'rating': '8.4', 'video': {'id': 'vi2335949337', 'url': 'https://url'}}),
        #         call.batch_writer().__aenter__().put_item(
        #             Item={'id': self.item_id_2, 'title': 'Avengers: Infinity War 2', 'titleType': 'movie', 'year': 2019,
        #                   'duration': 169,
        #                   'rating': '9.4', 'video': {'id': 'vi2335949338', 'url': 'https://url'}}),
        #         call.batch_writer().__aenter__().put_item(
        #             Item={'id': self.item_id_4, 'title': 'The Kingsroad', 'titleType': 'tvEpisode', 'year': 2011,
        #                   'duration': 56, 'rating': '9.4', 'video': None}),
        #         call.batch_writer().__aexit__(None, None, None)
        #     ]
        # )
