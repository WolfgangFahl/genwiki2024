"""
Created on 2024-08-15

@author: wf
"""

import sys

from ngwidgets.cmd import WebserverCmd

from genwiki.webserver import GenWikiWebServer


class GenWikiCmd(WebserverCmd):
    """
    command line handling for genealogy wiki frontend
    """

    def add_arguments(self, parser):
        """
        Add genwiki-specific CLI arguments.

        Args:
            parser: The argument parser
        """
        super().add_arguments(parser)
        parser.add_argument(
            "--url_prefix",
            default="",
            help="URL prefix for proxied deployments (e.g., '/djvu-viewer')",
        )

    def __init__(self):
        """
        constructor
        """
        config = GenWikiWebServer.get_config()
        WebserverCmd.__init__(self, config, GenWikiWebServer, DEBUG)


def main(argv: list = None):
    """
    main call
    """
    cmd = GenWikiCmd()
    exit_code = cmd.cmd_main(argv)
    return exit_code


DEBUG = 0
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
