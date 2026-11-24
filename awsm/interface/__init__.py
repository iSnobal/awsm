from . import correct_precip
from .correct_precip import CustomSMRFConnector
# Make CustomSMRFConnector the default connector
default_connector = CustomSMRFConnector
