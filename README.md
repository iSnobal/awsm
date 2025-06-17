
# Fork of the Automated Water Supply Model (AWSM)

This is a fork of the [USDA-ARS-NWRC AWSM](https://github.com/USDA-ARS-NWRC/awsm) repo
to continue the development of the framework.

# Usage
The installation of this package provides a command line interface to run the model.
The command is called `awsm`.

## Examples
### Run the first day
```bash
awsm -c awsm.ini -sd 2024-10-01 --no_previous
```

### Run a single day
```bash
awsm -c awsm.ini -sd 2024-10-01
```

### Run days set in the configuration file
```bash
awsm -c awsm.ini
```

### Re-run after a model crash
```bash
awsm -c awsm.ini -sd 2024-10-01 --threshold
```

## Help
```bash
usage: awsm [-h] -c CONFIG_FILE [-sd START_DATE] [-np] [-t] [-mt MEDIUM_THRESHOLD]

Run AWSM with given config file.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config_file CONFIG_FILE
                        Path to .ini config file.
  -sd START_DATE, --start_date START_DATE
                        Overwrite the start date in the .ini and force a single day run. Format: YYYYMMDD or YYYY-MM-DD
  -np, --no_previous    Skip finding a previous snow state and storm day file. Usually used when running the first day.
  -t, --threshold       Run iSnobal with different mass threshold
  -mt MEDIUM_THRESHOLD, --medium_threshold MEDIUM_THRESHOLD
                        Set the medium mass threshold. Default: 25
```

# Installation

Setting up the model uses the `conda` environment management software.
A setup follows the steps described in the
[isnoda instructions](https://github.com/UofU-Cryosphere/isnoda/tree/master/conda)

# History
This repo was used in the following publications

* Meyer, J., Horel, J., Kormos, P., Hedrick, A., Trujillo, E., and Skiles, S. M.: Operational water forecast ability of the HRRR-iSnobal combination: an evaluation to adapt into production environments, Geosci. Model Dev., 16, 233–250, https://doi.org/10.5194/gmd-16-233-2023, 2023.
  Zenodo [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7452230.svg)](https://doi.org/10.5281/zenodo.7452230)

* Meyer, J., Hedrick, A., and McKenzie Skiles, S.: A new approach to net solar radiation in a spatially distributed snow energy balance model to improve snowmelt timing, Journal of Hydrology, 131490, https://doi.org/10.1016/j.jhydrol.2024.131490, 2024.
  Zenodo [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11245701.svg)](https://doi.org/10.5281/zenodo.11245701)
