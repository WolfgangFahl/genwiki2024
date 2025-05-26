"""
Created on 2025-05-26

@author: wf
"""

import re
import time

import requests
from ngwidgets.persistent_log import Log
from ngwidgets.shell import Shell
from tqdm import tqdm
from lodstorage.sparql import SPARQL

class Blazegraph:
    """
    dockerized blazegraph
    """

    def __init__(
        self,
        container_name: str = "blazegraph",
        image: str = "lyrasis/blazegraph:2.1.5",
        port: int = 9999,
        log: Log = None,
        shell: Shell = None,
        debug: bool = False,
    ):
        """
        Initialize the Blazegraph manager.

        Args:
            container_name: Docker container name
            port: Port for Blazegraph web interface
        """
        if log is None:
            log = Log()
        self.log = log
        self.container_name = container_name
        self.image = image
        self.port = port
        self.base_url = f"http://localhost:{port}/bigdata"
        self.status_url = f"{self.base_url}/status"
        self.sparql_url = f"{self.base_url}/namespace/kb/sparql"
        self.sparql = SPARQL(self.sparql_url)
        if shell is None:
            shell = Shell()
        self.shell = shell
        self.debug = debug

    def start(self, show_progress: bool = True) -> bool:
        """
        Start Blazegraph in Docker container.

        Returns:
            True if started successfully
        """
        try:
            if self.is_running():
                self.log.log(
                    "✅",
                    "blazegraph",
                    f"Container {self.container_name} is already running",
                )
            elif self.exists():
                self.log.log(
                    "✅",
                    "blazegraph",
                    f"Container {self.container_name} exists, starting...",
                )
                start_cmd = f"docker start {self.container_name}"
                start_result = self.shell.run(start_cmd, debug=self.debug)
                if start_result.returncode != 0:
                    self.log.log(
                        "❌",
                        "blazegraph",
                        f"Failed to start container {self.container_name}",
                    )
                    return False
            else:
                self.log.log(
                    "✅",
                    "blazegraph",
                    f"Creating new Blazegraph container {self.container_name}...",
                )
                create_cmd = f"docker run -d --name {self.container_name} -p {self.port}:9999 {self.image}"
                create_result = self.shell.run(create_cmd, debug=self.debug)
                if create_result.returncode != 0:
                    self.log.log(
                        "❌",
                        "blazegraph",
                        f"Failed to create container {self.container_name}",
                    )
                    return False

            ok = self.wait_until_ready(show_progress=show_progress)
            return ok

        except Exception as e:
            self.log.log("❌", "blazegraph", f"Error starting Blazegraph: {e}")
            return False

    def count_triples(self) -> int:
        """
        Count total triples in Blazegraph.

        Returns:
            Number of triples
        """
        count_query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
        result = self.sparql.getValue(count_query, "count")
        count = int(result) if result else 0
        return count

    def status(self) -> dict:
        """
        Get Blazegraph status information.

        Returns:
            Dictionary with status information, empty dict if error
        """
        status_dict = {}
        try:
            response = requests.get(f"{self.status_url}", timeout=2)
            if response.status_code == 200:
                status_dict["status"] = "ready"
                html_content = response.text
                # uncomment to debug
                # status_dict["html"]= html_content
                name_value_pattern = r'(?:<span id="(?P<name1>[^"]+)">(?P<value1>[^<]+)</span[^>]*>|&#47;(?P<name2>[^=]+)=(?P<value2>[^\s&#]+))'
                matches = re.finditer(name_value_pattern, html_content, re.DOTALL)
                for match in matches:
                    for name_group, value_group in {
                        "name1": "value1",
                        "name2": "value2",
                    }.items():
                        name = match.group(name_group)
                        if name:
                            value = match.group(value_group)
                            sanitized_value = value.replace("</p", "").replace(
                                "&#47;", "/"
                            )
                            sanitized_name = name.replace("-", "_").replace("/", "_")
                            sanitized_name = sanitized_name.replace("&#47;", "/")
                            if not sanitized_name.startswith("/"):
                                status_dict[sanitized_name] = sanitized_value
                            break
            else:
                status_dict["status"] = f"status_code: {response.status_code}"
        except Exception as e:
            status_dict["status"] = f"error: {str(e)}"
        return status_dict

    def wait_until_ready(self, timeout: int = 30, show_progress: bool = False) -> bool:
        """
        Wait for Blazegraph to be ready.

        Args:
            timeout: Maximum seconds to wait
            show_progress: Show progress bar while waiting

        Returns:
            True if ready within timeout
        """

        self.log.log(
            "✅", "blazegraph", f"Waiting for Blazegraph to start ... {self.status_url}"
        )

        if show_progress:
            pbar = tqdm(total=timeout, desc="Waiting for Blazegraph", unit="s")

        for _i in range(timeout):
            try:
                status = self.status()
                if status.get("status") == "ready":
                    if show_progress:
                        pbar.close()
                    self.log.log(
                        "✅", "blazegraph", f"Blazegraph ready at {self.base_url}"
                    )
                    return True
            except requests.exceptions.RequestException:
                pass

            if show_progress:
                pbar.update(1)
            time.sleep(1)

        if show_progress:
            pbar.close()

        self.log.log(
            "⚠️",
            "blazegraph",
            f"Timeout waiting for Blazegraph to start after {timeout}s",
        )
        return False

    def is_running(self) -> bool:
        """
        Check if container is currently running.

        Returns:
            True if container is running
        """
        running_cmd = (
            f'docker ps --filter "name={self.container_name}" --format "{{{{.Names}}}}"'
        )
        running_result = self.shell.run(running_cmd, debug=self.debug)
        return self.container_name in running_result.stdout

    def exists(self) -> bool:
        """
        Check if container exists (running or stopped).

        Returns:
            True if container exists
        """
        check_cmd = f'docker ps -a --filter "name={self.container_name}" --format "{{{{.Names}}}}"'
        result = self.shell.run(check_cmd, debug=self.debug)
        if result.stderr:
            self.log.log("❌", "blazegraph", result.stderr)
        return self.container_name in result.stdout

    def stop(self) -> bool:
        """
        Stop the Blazegraph container.

        Returns:
            True if stopped successfully
        """
        try:
            stop_cmd = f"docker stop {self.container_name}"
            result = self.shell.run(stop_cmd, debug=self.debug)
            if result.returncode == 0:
                self.log.log(
                    "✅", "blazegraph", f"Stopped container {self.container_name}"
                )
                return True
            else:
                self.log.log(
                    "❌", "blazegraph", f"Failed to stop container: {result.stderr}"
                )
                return False
        except Exception as e:
            self.log.log("❌", "blazegraph", f"Error stopping container: {e}")
            return False
