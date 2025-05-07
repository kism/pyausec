"""Class to handle the candidates for the election."""

from pathlib import Path

from .elec_grabber import AusAECElectionGrabber


class ElectionCandidates(AusAECElectionGrabber):

    def __init__(self, cache_dir: Path | None = None, current_election: str | None = None) -> None:
        """Initialise the ElecCandidates.

        Args:
            cache_dir (str): Path to the cache directory, where the zips will be stored.
            current_election (str): The current election (number) to grab data for.
                If None, will grab the only election.
        """
        super().__init__(cache_dir, current_election)
