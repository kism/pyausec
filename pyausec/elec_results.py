"""Class to handle the results for the election."""

from .elec_grabber import ElectionGrabber
from .logger import get_logger

logger = get_logger(__name__)


class ElectionResults:
    """Class to handle the results for the election."""

    def __init__(self, grabber: ElectionGrabber) -> None:
        """Initialise the ElectionResults object."""
        self.grabber = grabber
        self.results_xml_str = self.grabber.get_results()
        logger.debug("Got results XML listing, length: %s", len(self.results_xml_str))
