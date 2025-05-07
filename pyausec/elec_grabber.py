"""Grabber for the Aus Election Dashboard."""

import contextlib
import platform
from ftplib import FTP
from pathlib import Path
from zipfile import ZipFile

from .constants import FTP_URL
from .logger import get_logger

logger = get_logger(__name__)


class AusElectionGrabber:
    """Grabs data from the AEC FTP server."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialise the AusElectionGrabber.

        Args:
            cache_dir (Path): Path to the instance directory.
        """
        if cache_dir is None:
            cache_dir = self._get_default_cache_dir()

        self.cache_dir = cache_dir
        self.ftp_tree: dict[str, dict] = {}
        self.grab()
        elections = list(self.ftp_tree.keys())
        if len(elections) != 1:
            msg = "There should only be one election in the FTP tree, you haven't accounted for this"
            raise ValueError(msg)
        self.election_root = elections[0]
        logger.info("Election root: %s", self.election_root)

        self.election_preload_file = None
        self.populate_election()
        self.populate_candidates()
        self.get_latest_results()

    def _get_default_cache_dir(self) -> Path:
        """Get the default cache directory for your platform."""
        if platform.system() == "Windows":
            return Path("~\\AppData\\Local\\pyausec").expanduser()

        return Path("~/.cache/pyausec").expanduser()

    # region: Preload
    def get_preload(self) -> None:
        """Get the preload file from the FTP server."""
        election_dict = self.ftp_tree[self.election_root]
        preload_dir = election_dict["Detailed"]["Preload"]
        file_list = list(preload_dir.keys())
        if len(file_list) != 1:
            msg = "There should only be one file in the candidates directory, you haven't accounted for this"
            raise ValueError(msg)

        ftp_srv_src_dir = f"/{self.election_root}/Detailed/Preload"
        self.download_file(file_dir=ftp_srv_src_dir, file_name=file_list[0])
        self.election_preload = self.cache_dir / file_list[0]

    def populate_election(self) -> None:
        """Populate election."""
        if not self.election_preload_file:
            self.get_preload()

        election_info_content = self._get_file_as_str_from_zip(
            self.election_preload, f"xml/eml-110-event-{self.election_root}.xml"
        )

    def populate_candidates(self) -> None:
        """Populate candidates."""
        if not self.election_preload_file:
            self.get_preload()

        candidate_info_content = self._get_file_as_str_from_zip(
            self.election_preload, f"xml/eml-230-candidates-{self.election_root}.xml"
        )

    # endregion

    # region: Results
    def get_latest_results(self) -> None:
        """Get the latest results from the FTP server."""
        election_dict = self.ftp_tree[self.election_root]
        results_dir = election_dict["Standard"]["Light"]

        results_file_list = list(results_dir.keys())
        results_file_list.sort()
        latest_file = results_file_list[-1]
        logger.info("Latest results file: %s", latest_file)  # Thank you AEC for the naming convention

        ftp_srv_src_dir = f"/{self.election_root}/Standard/Light"

        self.download_file(file_dir=ftp_srv_src_dir, file_name=latest_file)

        zip_file_path = self.cache_dir / latest_file
        print(zip_file_path)

        latest_results_content = self._get_file_as_str_from_zip(
            zip_file_path,
            f"xml/aec-mediafeed-results-standard-light-{self.election_root}.xml",
        )

    # endregion

    # region: Helper methods
    def _get_file_as_str_from_zip(self, zip_file_path: str, file_in_zip_path_str: str) -> str:
        """Get a file as a string from a zip file."""
        zip_file = ZipFile(zip_file_path, mode="r")
        with zip_file as zip_file:
            # List all files in the zip file
            logger.trace("Files in zip file: %s", zip_file.namelist())
            return zip_file.read(file_in_zip_path_str).decode("utf-8")

    def download_file(self, file_dir: str, file_name: str) -> None:
        """Download a file from the FTP server."""
        logger.info("Downloading file: %s from %s", file_name, file_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.cache_dir / file_name

        if output_file.exists():
            logger.info("File already exists, skipping download.")
            return

        with contextlib.closing(FTP(FTP_URL)) as ftp:
            ftp.login()
            ftp.cwd(file_dir)

            with output_file.open("wb") as local_file:
                ftp.retrbinary(f"RETR {file_name}", local_file.write)

    def grab(self) -> None:
        """Grab the data from the AEC FTP server."""
        files = self._get_ftp_file_list()
        self.ftp_tree = self._create_ftp_tree_from_list(files)

    def _create_ftp_tree_from_list(self, files: list[str]) -> dict[str, dict]:
        """Create a tree from the list of files on the FTP server.

        Args:
            files (list[str]): List of file paths from the FTP server

        Returns:
            dict: A nested dictionary representing the directory structure
        """
        tree: dict[str, dict | None] = {}

        for file_path in files:
            # Skip empty paths
            if not file_path:
                continue

            # Split path into components
            parts = file_path.strip("/").split("/")

            # Navigate the tree, creating branches as needed
            current: dict[str, dict | None] = tree
            for part in parts[:-1]:  # Process directories
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Handle the leaf (file)s
            leaf = parts[-1]
            if "." in leaf:  # It's a file
                current[leaf] = None  # Files are leaf nodes
            elif leaf not in current:
                current[leaf] = {}

        if not tree:
            msg = "No files found in the FTP directory."
            raise ValueError(msg)

        return tree

    def _get_ftp_file_list(self) -> list[str]:
        """Recursively get the list of files on the FTP server.

        Returns:
            list[str]: List of files on the FTP server.
        """
        logger.info("Connecting to FTP server.")
        with FTP(FTP_URL) as ftp:
            ftp.login()

            def _recurse_get_paths(path: str) -> list[str]:
                """Recursively get the list of files on the FTP server.

                Args:
                    path (str): Path to the directory on the FTP server.

                Returns:
                    list[str]: List of files in the directory.
                """
                found = []

                ftp.cwd(path)

                directories = ftp.nlst()

                for directory in directories:
                    full_path = f"{path}/{directory}"
                    found.append(full_path)

                    if "." not in directory:  # Fun hack to check if it is a file
                        found.extend(_recurse_get_paths(full_path))

                return found

            return _recurse_get_paths("")

    # endregion
