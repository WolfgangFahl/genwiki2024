#!/usr/bin/env python3
"""
Filesystem content Indexer with RDFLib and SPARQL Endpoint.
"""

import argparse
import logging
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from tqdm import tqdm
import uvicorn
from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef
from rdflib_endpoint import SparqlEndpoint

# Configuration & Namespaces
FS = Namespace("http://bitplan.com/filesystem#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FileSystemRDF:
    """
    file system as RDF representation
    """

    def __init__(self):
        self.g = Graph()
        self.g.bind("fs", FS)
        self.g.bind("dcterms", DCTERMS)

    def scan_directory(self, path: str,show_progress=False):
        """
        Walks directory, creates triples, adds to graph.
        Equivalent to the 'find' command in the bash script.
        """
        abs_path = os.path.abspath(path)
        logger.info(f"Scanning directory: {abs_path}")

        count = 0
        try:
            total_files = 0
            if show_progress:
                for _, _, files in os.walk(abs_path):
                    total_files += len(files)
            pbar = tqdm(total=total_files, disable=not show_progress, unit="file", desc="Indexing")
            for root, _, files in os.walk(abs_path):
                for name in files:
                    full_path = os.path.join(root, name)
                    try:
                        stats = os.stat(full_path)
                        self._add_file_to_graph(full_path, stats)
                        count += 1
                        if show_progress:
                            pbar.update(1)
                        else:
                            if count % 1000 == 0:
                                print(f"Processed {count} files...", end="\r")

                    except Exception as e:
                        logger.error(f"Error reading {full_path}: {e}")
            pbar.close()
        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user.")

        logger.info(f"Scan complete. Total files: {count}")

    def _add_file_to_graph(self, path: str, stats: os.stat_result):
        """Generates triples for a single file"""
        # Create a URI. Using file protocol or a URN
        # We enforce URL encoding to handle spaces/special chars in paths
        safe_path = urllib.parse.quote(path)
        file_uri = URIRef(f"file://{safe_path}")

        # Add Type
        self.g.add((file_uri, RDF.type, FS.File))

        # Add Properties
        self.g.add((file_uri, FS.path, Literal(path, datatype=XSD.string)))
        self.g.add((file_uri, FS.size, Literal(stats.st_size, datatype=XSD.integer)))

        # Timestamps
        mtime_iso = datetime.fromtimestamp(stats.st_mtime, timezone.utc).isoformat()
        self.g.add(
            (file_uri, DCTERMS.modified, Literal(mtime_iso, datatype=XSD.dateTime))
        )

        # User/Group (Unix specific)
        try:
            # We store IDs to avoid getpwuid overhead on millions of files,
            # but you can convert if needed.
            self.g.add((file_uri, FS.uid, Literal(stats.st_uid, datatype=XSD.integer)))
            self.g.add((file_uri, FS.gid, Literal(stats.st_gid, datatype=XSD.integer)))
            self.g.add(
                (
                    file_uri,
                    FS.mode,
                    Literal(oct(stats.st_mode)[-3:], datatype=XSD.string),
                )
            )
        except AttributeError:
            pass  # Windows compatibility

    def save_ttl(self, filename: str):
        """Save graph to Turtle file"""
        logger.info(f"Saving {len(self.g)} triples to {filename}...")
        self.g.serialize(destination=filename, format="turtle")
        logger.info("Save successful.")

    def load_ttl(self, filename: str):
        """Load graph from Turtle file"""
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            return
        logger.info(f"Loading triples from {filename}...")
        self.g.parse(filename, format="turtle")
        logger.info(f"Loaded {len(self.g)} triples.")

    def run_server(self, host="0.0.0.0", port=8000):
        """Start the SPARQL Endpoint"""
        logger.info(f"Starting SPARQL endpoint on {host}:{port}")

        endpoint = SparqlEndpoint(
            graph=self.g,
            path="/",
            cors_enabled=True,
            title="FileSystem Content Index",
            description="SPARQL endpoint for file system metadata",
            version="1.0.0",
            example_query="""PREFIX fs: <http://bitplan.com/filesystem#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?path ?size ?date WHERE {
    ?file a fs:File ;
          fs:path ?path ;
          fs:size ?size ;
          dcterms:modified ?date .
    FILTER(?size > 1000000)
} LIMIT 20""",
        )

        # Note: uvicorn arguments must be handled carefully when invoked programmatically
        uvicorn.run(endpoint, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="RDF File System Indexer")

    parser.add_argument("--scan", help="Directory directory to scan (replaces -dir)")
    parser.add_argument("--store", help="File path to save Turtle (.ttl) output")
    parser.add_argument("--load", help="File path to load Turtle (.ttl) input")
    parser.add_argument(
        "--serve", action="store_true", help="Start generic SPARQL endpoint"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for web server")
    parser.add_argument("--progress", action="store_true", help="Show progress bar")

    args = parser.parse_args()

    fs_rdf = FileSystemRDF()

    # 1. Load existing data if requested
    if args.load:
        fs_rdf.load_ttl(args.load)

    # 2. Scan directory (Add to graph)
    if args.scan:
        fs_rdf.scan_directory(args.scan, show_progress=args.progress)

    # 3. Store results if requested
    if args.store:
        fs_rdf.save_ttl(args.store)

    # 4. Serve
    if args.serve:
        if len(fs_rdf.g) == 0:
            logger.warning("Graph is empty. Did you forget to --scan or --load?")
        fs_rdf.run_server(port=args.port)


if __name__ == "__main__":
    main()
