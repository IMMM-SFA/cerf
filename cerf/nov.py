import calendar

import numpy as np


class NetOperationalValue:
    """Calculate Net Operational Value (NOV) in ($ / yr) per grid cell for all technologies.

    :param discount_rate:                   The time value of money in real terms.
                                            Units:  fraction
    :type discount_rate:                    float

    :param lifetime:                        Years of the expected technology plant lifetime.
                                            Units:  years
    :type lifetime:                         int

    :param unit_size:                       The size of the expected power plant.
                                            Units:  megawatt
    :type unit_size:                        int

    :param capacity_factor:                 Capacity factor defined as average annual power generated divided by the
                                            potential output if the plant operated at its rated capacity for a year.
                                            Units:  fraction
    :type capacity_factor:                  float

    :param variable_cost_esc_rate:          Escalation rate of variable cost.
                                            Units:  fraction
    :type variable_cost_esc_rate:           float

    :param fuel_esc_rate:                   Escalation rate of fuel.
                                            Units:  fraction
    :type fuel_esc_rate:                    float

    :param carbon_esc_rate:                 Escalation rate of carbon.
                                            Units:  fraction
    :type carbon_esc_rate:                  float

    :param variable_om:                     Variable operation and maintenance costs of yearly capacity use.
                                            Units:  $/MWh
    :type variable_om:                      float

    :param heat_rate:                       Amount of energy used by a power plant to generate one kilowatt-hour of
                                            electricity.
                                            Units:  Btu/kWh
    :type heat_rate:                        float

    :param fuel_price:                      Cost of fuel per unit.
                                            Units:  from GCAM ($/GJ) gets converted to ($/MBtu)
    :type fuel_price:                       float

    :param carbon_tax:                      The fee imposed on the burning of carbon-based fuels.
                                            Units:  $/ton
    :type carbon_tax:                       float

    :param carbon_capture_rate:             Rate of carbon capture.
                                            Units:  fraction
    :type carbon_capture_rate:              float

    :param fuel_co2_content:                CO2 content of the fuel and the heat rate of the technology.
                                            Units:  from GCAM (tons/MWh) gets converted to (tons/Btu)
    :type fuel_co2_content:                 float

    :param lmp_arr:                         Locational Marginal Price (LMP) per grid cell for each technology in a
                                            multi-dimensional array where the shape is [tech_id, xcoord, ycoord].
                                            Units:  $/MWh
    :type lmp_arr:                          ndarray

    :param target_year:                     Target year of the simulation as a four digit integer (e.g., 2010)
    :type target_year:                      int

    :param consider_leap_year:              Choose to account for leap year in the number of hours per year calculation
    :type consider_leap_year:               bool

    """

    # type hints
    discount_rate: float
    lifetime: int
    unit_size: int
    capacity_factor: float
    variable_cost_esc_rate: float
    fuel_esc_rate: float
    carbon_esc_rate: float
    variable_om: float
    heat_rate: float
    fuel_price: float
    carbon_tax: float
    carbon_capture_rate: float
    fuel_co2_content: float
    lmp_arr: np.ndarray
    target_year: int
    consider_leap_year: bool

    # constants for conversion
    FUEL_CO2_CONTENT_CONVERSION_FACTOR = 0.000000293071
    FUEL_PRICE_CONVERSION_FACTOR = 1.055056
    HOURS_PER_YEAR_NONLEAP = 8760
    HOURS_PER_YEAR_LEAP = 8784

    def __init__(self, discount_rate, lifetime, unit_size, capacity_factor, variable_cost_esc_rate,
                 fuel_esc_rate, carbon_esc_rate, variable_om, heat_rate, fuel_price, carbon_tax,
                 carbon_capture_rate, fuel_co2_content, lmp_arr, target_year, consider_leap_year=False):

        # assign class attributes
        self.discount_rate = discount_rate
        self.lifetime = lifetime
        self.unit_size = unit_size
        self.capacity_factor = capacity_factor
        self.variable_cost_esc = variable_cost_esc_rate
        self.fuel_esc = fuel_esc_rate
        self.carbon_esc = carbon_esc_rate
        self.variable_om = variable_om
        self.heat_rate = heat_rate
        self.carbon_tax = carbon_tax
        self.carbon_capture_rate = carbon_capture_rate
        self.lmp_arr = lmp_arr

        # create conversions
        self.fuel_price = self.convert_fuel_price(fuel_price)
        self.fuel_co2_content = self.convert_fuel_co2_content(fuel_co2_content)

        # adjust by leap year if so desired
        self.hours_per_year = self.assign_hours_per_year(target_year, consider_leap_year)

        # calculate annuity factor
        self.annuity_factor = self.calc_annuity_factor()

        # calculate levelizing factor for variable OM
        self.lf_vom = self.calc_levelization_factor_vom()

        # calculate levelizing factor for fuel
        self.lf_fuel = self.calc_levelization_factor_fuel()

        # calculate levelizing factor for carbon
        self.lf_carbon = self.calc_levelization_factor_carbon()

    @staticmethod
    def convert_fuel_price(fuel_price):
        """Convert fuel price from units $/GJ to $/MBtu"""

        return fuel_price * NetOperationalValue.FUEL_PRICE_CONVERSION_FACTOR

    @staticmethod
    def convert_fuel_co2_content(fuel_co2_content):
        """Convert fuel CO2 content from units tons/MWh to tons/Btu"""

        return fuel_co2_content * NetOperationalValue.FUEL_CO2_CONTENT_CONVERSION_FACTOR

    @classmethod
    def assign_hours_per_year(cls, target_year, consider_leap_year):
        """Assign the hours per year based on whether or not the target year is a leap year."""

        if calendar.isleap(target_year) and consider_leap_year:
            return cls.HOURS_PER_YEAR_LEAP
        else:
            return cls.HOURS_PER_YEAR_NONLEAP

    def calc_annuity_factor(self):
        """Calculate annuity factor."""

        fx = pow(1.0 + self.discount_rate, self.lifetime)
        return self.discount_rate * fx / (fx - 1.0)

    def calc_levelization_factor_vom(self):
        """Calculate the levelizing factor for variable OM."""

        k = (1.0 + self.variable_cost_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime)) * self.annuity_factor / (1.0 - k)

    def calc_levelization_factor_fuel(self):
        """Calculate the levelizing factor for fuel."""

        k = (1.0 + self.fuel_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime)) * self.annuity_factor / (1.0 - k)

    def calc_levelization_factor_carbon(self):
        """Calculate the levelizing factor for carbon."""

        k = (1.0 + self.carbon_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime)) * self.annuity_factor / (1.0 - k)

    def calc_generation(self):
        """Calculate electricity generation."""

        return self.unit_size * self.capacity_factor * self.hours_per_year

    def calc_nov(self):
        """Calculate NOV array for all technologies."""

        generation = self.calc_generation()
        term2 = self.lmp_arr * self.lf_fuel
        term3 = self.variable_om * self.lf_vom
        term4 = self.heat_rate * (self.fuel_price / 1000) * self.lf_fuel
        term5 = (self.carbon_tax * self.fuel_co2_content * self.heat_rate * self.lf_carbon / 1000000) * (1 - self.carbon_capture_rate)

        return generation * (term2 - (term3 + term4 + term5))
