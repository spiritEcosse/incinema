from decimal import Decimal
from typing import Optional, Dict, Set, List

from box import Box

from http_client import HttpClient
from models.video import Movie, Title


class FetchAllMovies:
    url = "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&start={}&ref_=adv_nxt"

    def __init__(self, start_page: int = 1, max_pages: Optional[int] = None, batch_size: int = 10):
        """
        Initialize the FetchAllMovies class with pagination parameters

        Parameters:
        - start_page: Page to start fetching from (default: 1)
        - max_pages: Optional limit on number of pages to fetch
        - batch_size: Number of pages to process in each batch
        """
        self.start_page = start_page
        self.max_pages = max_pages
        self.batch_size = batch_size

    def _convert_movie(self, movie_data: Box) -> Movie:
        # Convert genre_ids to genre names using the mapping
        genre_names = [GENRE_MAP.get(genre_id, f"Unknown-{genre_id}") for genre_id in movie_data.genre_ids]

        return Movie(
            id=str(movie_data.id),
            title=Title(en=movie_data.title),
            type="movie",
            release_date=movie_data.release_date,
            genres=genre_names,
            vote_average=Decimal(str(movie_data.vote_average)),
            vote_count=Decimal(str(movie_data.vote_count)),
            popularity=Decimal(str(movie_data.popularity)),
            overview=movie_data.overview,
            video=None,
            description=None
        )

    async def _get_total_pages(self) -> int:
        """Get the total number of pages available in the API"""
        # Create a client for the first page request
        client = HttpClient.from_dict(
            {"urls": [self.url.format(1)]}
        )

        # Make the request
        results = await client.run()
        first_page_data = results[0]  # Get the first (and only) result

        return first_page_data["total_pages"]

    async def _process_and_save_page(self, page_data: Box, existing_ids: Set[str]) -> List[Movie]:
        """Process a page of movie data and return new movies not already in the database"""
        new_movies = []

        for movie_data in page_data.results:
            movie_id = str(movie_data.id)

            # Skip movies that already exist in the database
            if movie_id in existing_ids:
                continue

            # Convert and add new movies
            movie = self._convert_movie(movie_data)
            new_movies.append(movie)

        # If there are new movies, save them to DynamoDB
        if new_movies:
            await Movie.save(new_movies)

        return new_movies

    async def _fetch_pages_batch(self, page_numbers: List[int]) -> List[Dict]:
        """Fetch a batch of pages using HttpClient"""
        # Construct URLs for all pages in this batch
        urls = [self.url.format(page) for page in page_numbers]

        # Create client for this batch
        client = HttpClient.from_dict({"urls": urls})

        # Make all requests
        return await client.run()

    async def fetch_all_movies(self) -> int:
        """
        Fetch all movies using pagination, saving each batch to DynamoDB

        Returns:
        - Total number of new movies saved
        """
        total_new_movies = 0

        # Get existing movie IDs from DynamoDB to avoid duplicates
        existing_ids = await Movie.get_existing_ids()
        print(f"Found {len(existing_ids)} existing movies in the database")

        # Get total pages from the API
        total_pages = await self._get_total_pages()
        print(f"Total available pages: {total_pages}")

        # Determine end page
        end_page = min(total_pages, self.start_page + self.max_pages - 1) if self.max_pages else total_pages

        # Adjust start page if it's out of range
        if self.start_page > total_pages:
            print(f"Start page {self.start_page} exceeds total pages {total_pages}. Exiting.")
            return 0

        print(f"Will process pages {self.start_page} through {end_page}")

        # Process pages in batches
        for batch_start in range(self.start_page, end_page + 1, self.batch_size):
            batch_end = min(batch_start + self.batch_size - 1, end_page)
            page_numbers = list(range(batch_start, batch_end + 1))

            print(f"Fetching pages {batch_start} to {batch_end}...")

            # Fetch batch of pages
            pages_data = await self._fetch_pages_batch(page_numbers)

            # Process each page in the batch
            for i, page_data in enumerate(pages_data):
                # ids = [str(_page['id']) for _page in page_data['results']]
                # print(f"Page: {page_data['page']}, ids: {", ".join(ids)}")
                page_num = page_numbers[i]
                new_movies = await self._process_and_save_page(Box(page_data), existing_ids)
                total_new_movies += len(new_movies)

                # Add new movie IDs to existing_ids set
                for movie in new_movies:
                    existing_ids.add(movie.id)

                print(f"Processed page {page_num}/{total_pages} - Added {len(new_movies)} new movies")

        return total_new_movies
