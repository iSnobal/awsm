import os
import smrf
from .version import __version__

__core_config__ = os.path.abspath(
    os.path.dirname(__file__) + '/framework/CoreConfig.ini'
)
__recipes__ = os.path.abspath(os.path.dirname(
    __file__) + '/framework/recipes.ini'
)
__config_titles__ = {
    "awsm master": "Configurations for AWSM Master section",
    "paths": "Configurations for PATHS section for rigid directory work",
    "grid": "Configurations for GRID data to run iSnobal",
    "files": "Input files to run AWSM",
    "awsm system": "System parameters",
    "ipysnobal": "Running Python wrapped iSnobal",
    "ipysnobal initial conditions": "Initial condition parameters for PySnobal",
    "ipysnobal constants": "Input constants for PySnobal",
}
__config_header__ = "Configuration File for AWSM {0}\n Using SMRF {1}\n".format(
        __version__,
        smrf.__version__,

)
