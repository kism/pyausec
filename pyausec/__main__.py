"""Main Entrypoint."""

from . import __version__
from .logger import get_logger
from .elec_grabber import AusElectionGrabber

logger = get_logger(__name__)


def main() -> None:
    """Main Entrypoint."""
    logger.info("pyausec version: %s", __version__)
    grabber = AusElectionGrabber()



if __name__ == "__main__":
    main()  # pragma: no cover
