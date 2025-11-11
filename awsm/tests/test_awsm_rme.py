from awsm.framework.framework import run_awsm
from awsm.tests.awsm_test_case import AWSMTestCase


class TestRME(AWSMTestCase):
    """
    Testing using RME
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold_dir = cls.basin_dir.joinpath("gold")

        cls.output_path = cls.basin_dir.joinpath(
            "output/rme/wy1986/rme_test/run19860217_19860217"
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
