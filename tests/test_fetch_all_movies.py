from unittest.mock import patch, AsyncMock, MagicMock

from api.fetch_all_movies import FetchAllMovies
from tests.base import BaseTest


@patch('aioboto3.Session')
@patch('aiohttp.ClientSession')
class TestFetchAllMovies(BaseTest):
    async def test_fetch_all_movies_movie(self, *args):
        client_session, aioboto = args

        # Mock HTML file responses
        with open('movie.html', 'r') as file_movie:
            with open('serial.html', 'r') as file_serial:
                with open('imdb_results.html', 'r') as file_imdb_results:
                    # Setup mock HTTP response
                    mock_response = AsyncMock()
                    mock_response.status = 200

                    file_imdb_results_data = file_imdb_results.read()
                    mock_response.text = AsyncMock()
                    mock_response.text.side_effect = [
                        file_imdb_results_data,
                        file_imdb_results_data,
                        file_movie.read(),
                        file_serial.read(),
                    ]

                    client_session.return_value.__aenter__.return_value.get.return_value = mock_response

        # Create all the mocks we need
        mock_resource = AsyncMock()
        mock_table = AsyncMock()
        mock_batch_writer = AsyncMock()

        # Set up the resource mock
        aioboto.return_value.resource.return_value.__aenter__.return_value = mock_resource

        # Critical fix: Make Table() return a regular object, not a coroutine
        # The Table() function itself needs to be awaitable, but its return value shouldn't be
        mock_resource.Table = AsyncMock(return_value=mock_table)

        # Set up batch_writer to return a proper async context manager, not a coroutine
        mock_table.batch_writer = MagicMock(return_value=AsyncMock())
        mock_table.batch_writer.return_value.__aenter__ = AsyncMock(return_value=mock_batch_writer)
        mock_table.batch_writer.return_value.__aexit__ = AsyncMock(return_value=None)

        # Set up the put_item method
        mock_batch_writer.put_item = AsyncMock()

        # Mock first scan response (partial results)
        first_response = {
            'Items': [{'id': f"id-{i}"} for i in range(1, 6)],
            'LastEvaluatedKey': {'id': 'id-5'}
        }
        # Mock second scan response (remaining results)
        second_response = {
            'Items': [{'id': f"id-{i}"} for i in range(6, 11)],
        }
        mock_table.scan = AsyncMock()
        mock_table.scan.side_effect = [first_response, second_response]

        start_page = 1
        max_pages = 1
        batch_size = 1

        total_new_movies = await FetchAllMovies(
            start_page=start_page,
            max_pages=max_pages,
            batch_size=batch_size
        ).fetch_all_movies()
