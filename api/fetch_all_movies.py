import asyncio
import json
import urllib.parse
from decimal import Decimal
from typing import List, Dict, Optional

from http_client import HttpClient
from models.video import Movie, Title


class ImdbGraphQLScraper:
    """
    Scrape IMDb using GraphQL API with async HttpClient and update existing records
    """
    host = "caching.graphql.imdb.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json'
    }

    def __init__(self, start_page: int = 1, max_pages: Optional[int] = None, batch_size: int = 5,
                 results_per_page: int = 50, update_existing: bool = True):
        """
        Initialize the IMDb GraphQL scraper

        Parameters:
        - start_page: Page to start fetching from (default: 1)
        - max_pages: Optional limit on number of pages to fetch (default: None, which means fetch all available pages)
        - batch_size: Number of pages to process in each batch
        - results_per_page: Number of results per page (default: 50)
        - update_existing: Whether to update existing movie records (default: True)
        """
        self.start_page = start_page
        self.max_pages = max_pages
        self.batch_size = batch_size
        self.results_per_page = results_per_page
        self.update_existing = update_existing

    def _generate_query_url(self, after_token: Optional[str] = None, first: int = 50,
                            language: str = "en-US", sort_by: str = "POPULARITY",
                            sort_order: str = "ASC") -> str:
        """
        Generate the GraphQL query URL with parameters

        Parameters:
        - after_token: Pagination token for next page
        - first: Number of results per page
        - language: Language code
        - sort_by: Sort field
        - sort_order: Sort direction

        Returns:
        - Full GraphQL query URL
        """
        variables = {
            "after": after_token,
            "first": first,
            "locale": language,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "titleTypeConstraint": {
                "anyTitleTypeIds": ["tvMovie", "tvMiniSeries", "tvEpisode", "tvSeries", "movie"],
                "excludeTitleTypeIds": []
            }
        }

        encoded_variables = urllib.parse.quote(json.dumps(variables))
        extensions = json.dumps({
            "persistedQuery": {
                "sha256Hash": "6842af47c3f1c43431ae23d394f3aa05ab840146b146a2666d4aa0dc346dc482",
                "version": 1
            }
        })

        return f"/?operationName=AdvancedTitleSearch&variables={encoded_variables}&extensions={urllib.parse.quote(extensions)}"

    def _extract_movie_data(self, data: Dict) -> List[Dict]:
        """
        Extract movie details from GraphQL response

        Parameters:
        - data: JSON response from GraphQL API

        Returns:
        - List of movie data dictionaries
        """
        movies_data = []

        edges = data.get("data", {}).get("advancedTitleSearch", {}).get("edges", [])

        for edge in edges:
            title_data = edge.get("node", {}).get("title", {})

            # Extract runtime in seconds
            runtime = Decimal("0.0")  # Default value
            runtime_data = title_data.get("runtime")
            if runtime_data is not None:
                runtime_seconds = runtime_data.get("seconds")
                if runtime_seconds is not None:
                    runtime = Decimal(str(runtime_seconds))

            # Extract release year and end year
            release_year_data = title_data.get("releaseYear", {})
            year = str(release_year_data.get("year", "")) if release_year_data else ""
            end_year = str(release_year_data.get("endYear", "")) if release_year_data else ""
            # If end_year is the same as year or empty, set it to empty
            if end_year == year:
                end_year = ""

            # Extract IMDb type
            imdb_type = title_data.get("titleType", {}).get("text", "movie")

            # Extract rating and votes
            rating = Decimal(str(title_data.get("ratingsSummary", {}).get("aggregateRating", 0) or 0))
            votes = title_data.get("ratingsSummary", {}).get("voteCount", 0)

            # Extract audience rating
            certificate = title_data.get("certificate", {})
            audience = certificate.get("rating", "") if certificate else ""

            # Extract genres
            title_genres = title_data.get("titleGenres", {})
            genres = [g["genre"]["text"] for g in
                      title_data.get("titleGenres", {}).get("genres", [])] if title_genres else []

            # Extract actors
            actors = []
            cast = title_data.get("principalCast", [])
            for cast_member in cast:
                for credit in cast_member.get("credits", []):
                    if credit.get("category", {}).get("text", "") == "actor":
                        name = credit.get("name", {}).get("nameText", {}).get("text", "")
                        if name:
                            actors.append(name)

            # Extract directors
            directors = []
            # Try extracting from principalCrew first
            crew = title_data.get("principalCrew", [])
            for category in crew:
                if category.get("category", {}).get("text", "") == "director":
                    for credit in category.get("credits", []):
                        name = credit.get("name", {}).get("nameText", {}).get("text", "")
                        if name:
                            directors.append(name)

            # Alternative method if principal crew doesn't have directors
            if not directors:
                crew_credits = title_data.get("credits", {}).get("crew", [])
                for credit in crew_credits:
                    if credit.get("category", {}).get("text", "") == "Director":
                        name = credit.get("name", {}).get("nameText", {}).get("text", "")
                        if name:
                            directors.append(name)

            # Another alternative using director field
            if not directors:
                director = title_data.get("director", {})
                if director:
                    name = director.get("name", {}).get("nameText", {}).get("text", "")
                    if name:
                        directors.append(name)

            # Extract production status
            production_status_data = title_data.get("productionStatus") or {}
            current_stage = production_status_data.get("currentProductionStage") or {}
            production_status = current_stage.get("id", "")

            # Extract overview/plot
            plot = title_data.get("plot", {}) or {}
            plot_text = plot.get("plotText", {}) or {}
            overview = plot_text.get("plainText", "") if plot_text else ""

            # Create movie data dictionary
            movie = {
                "id": title_data.get("id", ""),
                "title": title_data.get("titleText", {}).get("text", ""),
                "year": year,
                "end_year": end_year,
                "runtime": runtime,
                "imdb_type": imdb_type,
                "rating": rating,
                "votes": votes,
                "popularity": title_data.get("meterRanking", {}).get("currentRank", 0),
                "overview": overview,
                "genres": genres,
                "actors": actors,
                "directors": directors,
                "production_status": production_status,
                "audience": audience
            }

            movies_data.append(movie)

        return movies_data

    async def _fetch_page(self, after_token: Optional[str] = None) -> Dict:
        """
        Fetch a single page using HttpClient

        Parameters:
        - after_token: Pagination token

        Returns:
        - JSON response from GraphQL API
        """
        url = self._generate_query_url(after_token, first=self.results_per_page)
        client = HttpClient.from_dict({
            "server": self.host,
            "urls": [url],
            'headers': self.headers,
            'sleep': True,
            'json': True
        })

        result = await client.run()
        return result[0]

    async def _convert_to_movie_objects(self, movies_data: List[Dict]) -> List[Movie]:
        """
        Convert dictionaries to Movie objects

        Parameters:
        - movies_data: List of movie data dictionaries

        Returns:
        - List of Movie objects
        """
        movies = []

        for data in movies_data:
            movie = Movie(
                id=data["id"],
                title=Title(en=data["title"]),
                year=data["year"],
                genres=data["genres"],
                end_year=data["end_year"],
                directors=data["directors"],
                actors=data["actors"],
                popularity=data["popularity"],
                imdb_type=data["imdb_type"],
                rating=data["rating"],
                runtime=data["runtime"],
                votes=data["votes"],
                overview=data["overview"],
                audience=data["audience"],
                production_status=data["production_status"]
            )

            movies.append(movie)

        return movies

    async def _get_existing_movie(self, movie_id: str) -> Optional[Movie]:
        """
        Get an existing movie from DynamoDB by ID

        Parameters:
        - movie_id: The IMDb ID of the movie

        Returns:
        - Movie object if found, None otherwise
        """
        movie_data = await Movie.get_by_id(movie_id)
        if not movie_data:
            return None

        # Convert dictionary to Movie object
        return Movie.from_dict(movie_data)

    async def _should_update_movie(self, existing_movie: Movie, new_movie_data: Dict) -> bool:
        """
        Determine if the existing movie should be updated based on changes

        Parameters:
        - existing_movie: Existing Movie object from database
        - new_movie_data: New movie data from API

        Returns:
        - True if movie should be updated, False otherwise
        """
        # Compare important fields to see if an update is needed
        if (existing_movie.rating != Decimal(str(new_movie_data["rating"])) or
                existing_movie.votes != new_movie_data["votes"] or
                existing_movie.popularity != new_movie_data["popularity"] or
                existing_movie.production_status != new_movie_data["production_status"] or
                existing_movie.overview != new_movie_data["overview"] or
                set(existing_movie.genres) != set(new_movie_data["genres"]) or
                set(existing_movie.directors) != set(new_movie_data["directors"]) or
                set(existing_movie.actors) != set(new_movie_data["actors"])):
            return True

        return False

    async def _process_and_save_page(self, page_data: Dict, existing_ids: set, current_page: int) -> Dict:
        """
        Process and save a single page of movies

        Parameters:
        - page_data: Raw page data from GraphQL API
        - existing_ids: Set of existing movie IDs
        - current_page: Current page number for logging

        Returns:
        - Dictionary with counts of new and updated movies
        """
        # Extract movie data
        movies_data = self._extract_movie_data(page_data)

        # Initialize counters
        new_movie_data = []
        updated_movie_data = []
        existing_movie_ids = []
        updated_ids = []

        # Process each movie
        for movie in movies_data:
            movie_id = movie["id"]

            if movie_id in existing_ids:
                existing_movie_ids.append(movie_id)

                if self.update_existing:
                    # Get existing movie
                    existing_movie = await self._get_existing_movie(movie_id)

                    if existing_movie and await self._should_update_movie(existing_movie, movie):
                        updated_movie_data.append(movie)
                        updated_ids.append(movie_id)
            else:
                new_movie_data.append(movie)
                existing_ids.add(movie_id)

        print(
            f"Processed page {current_page} - Found {len(movies_data)} movies, {len(new_movie_data)} new, {len(updated_movie_data)} to update")

        results = {
            "new": 0,
            "updated": 0
        }

        # Process new movies
        if new_movie_data:
            try:
                # Convert to Movie objects and save
                new_movie_objects = await self._convert_to_movie_objects(new_movie_data)
                await Movie.save(new_movie_objects)
                print(f"Saved {len(new_movie_objects)} new movies from page {current_page}")
                results["new"] = len(new_movie_objects)
            except Exception as e:
                print(f"Error saving new movies from page {current_page}: {e}")

        # Process updated movies
        if updated_movie_data:
            try:
                # Convert to Movie objects and save (will overwrite existing)
                updated_movie_objects = await self._convert_to_movie_objects(updated_movie_data)
                await Movie.save(updated_movie_objects)
                print(f"Updated {len(updated_movie_objects)} existing movies from page {current_page}")
                results["updated"] = len(updated_movie_objects)
            except Exception as e:
                print(f"Error updating movies from page {current_page}: {e}")

        return results

    async def fetch_all_movies(self) -> Dict:
        """
        Fetch all movies using pagination, saving and updating each page individually
        Will continue until all pages are fetched or max_pages limit is reached

        Returns:
        - Dictionary with counts of total new and updated movies
        """
        results = {
            "total_new": 0,
            "total_updated": 0,
            "pages_processed": 0
        }

        after_token = None  # First page has no token
        has_next_page = True

        # Get existing movie IDs
        existing_ids = set()
        try:
            all_movies = await Movie.scan_all()
            existing_ids = {movie.id for movie in all_movies}
            print(f"Found {len(existing_ids)} existing movies in the database")
        except Exception as e:
            print(f"Error getting existing movies: {e}")
            print("Continuing with empty existing IDs set")

        # Skip to start page if needed
        if self.start_page > 1:
            print(f"Skipping to page {self.start_page}...")
            current_page = 1

            while current_page < self.start_page and has_next_page:
                try:
                    data = await self._fetch_page(after_token)

                    # Get next page token
                    page_info = data.get("data", {}).get("advancedTitleSearch", {}).get("pageInfo", {})
                    has_next_page = page_info.get("hasNextPage", False)
                    after_token = page_info.get("endCursor")

                    if not has_next_page:
                        print(
                            f"Reached end of results at page {current_page}, unable to start at page {self.start_page}")
                        return results

                    print(f"Skipped page {current_page}")
                    current_page += 1

                except Exception as e:
                    print(f"Error skipping to page {current_page}: {e}")
                    return results

            print(f"Starting from page {self.start_page}")
        else:
            current_page = 1

        # Process all available pages or up to max_pages
        while has_next_page:
            try:
                # Check if we've reached max_pages
                if self.max_pages is not None and results["pages_processed"] >= self.max_pages:
                    print(f"Reached max_pages limit ({self.max_pages})")
                    break

                # Fetch current page
                data = await self._fetch_page(after_token)

                # Process and save this page
                page_results = await self._process_and_save_page(data, existing_ids, current_page)
                results["total_new"] += page_results["new"]
                results["total_updated"] += page_results["updated"]
                results["pages_processed"] += 1

                # Check for next page
                page_info = data.get("data", {}).get("advancedTitleSearch", {}).get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                after_token = page_info.get("endCursor")

                if not has_next_page:
                    print("Reached end of all available results.")
                    break

                current_page += 1

            except Exception as e:
                print(f"Error processing page {current_page}: {e}")
                # Try to continue with the next page if possible
                if after_token:
                    current_page += 1
                    continue
                else:
                    break

        print(f"Total pages processed: {results['pages_processed']}")
        print(f"Total new movies added: {results['total_new']}")
        print(f"Total movies updated: {results['total_updated']}")
        return results


# Example usage
if __name__ == "__main__":
    async def run():
        # To get all available pages, set max_pages to None
        # To limit to a specific number of pages, set max_pages to that number
        scraper = ImdbGraphQLScraper(
            start_page=1,  # Which page to start on
            max_pages=None,  # How many pages to process (None = all)
            batch_size=1,  # How many pages to process in one batch
            update_existing=True  # Whether to update existing movie records
        )
        total_movies = await scraper.fetch_all_movies()
        print(f"Total new movies added: {total_movies}")


    # Run the
    asyncio.run(run())
