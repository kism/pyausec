"""Main Entrypoint."""

from . import __version__
from .elec_grabber import AusAECElectionGrabber
from .logger import get_logger, setup_logger

logger = get_logger(__name__)


def main() -> None:
    """Main Entrypoint."""
    setup_logger(log_level="DEBUG")
    logger.info("pyausec version: %s", __version__)
    AusAECElectionGrabber()


if __name__ == "__main__":
    main()  # pragma: no cover
