"""
Created on 2025-05-26

@author: wf

Load RDF dump files into dockerized Blazegraph.
"""

import argparse
import glob
import os
import time
from pathlib import Path

import requests
from ngwidgets.shell import Shell
from tqdm import tqdm


class BlazegraphLoader:
    """
    Manages dockerized Blazegraph and loads RDF dump files.
    """

    def __init__(self, container_name: str = "blazegraph", port: int = 9999):
        """
        Initialize the Blazegraph loader.

        Args:
            container_name: Docker container name
            port: Port for Blazegraph web interface
        """
        self.container_name = container_name
        self.port = port
        self.base_url = f"http://localhost:{port}/blazegraph"
        self.sparql_url = f"{self.base_url}/namespace/kb/sparql"

    def load_file(self, filepath: str) -> bool:
        """
        Load a single RDF file into Blazegraph.

        Args:
            filepath: Path to RDF file

        Returns:
            True if loaded successfully
        """
        try:
            with open(filepath, "rb") as f:
                response = requests.post(
                    self.sparql_url,
                    headers={"Content-Type": "text/turtle"},
                    data=f.read(),
                    timeout=300,
                )

            if response.status_code in [200, 204]:
                return True
            else:
                print(f"Error loading {filepath}: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"Exception loading {filepath}: {e}")
            return False

    def load_dump_files(self, file_pattern: str = "dump_*.ttl") -> int:
        """
        Load all dump files matching pattern.

        Args:
            file_pattern: Glob pattern for dump files

        Returns:
            Number of files loaded successfully
        """
        files = sorted(glob.glob(file_pattern))
        if not files:
            print(f"No files found matching pattern: {file_pattern}")
            return 0

        print(f"Found {len(files)} files to load")
        loaded_count = 0

        for filepath in tqdm(files, desc="Loading files"):
            if self.load_file(filepath):
                loaded_count += 1
            else:
                print(f"Failed to load: {filepath}")

        return loaded_count

    def count_triples(self) -> int:
        """
        Count total triples in Blazegraph.

        Returns:
            Number of triples
        """
        count_query = """
        SELECT (COUNT(*) AS ?count) WHERE {
            ?s ?p ?o
        }
        """

        try:
            response = requests.post(
                self.sparql_url,
                data={"query": count_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=30,
            )

            if response.status_code == 200:
                results = response.json()
                bindings = results.get("results", {}).get("bindings", [])
                if bindings:
                    count_value = bindings[0].get("count", {}).get("value", "0")
                    return int(count_value)

        except Exception as e:
            print(f"Error counting triples: {e}")

        return 0

    def test_geosparql(self) -> bool:
        """
        Test if GeoSPARQL functions work.

        Returns:
            True if GeoSPARQL is available
        """
        test_query = """
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX geof: <http://www.opengis.net/def/function/geosparql/>

        SELECT * WHERE {
            BIND(geof:distance("POINT(0 0)"^^geo:wktLiteral, "POINT(1 1)"^^geo:wktLiteral) AS ?dist)
        } LIMIT 1
        """

        try:
            response = requests.post(
                self.sparql_url,
                data={"query": test_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=10,
            )

            return response.status_code == 200

        except Exception:
            return False

    def stop_blazegraph(self):
        """
        Stop the Blazegraph container.
        """
        try:
            subprocess.run(["docker", "stop", self.container_name], check=True)
            print(f"Stopped container {self.container_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error stopping container: {e}")


def main():
    """
    Main function with argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="Load RDF dump files into dockerized Blazegraph"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="dump_*.ttl",
        help="File pattern for dump files (default: dump_*.ttl)",
    )

    parser.add_argument(
        "--container",
        type=str,
        default="blazegraph-gov",
        help="Docker container name (default: blazegraph-gov)",
    )

    parser.add_argument(
        "--port", type=int, default=9999, help="Port for Blazegraph (default: 9999)"
    )

    parser.add_argument(
        "--start-only",
        action="store_true",
        help="Only start Blazegraph, don't load data",
    )

    parser.add_argument("--stop", action="store_true", help="Stop Blazegraph container")

    args = parser.parse_args()

    loader = BlazegraphLoader(container_name=args.container, port=args.port)

    if args.stop:
        loader.stop_blazegraph()
        return

    # Start Blazegraph
    if not loader.start_blazegraph():
        print("Failed to start Blazegraph")
        return

    if args.start_only:
        print(f"Blazegraph started at {loader.base_url}")
        return

    # Load dump files
    print(f"Loading files matching: {args.pattern}")
    loaded_count = loader.load_dump_files(args.pattern)

    if loaded_count > 0:
        print(f"Successfully loaded {loaded_count} files")

        # Count triples
        triple_count = loader.count_triples()
        print(f"Total triples in database: {triple_count:,}")

        # Test GeoSPARQL
        if loader.test_geosparql():
            print("✅ GeoSPARQL functions available")
        else:
            print("❌ GeoSPARQL functions not available")

        print(f"Blazegraph interface: {loader.base_url}")
        print(f"SPARQL endpoint: {loader.sparql_url}")
    else:
        print("No files were loaded successfully")


if __name__ == "__main__":
    main()
