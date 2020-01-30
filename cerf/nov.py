import numpy as np


class Nov:
    """Calculate Net Operating Value (NOV) in ($ / yr) as the following:

    ```NOV ($ / yr) = Generation (MWh / yr) *
                        [ Locational Marginal Price ($ / MWh) - Operating Costs ($ / MWh) ] *
                        Levelization Factor

            where, Operating Costs ($ / MWh) = Heat Rate (Btu / kWh) *
                                                Fuel Price ($ / MBtu) (MBtu / 10**6 Btu) (10**3 kWh / MWh) +
                                                Variable O&M ($ / MWh) +
                                                Carbon Price ($ / ton) *
                                                Carbon Fuel Content (tons / Btu) *
                                                Heat Rate (Btu / kWh) (10**3 kWh / MWh) *
                                                (1 - Carbon Capture Rate (%))

            and, Levelization Factor = k * (1 - k**n) * (Annuity Factor / (1 - k))

                where, k = (1 + l) / (1 + d)
                        l = real annual growth rate (%)
                        d = real annual discount rate (%)

                and, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)

                    where, d = real annual discount rate (%)
                            n = asset lifetime (years)```

    :param technology_dict:         Dictionary of technology-specific data. E.g., {techid: unit_size: 600

    """

    def __init__(self, technology_dict, discount_rate, lmp_array):

        self.tech_dict = technology_dict
        self.discount_rate = discount_rate
        self.lmp_arr = lmp_array

        self.arr = np.zeros_like(self.lmp_arr)  # techid, col, row

        self.annuity_factor_arr, self.lifetime_arr = self.calc_annuity_factor()

    def calc_levelization_factor(self, l):
        """Calculate levelization factor

        :param l:            Real annual growth rate (%)

        :return:             3D array of levelization factor [techid, col, row]

        """

        # TODO:  check on the actual value for l
        k = (1 + l) / (1 + self.discount_rate)

        return k * (1 - k ** self.lifetime_arr) * (self.annuity_factor_arr / (1 - k))

    def calc_annuity_factor(self):
        """Calculate annuity factor as (d(1 + d)**n) / ((1 + d)**n - 1)
            where, d = real annual discount rate (%), n = asset lifetime (years)

        :returns:           [0] annuity factor as a 3D array (techid, col, row)
                            [1] technology lifetime in years as a 3D array (techid, col, row)

        """
        lifetime_arr = self.arr.copy()

        for i in range(0, len(d)):
            lifetime_arr[i] = lifetime_arr[i] + self.tech_dict[i + 1]["lifetime"]

        fx = (1 + self.discount_rate) ** lifetime_arr

        annuity_factor = (self.discount_rate * fx) / (fx - 1)

        return annuity_factor, lifetime_arr

    def calc_operating_costs(self):
        """Calculate operating costs"""

        variable_om_arr = self.arr.copy()
        fuel_arr = self.arr.copy()
        carbon_arr = self.arr.copy()
        capture_arr = self.arr.copy()
        lev_tech_arr = self.arr.copy()
        lev_fuel_arr = self.arr.copy()
        lev_carbon_arr = self.arr.copy()

        for index, tech in enumerate(self.tech_dict.keys()):
            techid = index + 1

            tech_data = self.tech_dict[techid]

            # from constants
            carbon_tax = 0.0
            carbon_tax_escalation = 0.0

            # TODO:  find what the escalation variable is for technology lev factor
            # TODO: change these from 3D to 2D arrays in the actual method
            lev_tech_arr[index] = self.calc_levelization_factor(tech_data["fuel_price_escalation"])[index]
            lev_fuel_arr[index] = self.calc_levelization_factor(tech_data["fuel_price_escalation"])[index]
            lev_carbon_arr[index] = self.calc_levelization_factor(carbon_tax_escalation)[index]

            #             # TODO:  why does heat_rate apprear twice?
            #             operating_costs = [d[i]["heat_rate"] * d[i]["fuel_price"] + d[i]["variable_om"] + carbon_price *
            #              carbon_fuel_content * d[i]["heat_rate"] * (1 - d[i]["carbon_capture_rate"])
            #              for i in range(1, len(d) + 1)]

            variable_om_arr[index] = tech_data["variable_om"]
            fuel_arr[index] = tech_data["heat_rate"] * (tech_data["fuel_price"] / 1000)
            carbon_arr[index] = carbon_tax * tech_data["fuel_co2_content"] * tech_data["heat_rate"]
            capture_arr[index] = 1 - tech_data["carbon_capture_rate"]

        opp_arr = (variable_om_arr * lev_tech_arr) + (fuel_arr * lev_fuel_arr) + (
                    carbon_arr * carbon_tax_escalation / 1000000) * capture_arr

        return opp_arr

    def calc_generation(self):
        """Calcuate generation in (MWh / yr)

            Note:  8760 is the number of hours in a year

        """

        gen_arr = self.arr.copy()

        for index, tech in enumerate(self.tech_dict.keys()):
            techid = index + 1

            unit_size = self.tech_dict[techid]["unit_size"]
            cap_fact = self.tech_dict[techid]["capacity_factor"]

            gen_arr[index] = unit_size * cap_fact * 8760

        return gen_arr

    def calc_nov(self):
        """Calculate NOV"""

        generation = self.calc_generation()

        # levelize LMPs
        lmps = self.lmp_arr * self.calc_levelization_factor(self.lmp_arr)

        # operating costs
        operating_costs = self.calc_operating_costs()

        return generation * (lmps - operating_costs)
