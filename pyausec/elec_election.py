"""Class to handle the election information."""

from .elec_grabber import ElectionGrabber
from .logger import get_logger

logger = get_logger(__name__)


class ElectionInfo:
    """Class to handle the election information."""

    def __init__(self, grabber: ElectionGrabber) -> None:
        """Initialise the ElectionInfo object."""
        self.grabber = grabber
        self.election_info_xml_str = self.grabber.get_election_info()
        logger.debug("Got election XML listing, length: %s", len(self.election_info_xml_str))
