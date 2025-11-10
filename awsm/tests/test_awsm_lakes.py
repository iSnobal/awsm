from awsm.framework.framework import run_awsm
from awsm.tests.awsm_test_case_lakes import AWSMTestCaseLakes


class TestLakes(AWSMTestCaseLakes):
    """
    Testing using Lakes:
        - ipysnobal
        - initialize from snow.nc file
        - loading from netcdf
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold_dir = cls.basin_dir.joinpath("gold_hrrr")

        cls.output_path = cls.basin_dir.joinpath(
            "output/lakes/wy2020/lakes_gold/run20191001_20191001"
        )

        run_awsm(cls.run_config, testing=True)

    def test_snow_nc(self):
        self.compare_netcdf_files(
            "snow.nc",
            [
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
        )

    def test_em_nc(self):
        self.compare_netcdf_files(
            "em.nc",
            [
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
        )
