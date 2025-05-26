"""
Created on 2025-05-26

@author: wf

Download RDF dump via paginated CONSTRUCT queries.
"""

import argparse
import time

import requests
from tqdm import tqdm


class RdfDumpDownloader:
    """
    Downloads an RDF dump from a SPARQL endpoint via paginated CONSTRUCT queries.
    """

    def __init__(
        self,
        endpoint_url: str,
        limit: int = 10000,
        max_triples: int = 200000,
        show_progress: bool = True,
    ):
        """
        Initialize the RDF dump downloader.

        Args:
            endpoint_url: SPARQL endpoint URL
            limit: Number of triples per request
            max_triples: Maximum number of triples to download
            show_progress: Whether to show progress bar
        """
        self.endpoint_url = endpoint_url
        self.limit = limit
        self.max_triples = max_triples
        self.show_progress = show_progress
        self.headers = {"Accept": "text/turtle"}

    def construct_query(self, offset: int) -> str:
        """
        Create CONSTRUCT query with OFFSET and LIMIT.

        Args:
            offset: Query offset

        Returns:
            SPARQL CONSTRUCT query string
        """
        return f"""
        CONSTRUCT {{ ?s ?p ?o }}
        WHERE     {{ ?s ?p ?o }}
        OFFSET {offset}
        LIMIT {self.limit}
        """

    def fetch_chunk(self, offset: int) -> str:
        """
        Fetch a chunk of RDF data from the endpoint.

        Args:
            offset: Query offset

        Returns:
            RDF content as string

        Raises:
            Exception: If HTTP request fails
        """
        query = self.construct_query(offset)
        response = requests.post(
            self.endpoint_url,
            data={"query": query},
            headers=self.headers,
            timeout=60,
        )
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response.text.strip()

    def download(self) -> int:
        """
        Download the RDF dump in chunks.

        Returns:
            Number of chunks downloaded
        """
        total_chunks = self.max_triples // self.limit
        chunk_count = 0

        iterator = range(total_chunks)
        if self.show_progress:
            iterator = tqdm(iterator, desc="Downloading RDF dump")

        for chunk_idx in iterator:
            offset = chunk_idx * self.limit
            try:
                content = self.fetch_chunk(offset)
            except Exception as e:
                print(f"Error at offset {offset}: {e}")
                break

            if not content:
                print(f"Offset {offset}: Empty response → stopping.")
                break

            filename = f"dump_{offset:06d}.ttl"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            chunk_count += 1
            time.sleep(0.5)

        return chunk_count


def main():
    """
    Main function with argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="Download RDF dump from SPARQL endpoint via paginated CONSTRUCT queries"
    )

    parser.add_argument(
        "--url",
        type=str,
        default="https://gov-sparql.genealogy.net/dataset/sparql",
        help="SPARQL endpoint URL (default: gov.genealogy.net)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Number of triples per request (default: 10000)",
    )

    parser.add_argument(
        "--max-triples",
        type=int,
        default=200000,
        help="Maximum number of triples to download (default: 200000)",
    )

    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    args = parser.parse_args()

    downloader = RdfDumpDownloader(
        endpoint_url=args.url,
        limit=args.limit,
        max_triples=args.max_triples,
        show_progress=not args.no_progress,
    )

    print(f"Starting download from: {args.url}")
    print(f"Limit per request: {args.limit}")
    print(f"Max triples: {args.max_triples}")

    chunk_count = downloader.download()
    print(f"Download completed. Downloaded {chunk_count} chunks.")


if __name__ == "__main__":
    main()
