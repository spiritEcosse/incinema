import re
from decimal import Decimal
from typing import Optional, Dict, List

import math
from bs4 import BeautifulSoup

from http_client import HttpClient
from models.video import Movie, Title


class FetchAllMovies:
    # url = "search/title/?title_type=feature&sort=moviemeter,asc&start={}&ref_=adv_nxt"
    url = "search/title/?title_type=tv_movie,tv_miniseries,tv_episode,tv_series,feature&sort=moviemeter,asc&start={}&ref_=adv_nxt"
    host = "www.imdb.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'}
    pages_selector = "#__next > main > div.ipc-page-content-container.ipc-page-content-container--center.sc-b8fa3fca-0.jxQzGK > div.ipc-page-content-container.ipc-page-content-container--center > section > section > div > section > section > div:nth-child(2) > div > section > div.ipc-page-grid.ipc-page-grid--bias-left.ipc-page-grid__item.ipc-page-grid__item--span-2 > div.ipc-page-grid__item.ipc-page-grid__item--span-2 > div.sc-13add9d7-6.dCCeCI > div.sc-13add9d7-3.fwjHEn"
    items_selector = "#__next > main > div.ipc-page-content-container.ipc-page-content-container--center.sc-b8fa3fca-0.jxQzGK > div.ipc-page-content-container.ipc-page-content-container--center > section > section > div > section > section > div:nth-child(2) > div > section > div.ipc-page-grid.ipc-page-grid--bias-left.ipc-page-grid__item.ipc-page-grid__item--span-2 > div.ipc-page-grid__item.ipc-page-grid__item--span-2 > ul"
    link_movie = "a.ipc-title-link-wrapper"
    metadata_selector = "#__next > main > div > section.ipc-page-background.ipc-page-background--base.sc-75c84411-0.icfMdl > section > div:nth-child(5) > section > section > div.sc-9a2a0028-3.bwWOiy"
    genres_selector = "#__next > main > div > section.ipc-page-background.ipc-page-background--base.sc-75c84411-0.icfMdl > section > div:nth-child(5) > section > section > div.sc-9a2a0028-4.eeUUGv > div.sc-9a2a0028-6.zHrZh > div.sc-9a2a0028-10.iUfJXd > section > div.ipc-chip-list--baseAlt.ipc-chip-list.ipc-chip-list--nowrap.sc-42125d72-4.iPHzA-d > div.ipc-chip-list__scroller"
    actors_selector = ".ipc-sub-grid.ipc-sub-grid--page-span-2.ipc-sub-grid--wraps-at-above-l.ipc-shoveler__grid"
    directors_selector = "#__next > main > div > section.ipc-page-background.ipc-page-background--base.sc-75c84411-0.icfMdl > section > div:nth-child(5) > section > section > div.sc-9a2a0028-4.eeUUGv > div.sc-9a2a0028-6.zHrZh > div.sc-9a2a0028-10.iUfJXd > section > div.sc-70a366cc-3.iwmAOx > div > ul > li:nth-child(1) > div > ul"
    overview_selector = "#__next > main > div > section.ipc-page-background.ipc-page-background--base.sc-75c84411-0.icfMdl > section > div:nth-child(5) > section > section > div.sc-9a2a0028-4.eeUUGv > div.sc-9a2a0028-6.zHrZh > div.sc-9a2a0028-10.iUfJXd > section > p"

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

    def get_overview(self, soup) -> str:
        """
        Extract the movie/series overview from the page

        Parameters:
        - soup: BeautifulSoup object of the movie page

        Returns:
        - str: Overview text
        """
        # Try to find the overview in the metadata section using your selector
        metadata_div = soup.select_one(self.overview_selector)
        if metadata_div:
            overview_element = metadata_div.select_one('span[data-testid="plot-xl"]')
            if overview_element:
                return overview_element.text.strip()

        # Fallback to other common selectors
        overview_element = soup.select_one('span[data-testid="plot-xl"]')
        if overview_element:
            return overview_element.text.strip()

        # Another fallback
        overview_element = soup.select_one('div.sc-9a2a0028-3.bwWOiy span.sc-466bb6c-0')
        if overview_element:
            return overview_element.text.strip()

        return ""

    def get_genres(self, soup) -> list:
        """
        Extract the genres for the movie/series

        Parameters:
        - soup: BeautifulSoup object of the movie page

        Returns:
        - list: List of genre strings
        """
        div = soup.select_one(self.genres_selector)
        genre_elements = div.select('a.ipc-chip--on-baseAlt')
        genres = [genre.text.strip() for genre in genre_elements]
        if not genres:
            raise ValueError("No genres found")
        return genres

    def get_actors(self, soup) -> list:
        """
        Extract the main actors from the movie/series page

        Parameters:
        - soup: BeautifulSoup object of the movie page

        Returns:
        - list: List of actor names
        """
        div = soup.select_one(self.actors_selector)
        elements = div.select('a[data-testid="title-cast-item__actor"]')
        actors = [re.sub(r'\s+', ' ', element.text.replace('\n', '').strip()) for element in elements]
        if not actors:
            raise ValueError("No actors found")
        return actors

    def get_directors(self, soup) -> list:
        """
        Extract the directors from the movie/series page

        Parameters:
        - soup: BeautifulSoup object of the movie page

        Returns:
        - list: List of director names
        """
        div = soup.select_one(self.directors_selector)
        elements = div.select('a.ipc-metadata-list-item__list-content-item')
        directors = [re.sub(r'\s+', ' ', element.text.replace('\n', '').strip()) for element in elements]
        if not directors:
            raise ValueError("No directors found")
        return directors

    def _get_title(self, soup):
        title_element = soup.select_one('h1[data-testid="hero__pageTitle"]')
        title = title_element.text.strip()
        if not title:
            raise ValueError("No title found")
        return title

    def _get_popularity(self, soup):
        popularity_element = soup.select_one('div[data-testid="hero-rating-bar__popularity__score"]')
        popularity = int(popularity_element.text.strip().replace(',', ''))
        return popularity

    def get_runtime(self, runtime_text):
        # Process runtime
        runtime = Decimal("0.0")  # Default value
        if runtime_text:
            # Handle formats like "2h 17m"
            hours, minutes = 0, 0
            if 'h' in runtime_text:
                hours_parts = runtime_text.split('h')
                hours = int(hours_parts[0].strip())
                if 'm' in hours_parts[1]:
                    minutes = int(hours_parts[1].split('m')[0].strip())
            elif 'm' in runtime_text:
                minutes = int(runtime_text.split('m')[0].strip())

            # Convert to total minutes
            runtime = Decimal(str(hours * 60 + minutes))
        return runtime

    def get_year(self, year):
        end_year = ""

        # Handle series with date ranges
        if '–' in year or '-' in year:
            separator = '–' if '–' in year else '-'
            date_parts = year.split(separator)
            start_year = date_parts[0].strip()
            end_year = date_parts[1].strip() if len(date_parts) > 1 and date_parts[1].strip() else ""
            year = start_year
        return end_year, year

    def get_rating(self, soup):
        # Extract rating and votes (unchanged from your original code)
        # Extract rating
        rating_span = soup.select_one('span.sc-d541859f-1')
        if rating_span:
            rating = Decimal(rating_span.text.strip())
        else:
            rating = Decimal('0.0')

        # Extract votes
        votes_span = soup.select_one('div.sc-d541859f-3')
        if not votes_span:
            return rating, 0

        # Clean up the votes text
        votes_text = votes_span.text.strip()
        votes_text = votes_text.replace('(', '').replace(')', '')
        votes_text = votes_text.replace('\xa0', '').replace(',', '')

        # Handle different vote formats
        if 'M' in votes_text:
            # Convert millions (e.g., "1.2M" to 1200000)
            votes = int(float(votes_text.replace('M', '')) * 1000000)
        elif 'K' in votes_text:
            # Convert thousands (e.g., "247K" to 247000)
            votes = int(float(votes_text.replace('K', '')) * 1000)
        else:
            # Handle plain numbers, ensuring we're not trying to convert a rating
            if '.' in votes_text:
                # If it looks like a rating (has decimal), it's probably wrong data
                raise ValueError(f"Unexpected decimal in votes count: {votes_text}")
            votes = int(votes_text)

        return rating, votes

    def get_metadata(self, soup):
        """
        Extract all metadata from a movie page including title, year, runtime, end_year, rating, votes,
        popularity, imdb_type, and audience rating

        Parameters:
        - soup: BeautifulSoup object of the movie page

        Returns:
        - tuple: (title, year, runtime, end_year, rating, votes, popularity, imdb_type, audience)
        """
        # Initialize variables
        year = ""
        runtime = Decimal("0.0")
        end_year = ""
        audience = ""
        imdb_type = "movie"

        # Extract title
        title = self._get_title(soup)
        popularity = self._get_popularity(soup)
        serial = False

        # Get basic metadata from the metadata section - updated selector for the new HTML structure
        metadata_list = soup.select_one(self.metadata_selector)

        list_items = metadata_list.select('li.ipc-inline-list__item')

        for item in list_items:
            item_text = item.text.strip()

            # Check for TV Series/Movie identifier
            if item_text in ["TV Series", "TV Mini Series", "TV Movie", "Episode", "TV Episode"]:
                imdb_type = item_text.replace(" ", "")
                serial = True
                continue

            # Check for year with link
            year_link = item.select_one('a[href*="releaseinfo"]')
            if year_link:
                end_year, year = self.get_year(year_link.text.strip())
                continue

            # Check for runtime (doesn't have a link)
            if 'h' in item_text or 'm' in item_text:
                runtime = self.get_runtime(item_text)
                continue

            if serial:
                # Check for audience rating with link to parental guide
                audience_link = item.select_one('a[href*="parentalguide"]')
                if audience_link:
                    audience = audience_link.text.strip()
                    continue

        rating, votes = self.get_rating(soup)
        return title, year, runtime, end_year, rating, votes, popularity, imdb_type, audience

    async def fetch_movie_details(self, movie_urls: List[str]) -> List[Movie]:
        """
        Fetch detailed information about movies from their URLs

        Parameters:
        - movie_urls: List of movie URLs

        Returns:
        - List of Movie objects
        """

        # Create client for this batch
        client = HttpClient.from_dict({
            "server": self.host,
            "urls": movie_urls,
            'headers': self.headers,
            'sleep': True,
            'json': False
        })

        # Make all requests
        pages_data = await client.run()

        # Process each movie page
        movies = []
        for i, page_data in enumerate(pages_data):
            movie_url = movie_urls[i]
            movie_id = movie_url.split('/')[2]
            try:
                # Parse HTML
                soup = BeautifulSoup(page_data, 'html.parser')

                # Get metadata
                title, year, runtime, end_year, rating, votes, popularity, imdb_type, audience = self.get_metadata(soup)

                # Get additional details
                overview = self.get_overview(soup)
                genres = self.get_genres(soup)
                actors = self.get_actors(soup)
                directors = self.get_directors(soup)

                # Create Movie object
                movie = Movie(
                    id=movie_id,
                    title=Title(en=title),
                    year=year,
                    genres=genres,
                    end_year=end_year,
                    directors=directors,
                    actors=actors,
                    popularity=popularity,
                    imdb_type=imdb_type,
                    rating=rating,
                    runtime=runtime,
                    votes=votes,
                    overview=overview,
                    audience=audience
                )

                movies.append(movie)
            except Exception as e:
                print(f"Error processing movie page: {e}, movie_id: {movie_id}")
                raise e

        return movies

    async def _collect_movies_urls(self, page_data: str, existing_ids: set) -> List[str]:
        """
        Process a page of search results and extract movie URLs

        Parameters:
        - page_data: Raw HTML data from the search results page
        - existing_ids: Set of existing movie IDs to avoid duplicates

        Returns:
        - List of movie URLs that haven't been processed yet
        """
        new_movie_urls = []

        try:
            # Parse HTML
            soup = BeautifulSoup(page_data, 'html.parser')

            # Find movie items
            movie_elements = soup.select_one(self.items_selector)

            for movie in movie_elements.select('li'):
                try:
                    # Extract movie link
                    link_element = movie.select_one(self.link_movie)
                    if not link_element:
                        continue

                    movie_url = link_element.get('href', '')
                    if not movie_url or not movie_url.startswith('/title/'):
                        raise ValueError(f"Invalid movie URL: {movie}")

                    # Get movie ID
                    movie_id = movie_url.split('/')[2]

                    # Skip if we already have this movie
                    if movie_id in existing_ids:
                        continue

                    # Add to new movie URLs list
                    new_movie_urls.append(movie_url)

                except Exception as e:
                    print(f"Error extracting movie URL: {movie}")
                    raise e

        except Exception as e:
            print(f"Error processing page: {e}")
            raise e

        return new_movie_urls

    async def _get_total_pages(self) -> int:
        """Get the total number of pages available"""
        # Create a client for the first page request
        client = HttpClient.from_dict(
            {"server": self.host, "urls": [self.url.format(1)], 'headers': self.headers, 'sleep': True,
             'json': False}
        )

        # Make the request
        results = await client.run()
        soup = BeautifulSoup(results[0], "html.parser")

        # Find total results www.imdb.com
        total_results_text = soup.select_one(self.pages_selector).text  # Example: "1-50 of 3,456"

        # Extract total results using regex
        match = re.search(r'of ([0-9,]+)', total_results_text)
        if match:
            total_results = int(match.group(1).replace(',', ''))
            results_per_page = 50  # IMDb usually shows 50 results per page
            total_pages = math.ceil(total_results / results_per_page)
            print(f"Total Titles: {total_results}")
            print(f"Total Pages: {total_pages}")
        else:
            raise RuntimeError(f"Unable to parse total results from {total_results_text}")
        return total_pages

    async def _fetch_pages_batch(self, page_numbers: List[int]) -> List[Dict]:
        """Fetch a batch of pages using HttpClient"""
        # Construct URLs for all pages in this batch
        # IMDb uses a different pagination style - each page shows 50 results
        urls = [self.url.format((page - 1) * 50 + 1) for page in page_numbers]

        # Create client for this batch
        client = HttpClient.from_dict(
            {"server": self.host, "urls": urls, 'headers': self.headers, 'sleep': True, 'json': False})

        # Make all requests
        return await client.run()

    async def fetch_all_movies(self) -> int:
        """
        Fetch all movies using pagination, saving each batch to database

        Returns:
        - Total number of new movies saved
        """
        total_new_movies = 0

        # Get existing movie IDs to avoid duplicates
        existing_ids = await Movie.get_existing_ids()
        print(f"Found {len(existing_ids)} existing movies in the database")

        # Get total pages
        total_pages = await self._get_total_pages()

        # Determine end page
        end_page = min(total_pages, self.start_page + self.max_pages - 1) if self.max_pages else total_pages

        # Adjust start page if it's out of range
        if self.start_page > total_pages:
            print(f"Start page {self.start_page} exceeds total pages {total_pages}. Exiting.")
            return 0

        print(f"Will process pages {self.start_page} through {end_page}")

        # Process pages in batches
        all_new_movie_urls = []

        for batch_start in range(self.start_page, end_page + 1, self.batch_size):
            batch_end = min(batch_start + self.batch_size - 1, end_page)
            page_numbers = list(range(batch_start, batch_end + 1))

            print(f"Fetching pages {batch_start} to {batch_end}...")

            # Fetch batch of pages
            pages_data = await self._fetch_pages_batch(page_numbers)

            # Process each page in the batch to extract movie URLs
            for i, page_data in enumerate(pages_data):
                page_num = page_numbers[i]
                new_movie_urls = await self._collect_movies_urls(page_data, existing_ids)
                all_new_movie_urls.extend(new_movie_urls)

                print(f"Processed page {page_num}/{total_pages} - Found {len(new_movie_urls)} new movies")

        # Now fetch details for all new movies in batches
        movie_batch_size = 10  # Process movies in smaller batches
        for i in range(0, len(all_new_movie_urls), movie_batch_size):
            batch_urls = all_new_movie_urls[i:i + movie_batch_size]
            print(f"Fetching details for movies {i + 1}-{i + len(batch_urls)} of {len(all_new_movie_urls)}")

            # Fetch details for this batch
            new_movies = await self.fetch_movie_details(batch_urls)
            await Movie.save(new_movies)
            total_new_movies += len(new_movies)

        return total_new_movies
