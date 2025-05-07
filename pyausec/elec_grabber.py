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

    def __init__(self, cache_dir: Path | None = None, current_election: str | None = None) -> None:
        """Initialise the AusElectionGrabber.

        Args:
            cache_dir (Path): Path to the cache directory, where the zips will be stored.
            current_election (str): The current election (number) to grab data for.
                If None, will grab the only election.
        """
        if cache_dir is None:
            cache_dir = self._get_default_cache_dir()
        self.cache_dir = cache_dir

        self.ftp_listing: list[str] = []
        self.refresh_ftp_file_list()

        self.election_root = self.get_election(current_election)

        self.tracked_files: dict[str, Path] = {}

        self.election_preload_file = None

        self.populate_election()
        self.populate_candidates()
        self.get_latest_results()

    def _get_default_cache_dir(self) -> Path:
        """Get the default cache directory for your platform."""
        if platform.system() == "Windows":
            return Path("~\\AppData\\Local\\pyausec").expanduser()

        return Path("~/.cache/pyausec").expanduser()

    def get_election(self, override: str | None) -> str:
        """Get the current election number from the FTP listing."""
        logger.debug("Getting election number from FTP listing.")
        election_list_scratch = [file.split("/")[1] for file in self.ftp_listing]
        election_list_scratch_set = set(election_list_scratch)

        if len(election_list_scratch_set) == 0:
            msg = "No elections found in the FTP listing."
            raise ValueError(msg)
        if not override and len(election_list_scratch_set) > 1:
            msg = "Multiple elections found in the FTP listing, please specify an override."
            raise ValueError(msg)
        if override:
            if override not in election_list_scratch_set:
                msg = f"Override election {override} not found in the FTP listing."
                raise ValueError(msg)
            logger.info("Override election found: %s", override)
            return override

        election: str = election_list_scratch_set.pop()
        logger.info("Election found: %s", election)
        return election

    # region: Preload
    def _get_latest_ftp_file_from_path(self, path: str, file_role: str, file_extension: str) -> Path:
        """Get the latest file, from a folder in the FTP server."""
        logger.debug("Getting latest %s file from path: %s for %s", file_extension, path, file_role)

        file_shortlist = [file for file in self.ftp_listing if path in file and file.endswith(file_extension)]

        if len(file_shortlist) == 0:
            msg = f"No preload files found in {file_shortlist}."
            raise ValueError(msg)
        if len(file_shortlist) > 1 and file_role == "preload":
            msg = f"Invalid number of preload files found: {len(file_shortlist)}, expected 1."
            logger.warning(msg)

        file_shortlist.sort()

        preload_file_full_path = file_shortlist[-1]
        preload_file: str = preload_file_full_path.split("/")[-1]

        self.download_file(file_dir=path, file_name=preload_file, file_role=file_role)
        return self.tracked_files[file_role]

    def get_preload(self) -> Path:
        """Get the preload file from the FTP server if needed."""
        return self._get_latest_ftp_file_from_path(
            path=f"/{self.election_root}/Detailed/Preload",
            file_role="preload",
            file_extension=".zip",
        )

    def populate_election(self) -> None:
        """Populate election."""
        preload_path = self.get_preload()

        election_info_content = self._get_file_as_str_from_zip(
            preload_path, f"xml/eml-110-event-{self.election_root}.xml"
        )

    def populate_candidates(self) -> None:
        """Populate candidates."""
        preload_path = self.get_preload()
        logger.debug("Populating candidates.")

        candidate_info_content = self._get_file_as_str_from_zip(
            preload_path, f"xml/eml-230-candidates-{self.election_root}.xml"
        )

    # endregion

    # region: Results
    def get_latest_results(self) -> None:
        """Get the latest results from the FTP server."""
        logger.debug("Getting latest results from FTP server.")
        results_zip_path = self._get_latest_ftp_file_from_path(
            path=f"/{self.election_root}/Standard/Light",
            file_role="results",
            file_extension=".zip",
        )

        latest_results_content = self._get_file_as_str_from_zip(
            results_zip_path,
            f"xml/aec-mediafeed-results-standard-light-{self.election_root}.xml",
        )

    # endregion

    # region: Helper methods
    def _get_file_as_str_from_zip(self, zip_file_path: Path, file_in_zip_path_str: str) -> str:
        """Get a file as a string from a zip file."""
        logger.debug("Getting file from zip: %s", file_in_zip_path_str)
        zip_file = ZipFile(zip_file_path, mode="r")
        with zip_file as zip_file:
            # List all files in the zip file
            logger.trace("Files in zip file: %s", zip_file.namelist())
            return zip_file.read(file_in_zip_path_str).decode("utf-8")

    def download_file(self, file_dir: str, file_name: str, file_role: str) -> None:
        """Download a file from the FTP server."""
        logger.info("Downloading file: %s from %s", file_name, file_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.cache_dir / file_name

        if output_file.exists():
            logger.info("File already exists, skipping download.")
        else:
            with contextlib.closing(FTP(FTP_URL)) as ftp:
                ftp.login()
                ftp.cwd(file_dir)

                with output_file.open("wb") as local_file:
                    ftp.retrbinary(f"RETR {file_name}", local_file.write)

        self.tracked_files[file_role] = output_file

    def refresh_ftp_file_list(self) -> None:
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

            paths = _recurse_get_paths("")
            paths.sort()

            if len(paths) == 0:
                msg = "No files found on the FTP server."
                raise ValueError(msg)

            self.ftp_listing = paths

    # endregion
