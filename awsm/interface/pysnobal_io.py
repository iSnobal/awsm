import os
from copy import copy
from datetime import datetime
from pathlib import Path

import netCDF4 as nc
import numpy as np
from spatialnc.proj import add_proj

# NetCDF file parameters
COMPRESSION = dict(zlib=True, complevel=4)
DIMENSIONS = ("time", "y", "x")

C_TO_K = 273.16
FREEZE = C_TO_K


# Kelvin to Celsius
def K_TO_C(x):
    return x - FREEZE

def create_netCDF(
    filename: Path, start_date: datetime, init: dict, myawsm
) -> nc.Dataset:
    """
    Create a new netCDF output file, removing any existing with the same name.
    This adds all required dimensions for the file, including x, y, and time.

    Parameters
    ----------
    filename : Path
        Full path of the output file including the name
    start_date : datetime
        Start date of written data
    init : dict
        X and Y dimensions
    myawsm : AWSM
        AWSM instance object

    Returns
    -------
    nc.Dataset
        Create file in open state
    """
    if os.path.isfile(filename):
        myawsm._logger.warning("Removing existing {} file".format(filename))
        os.remove(filename)

    netcdf_file = nc.Dataset(filename, "w")

    # Create the dimensions
    netcdf_file.createDimension("time", None)
    netcdf_file.createDimension("y", len(init["y"]))
    netcdf_file.createDimension("x", len(init["x"]))

    # Variables for dimensions
    time = netcdf_file.createVariable(
        "time", np.float32, DIMENSIONS[0], **COMPRESSION
    )
    netcdf_file.createVariable("y", "f4", DIMENSIONS[1], **COMPRESSION)
    netcdf_file.createVariable("x", "f4", DIMENSIONS[2], **COMPRESSION)

    time.units = "hours since %s" % start_date.tz_localize(None)
    time.time_zone = str(myawsm.tzinfo).lower()
    time.calendar = "standard"

    netcdf_file.variables["x"][:] = init["x"]
    netcdf_file.variables["y"][:] = init["y"]

    return netcdf_file


def create_variables(netcdf_file: nc.Dataset, variables: dict, myawsm):
    """
    Create NetCDF variables with units and description

    Parameters
    ----------
    netcdf_file : nc.Dataset
        File to add variables to
    variables : dict
        Variable information. Needs keys for name, units ,and description
    myawsm : AWSM
        AWSM instance
    """
    for index, variable in enumerate(variables["name"]):
        # check to see if in output variables
        if variable.lower() in myawsm.pysnobal_output_vars:
            nc_variable = netcdf_file.createVariable(
                variable,
                "f4",
                DIMENSIONS,
                **COMPRESSION,
                least_significant_digit=4,
            )
            nc_variable.units = variables["units"][index]
            nc_variable.description = variables["description"][index]


