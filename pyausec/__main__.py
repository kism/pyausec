"""Main Entrypoint."""

from . import __version__
from .elec_candidates import ElectionCandidates
from .elec_election import ElectionInfo
from .elec_grabber import ElectionGrabber
from .elec_results import ElectionResults
from .logger import get_logger, setup_logger

logger = get_logger(__name__)


def main() -> None:
    """Main Entrypoint."""
    setup_logger(log_level="DEBUG")
    logger.info("pyausec version: %s", __version__)
    grabber = ElectionGrabber()
    ElectionCandidates(grabber)
    ElectionInfo(grabber)
    ElectionResults(grabber)
    logger.info("Finished grabbing election data.")


if __name__ == "__main__":
    main()  # pragma: no cover
