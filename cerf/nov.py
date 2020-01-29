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

    def calc_levelization_factor(self):
        """Calculate levelization factor"""

        annuity_factor, lifetime_arr = self.calc_annuity_factor()

        # TODO:  the value for l, real annual growth rate is missing (%)
        l = 0.1

        k = (1 + l) / (1 + self.discount_rate)

        return k * (1 - k ** lifetime_arr) * (annuity_factor / (1 - k))

    def calc_annuity_factor(self):
        """Calculate annuity factor as (d(1 + d)**n) / ((1 + d)**n - 1)
            where, d = real annual discount rate (%), n = asset lifetime (years)

        """
        lifetime_arr = self.arr.copy()

        for i in range(0, len(d)):
            lifetime_arr[i] = lifetime_arr[i] + self.tech_dict[i + 1]["lifetime"]

        numer = self.discount_rate * (1 + self.discount_rate) ** lifetime_arr
        denom = (1 + self.discount_rate) ** lifetime_arr - 1

        return numer / denom, lifetime_arr

    def calc_operating_costs(self):
        """Calculate operating costs"""

        # TODO: carbon price ($ / ton) not accounted for
        carbon_price = 0

        # TODO: carbon fuel content (tons / Btu) not accounted for
        carbon_fuel_content = 0

        # TODO:  why does heat_rate apprear twice?
        operating_costs = [d[i]["heat_rate"] * d[i]["fuel_price"] + d[i]["variable_om"] + carbon_price *
                           carbon_fuel_content * d[i]["heat_rate"] * (1 - d[i]["carbon_capture_rate"])
                           for i in range(1, len(d) + 1)]

        arr = self.arr.copy()

        for index, i in enumerate(operating_costs):
            arr[index] += i

        return arr

    def calc_nov(self):
        """Calculate NOV"""

        #         Generation (MWh / yr) *
        #                         [ Locational Marginal Price ($ / MWh) - Operating Costs ($ / MWh) ] *
        #                         Levelization Factor

        lev_factor = self.calc_levelization_factor()
        op_costs = self.calc_operating_costs()

        # TODO: start here