def output_files(options, init, start_date, myawsm):
    """
    Create the snow and em output netCDF file

    Args:
        options:     dictionary of Snobal options
        init:        dictionary of Snobal initialization images
        start_date:  date for time units in files
        myawsm:      awsm class

    """
    # ------------------------------------------------------------------------
    # EM netCDF
    em_variables = {
        "name": [
            "net_rad",
            "sensible_heat",
            "latent_heat",
            "snow_soil",
            "precip_advected",
            "sum_EB",
            "evaporation",
            "snowmelt",
            "SWI",
            "cold_content",
        ],
        "units": [
            "W m-2",
            "W m-2",
            "W m-2",
            "W m-2",
            "W m-2",
            "W m-2",
            "kg m-2",
            "kg m-2",
            "kg or mm m-2",
            "J m-2",
        ],
        "description": [
            "Average net all-wave radiation",
            "Average sensible heat transfer",
            "Average latent heat exchange",
            "Average snow/soil heat exchange",
            "Average advected heat from precipitation",
            "Average sum of EB terms for snowcover",
            "Total evaporation",
            "Total snowmelt",
            "Total runoff",
            "Snowcover cold content",
        ],
    }

    file_path = os.path.join(
        options["output"]["location"], myawsm.em_name + ".nc"
    )
    em = create_netCDF(file_path, start_date, init, myawsm)
    create_variables(em, em_variables, myawsm)

    em = add_proj(em, None, myawsm.topo.topoConfig["filename"])

    options["output"]["em"] = em

    # ------------------------------------------------------------------------
    # SNOW netCDF

    snow_variables = {
        "name": [
            "thickness",
            "snow_density",
            "specific_mass",
            "liquid_water",
            "temp_surf",
            "temp_lower",
            "temp_snowcover",
            "thickness_lower",
            "water_saturation",
        ],
        "units": [
            "m",
            "kg m-3",
            "kg m-2",
            "kg m-2",
            "C",
            "C",
            "C",
            "m",
            "percent",
        ],
        "description": [
            "Predicted thickness of the snowcover",
            "Predicted average snow density",
            "Predicted specific mass of the snowcover",
            "Predicted mass of liquid water in the snowcover",
            "Predicted temperature of the surface layer",
            "Predicted temperature of the lower layer",
            "Predicted temperature of the snowcover",
            "Predicted thickness of the lower layer",
            "Predicted percentage of liquid water saturation of the snowcover",
        ],
    }

    file_path = os.path.join(
        options["output"]["location"], myawsm.snow_name + ".nc"
    )
    snow = create_netCDF(file_path, start_date, init, myawsm)
    create_variables(snow, snow_variables, myawsm)

    snow = add_proj(snow, None, myawsm.topo.topoConfig["filename"])

    options["output"]["snow"] = snow


def output_timestep(s, tstep, options, output_vars):
    """
    Output the model results for the current time step

    Args:
        s:       dictionary of output variable numpy arrays
        tstep:   datetime time step
        options: dictionary of Snobal options

    """

    em_out = {
        "net_rad": "R_n_bar",
        "sensible_heat": "H_bar",
        "latent_heat": "L_v_E_bar",
        "snow_soil": "G_bar",
        "precip_advected": "M_bar",
        "sum_EB": "delta_Q_bar",
        "evaporation": "E_s_sum",
        "snowmelt": "melt_sum",
        "SWI": "ro_pred_sum",
        "cold_content": "cc_s",
    }
    snow_out = {
        "thickness": "z_s",
        "snow_density": "rho",
        "specific_mass": "m_s",
        "liquid_water": "h2o",
        "temp_surf": "T_s_0",
        "temp_lower": "T_s_l",
        "temp_snowcover": "T_s",
        "thickness_lower": "z_s_l",
        "water_saturation": "h2o_sat",
    }

    em = {}
    snow = {}

    # Gather all the data together
    for key, value in em_out.items():
        em[key] = copy(s[value])

    for key, value in snow_out.items():
        snow[key] = copy(s[value])

    # convert from K to C
    snow["temp_snowcover"] -= FREEZE
    snow["temp_surf"] -= FREEZE
    snow["temp_lower"] -= FREEZE

    times = options["output"]["snow"].variables["time"]
    # offset to match same convention as iSnobal
    # tstep -= pd.to_timedelta(1, unit='h')                                 # pk commented this out. correct me if i'm wrong 2022 10 19
    t = nc.date2num(tstep.replace(tzinfo=None), times.units, times.calendar)

    if len(times) != 0:
        index = np.where(times[:] == t)[0]
        if index.size == 0:
            index = len(times)
        else:
            index = index[0]
    else:
        index = len(times)

    # Insert the time
    options["output"]["snow"].variables["time"][index] = t
    options["output"]["em"].variables["time"][index] = t

    # insert the data
    for key in em_out:
        if key.lower() in output_vars:
            options["output"]["em"].variables[key][index, :] = em[key]
    for key in snow_out:
        if key.lower() in output_vars:
            options["output"]["snow"].variables[key][index, :] = snow[key]

    # sync to disk
    options["output"]["snow"].sync()
    options["output"]["em"].sync()
