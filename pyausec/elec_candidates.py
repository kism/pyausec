"""Class to handle the candidates for the election."""

from .elec_grabber import ElectionGrabber
from .logger import get_logger

logger = get_logger(__name__)


class ElectionCandidates:
    def __init__(self, grabber: ElectionGrabber) -> None:
        """Initialise the ElecCandidates object."""
        self.grabber = grabber
        self.candidate_xml_str = self.grabber.get_candidate_info()
        logger.debug("Got candidate XML listing, length: %s", len(self.candidate_xml_str))
