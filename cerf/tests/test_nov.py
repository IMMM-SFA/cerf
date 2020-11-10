"""Tests for Net Operational Value calculations.

:author:   Chris R. Vernon
:email:    chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

from cerf import NetOperationalValue


class TestNov(unittest.TestCase):
    """Tests for the NOV calculations."""

    # unit size in MW
    UNIT_SIZE = 1350

    # a single LMP for simplification
    LMP = 120.1228824

    TECH_DICT = {'lifetime': 60.0,
                    'capacity_factor': 0.9,
                    'variable_cost_esc_rate': -0.00104311614063357,
                    'fuel_esc_rate': 0.046979999999999945,
                    'interconnection_cost_per_km': 1104,
                    'variable_om': 2.0819883795997414,
                    'heat_rate': 10246.19999999998,
                    'fuel_price': 0.7810699999999998,
                    'carbon_capture_rate': 0.0,
                    'fuel_co2_content': 0.0,
                    'cf_lmp': 0.8,
                    'discount_rate': 0.05,
                    'carbon_esc_rate': 0.0,
                    'carbon_tax': 0}

    # expected values from calculations
    EXPECTED_ANNUITY_FACTOR = 0.05282818452724236
    EXPECTED_LF_LMP = 2.8109999800268062e+122
    EXPECTED_LF_TECH = 0.9819019248539469
    EXPECTED_LF_FUEL = 2.906727029767612
    EXPECTED_LF_CARBON = 0.999999999999999
    EXPECTED_NOV = 3.5939081315171005e+131

    @classmethod
    def instantiate_nov(cls):
        """Instantiate NOV class with test values."""

        return NetOperationalValue(discount_rate=cls.TECH_DICT['discount_rate'],
                                   lifetime=cls.TECH_DICT['lifetime'],
                                   unit_size=cls.UNIT_SIZE,
                                   capacity_factor=cls.TECH_DICT['capacity_factor'],
                                   variable_cost_esc_rate=cls.TECH_DICT['variable_cost_esc_rate'],
                                   fuel_esc_rate=cls.TECH_DICT['fuel_esc_rate'],
                                   carbon_esc_rate=cls.TECH_DICT['carbon_esc_rate'],
                                   variable_om=cls.TECH_DICT['variable_om'],
                                   heat_rate=cls.TECH_DICT['heat_rate'],
                                   fuel_price=cls.TECH_DICT['fuel_price'],
                                   carbon_tax=cls.TECH_DICT['carbon_tax'],
                                   carbon_capture_rate=cls.TECH_DICT['carbon_capture_rate'],
                                   fuel_co2_content=cls.TECH_DICT['fuel_co2_content'],
                                   lmp_arr=cls.LMP)

    def test_annuity_factor(self):
        """Test the calculation of annuity factor."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        af = econ.calc_annuity_factor()

        # compare against expected
        self.assertEqual(af, TestNov.EXPECTED_ANNUITY_FACTOR)

    def test_levelization_factor_lmp(self):
        """Test the calculation of the levelization factor for LMPs."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        lf = econ.calc_lf_lmp()

        # compare against expected
        self.assertEqual(lf, TestNov.EXPECTED_LF_LMP)

    def test_levelization_factor_tech(self):
        """Test the calculation of the levelization factor for technologies."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        lf = econ.calc_lf_tech()

        # compare against expected
        self.assertEqual(lf, TestNov.EXPECTED_LF_TECH)

    def test_levelization_factor_fuel(self):
        """Test the calculation of the levelization factor for fuel."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        lf = econ.calc_lf_fuel()

        # compare against expected
        self.assertEqual(lf, TestNov.EXPECTED_LF_FUEL)

    def test_levelization_factor_carbon(self):
        """Test the calculation of the levelization factor for carbon."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        lf = econ.calc_lf_carbon()

        # compare against expected
        self.assertEqual(lf, TestNov.EXPECTED_LF_CARBON)

    def test_nov(self):
        """Test the calculation of net operational value."""

        # instantiate NOV class
        econ = self.instantiate_nov()

        # calculate annuity factor
        nov = econ.calc_nov()

        # compare against expected
        self.assertEqual(nov, TestNov.EXPECTED_NOV)