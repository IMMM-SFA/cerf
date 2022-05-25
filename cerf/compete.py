import logging

import numpy as np
import pandas as pd

import cerf.utils as util


class Competition:
    """Technology competition algorithm for CERF.

    Grid cell level net locational cost (NLC) per technology and an electricity technology capacity expansion plan are
    used to compete technologies against each other to see which will win the grid cell. The technology that wins the
    grid cell is then sited until no further winning cells exist. Once sited, the location of the winning technology’s
    grid cell, along with its buffer, are no longer available for siting. The competition array is recalculated after
    all technologies have passed through an iteration. This process is repeated until there are either no cells left
    to site or there are no more power plants left to satisfy the expansion plan for any technology. For technologies
    that have the same NLC value in multiple grid cells that win the competition, random selection is available by
    default. If the user wishes to have the outcomes be repeatable, the randomizer can be set to False and a random
    seed set.

    :param expansion_plan:                          Dictionary of {tech_id: number_of_sites, ...}
    :type expansion_plan:                           dict

    :param nlc_mask:                                3D masked array of [tech_id, x, y] for Net Locational Costs. Each
                                                    technology has been masked with its suitability data, so only
                                                    grid cells that are suitable have an NLC per tech. The 0 index
                                                    position is a default dimension which is chosen if no technologies
                                                    are able to compete.
    :type nlc_mask:                                 ndarray

    :param technology_dict:                         A technology dictionary containing at a minimum
                                                    {tech_id:  buffer_in_km, ...}
    :type technology_dict:                          dict

    :param randomize:                               Choose to make randomization of site selection where NLC is the same
                                                    in multiple grid cells for a single technology random. If False,
                                                    the seed_value will be used as a way to reproduce the exact siting.
                                                    Default:  True
    :type randomize:                                bool

    :param seed_value:                              Value for the see if randomize is False.
    :type seed_value:                               int

    :param verbose:                                 Log out siting information. Default False.
    :type verbose:                                  bool

    """

    def __init__(self,
                 target_region_name,
                 settings_dict,
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 lmp_dict,
                 generation_dict,
                 operating_cost_dict,
                 nov_dict,
                 ic_dict,
                 nlc_mask,
                 zones_arr,
                 xcoords,
                 ycoords,
                 indices_flat,
                 randomize=True,
                 seed_value=0,
                 verbose=False):

        # target region
        self.target_region_name = target_region_name

        # project level settings dictionary
        self.settings_dict = settings_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # dictionary containing the expansion plan
        self.expansion_dict = expansion_dict

        # locational marginal pricing
        self.lmp_flat_dict = lmp_dict

        # generation
        self.generation_flat_dict = generation_dict

        # operating cost
        self.operating_cost_flat_dict = operating_cost_dict

        # net operational value
        self.nov_flat_dict = nov_dict

        # interconnection costs
        self.ic_flat_dict = ic_dict

        # lmp zones array
        self.zones_flat_arr = zones_arr

        # flat array of full grid indices value for the target region
        self.indices_flat = indices_flat

        # net locational costs with suitability mask for the target region
        self.nlc_mask = nlc_mask
        self.nlc_mask_shape = self.nlc_mask.shape

        # log out additional info
        self.verbose = verbose

        # use random seed to create reproducible outcomes
        if randomize is False:
            np.random.seed(seed_value)

        # number of technologies
        self.n_techs = len(self.technology_order)

        # dictionary to hold sited information
        self.sited_dict = util.empty_sited_dict()

        # coordinates for each index
        self.xcoords = xcoords
        self.ycoords = ycoords

        # mask any technologies having 0 expected sites in the expansion plan to exclude them from competition
        for index, i in enumerate(self.technology_order, 1):
            if expansion_dict[i]["n_sites"] == 0:
                self.nlc_mask[index, :, :] = np.ma.masked_array(self.nlc_mask[index, :, :],
                                                                np.ones_like(self.nlc_mask[index, :, :]))

        # show cheapest option, add 1 to the index to represent the technology number
        self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

        # flatten cheapest array to be able to use random
        self.cheapest_arr_1d = self.cheapest_arr.flatten()

        # prep array to hold outputs
        self.sited_arr_1d = np.zeros_like(self.cheapest_arr_1d)

        # set initial value to for available grid cells
        self.avail_grids = np.where(self.cheapest_arr_1d > 0)[0].shape[0]

        # create dictionary of {tech_id: flat_nlc_array, ...}
        self.nlc_flat_dict = {i: self.nlc_mask[ix+1, :, :].flatten() for ix, i in enumerate(self.technology_order)}

        # run competition and site
        self.sited_array, self.sited_df = self.compete()

        # evaluate sites to see if expansion plan was met
        self.log_outcome()

    def log_outcome(self):
        """Log a warning sites that were not able to be sited."""

        for k in self.expansion_dict.keys():

            tech_name = self.expansion_dict[k]['tech_name']
            remaining_sites = self.expansion_dict[k]['n_sites']

            if remaining_sites > 0:
                logging.warning(f"Unable to achieve full siting for `{tech_name}` in `{self.target_region_name}`:  {remaining_sites} unsited.")

    def compete(self):

        # initialize keep sighting designation; False if no more sites or area to site
        keep_siting = True

        while keep_siting:

            # evaluate by technology
            for index, tech_id in enumerate(self.technology_order):

                # assign an index as it appears in the n-dim array to the order in which it is being processed
                #  index of 0 is the default array and does not represent a technology
                tech_index = index + 1

                # get the indices of the target tech ids where the target tech is the cheapest option
                tech = np.where(self.cheapest_arr_1d == tech_index)[0]

                # the number of sites for the target tech
                required_sites = self.expansion_dict[tech_id]['n_sites']

                # calculate the year of retirement
                retirement_year = self.settings_dict['run_year'] + int(self.technology_dict[tech_id]['lifetime_yrs'])

                # if there are more power plants to site and there are grids available to site them...
                if self.avail_grids > 0 and tech.shape[0] > 0 and required_sites > 0:

                    # site with buffer and exclude buffered area from further siting
                    still_siting = True
                    sited_list = []
                    while still_siting:

                        # get the NLC values associated with each winner
                        tech_nlc = self.nlc_flat_dict[tech_id][tech]

                        # get the least expensive NLC indices from the winners
                        tech_nlc_cheap = tech[np.where(tech_nlc == np.nanmin(tech_nlc))]

                        # select a random index that has a winning cell for the check where multiple low NLC may exists
                        target_ix = np.random.choice(tech_nlc_cheap)

                        # add selected index to sited dictionary
                        self.sited_dict['region_name'].append(self.target_region_name)
                        self.sited_dict['tech_id'].append(tech_id)
                        self.sited_dict['tech_name'].append(self.technology_dict[tech_id]['tech_name'])
                        self.sited_dict['unit_size_mw'].append(self.technology_dict[tech_id]['unit_size_mw'])
                        self.sited_dict['xcoord'].append(self.xcoords[target_ix])
                        self.sited_dict['ycoord'].append(self.ycoords[target_ix])
                        self.sited_dict['index'].append(self.indices_flat[target_ix])
                        self.sited_dict['buffer_in_km'].append(self.technology_dict[tech_id]['buffer_in_km'])
                        self.sited_dict['sited_year'].append(self.settings_dict['run_year'])
                        self.sited_dict['retirement_year'].append(retirement_year)
                        self.sited_dict['lmp_zone'].append(self.zones_flat_arr[target_ix])
                        self.sited_dict['locational_marginal_price_usd_per_mwh'].append(self.lmp_flat_dict[tech_id][target_ix])
                        self.sited_dict['generation_mwh_per_year'].append(self.generation_flat_dict[tech_id][target_ix])
                        self.sited_dict['operating_cost_usd_per_year'].append(self.operating_cost_flat_dict[tech_id][target_ix])
                        self.sited_dict['net_operational_value_usd_per_year'].append(self.nov_flat_dict[tech_id][target_ix])
                        self.sited_dict['interconnection_cost_usd_per_year'].append(self.ic_flat_dict[tech_id][target_ix])
                        self.sited_dict['net_locational_cost_usd_per_year'].append(self.nlc_flat_dict[tech_id][target_ix])
                        self.sited_dict['capacity_factor_fraction'].append(self.technology_dict[tech_id]["capacity_factor_fraction"])
                        self.sited_dict['carbon_capture_rate_fraction'].append(self.technology_dict[tech_id]["carbon_capture_rate_fraction"])
                        self.sited_dict['fuel_co2_content_tons_per_btu'].append(self.technology_dict[tech_id]["fuel_co2_content_tons_per_btu"])
                        self.sited_dict['fuel_price_usd_per_mmbtu'].append(self.technology_dict[tech_id]["fuel_price_usd_per_mmbtu"])
                        self.sited_dict['fuel_price_esc_rate_fraction'].append(self.technology_dict[tech_id]["fuel_price_esc_rate_fraction"])
                        self.sited_dict['heat_rate_btu_per_kWh'].append(self.technology_dict[tech_id]["heat_rate_btu_per_kWh"])
                        self.sited_dict['lifetime_yrs'].append(self.technology_dict[tech_id]["lifetime_yrs"])
                        self.sited_dict['variable_om_usd_per_mwh'].append(self.technology_dict[tech_id]["variable_om_usd_per_mwh"])
                        self.sited_dict['variable_om_esc_rate_fraction'].append(self.technology_dict[tech_id]["variable_om_esc_rate_fraction"])
                        self.sited_dict['carbon_tax_usd_per_ton'].append(self.technology_dict[tech_id]["carbon_tax_usd_per_ton"])
                        self.sited_dict['carbon_tax_esc_rate_fraction'].append(self.technology_dict[tech_id]["carbon_tax_esc_rate_fraction"])

                        # add selected index to list
                        sited_list.append(target_ix)

                        # apply buffer
                        result = util.buffer_flat_array(target_index=target_ix,
                                                        arr=self.cheapest_arr_1d,
                                                        nrows=self.cheapest_arr.shape[0],
                                                        ncols=self.cheapest_arr.shape[1],
                                                        ncells=self.technology_dict[tech_id]['buffer_in_km'],
                                                        set_value=0)

                        # unpack values
                        self.cheapest_arr_1d, buffer_indices_list = result

                        # update the number of sites left to site
                        required_sites -= 1
                        self.expansion_dict[tech_id].update(n_sites=required_sites)

                        # remove any buffered elements as an option to site
                        tech_indices_to_delete = [np.where(tech == i)[0][0] for i in buffer_indices_list if i in tech]
                        tech = np.delete(tech, tech_indices_to_delete)

                        # exit siting for the target technology if all sites have been sited or if there are no more
                        #   winning cells
                        if required_sites == 0 or tech.shape[0] == 0:
                            still_siting = False

                    # array of the site indices
                    rdx = np.array(sited_list)

                    # add sited techs to output array
                    self.sited_arr_1d[rdx] = tech_id

                    if self.verbose:
                        logging.info('\nUpdate expansion plan to represent siting requirements:')
                        logging.info(self.expansion_dict)

                    # update original array with excluded area where siting occurred
                    # if target technology has no more sites to be sited
                    if self.expansion_dict[tech_id] == 0:

                        # make all elements for the target tech in the NLC mask unsuitable so we can progress
                        self.nlc_mask[tech_index, :, :] = np.ma.masked_array(self.nlc_mask[0, :, :],
                                                                             np.ones_like(self.nlc_mask[0, :, :]))

                    # apply the new exclusion from the current technology to all techs...
                    #   invert sited elements to have a value of 1 so they can be used as a mask
                    #   repeat the new sited array to create a mask for all techs and reshape to 2D
                    #   update all technologies with the new mask
                    self.nlc_mask[1:, :, :] = np.ma.masked_array(self.nlc_mask[1:, :, :],
                                                                 np.tile(np.where(self.cheapest_arr_1d == 0, 1, 0),
                                                                         self.nlc_mask_shape[0] - 1).reshape(
                                                                     (self.nlc_mask_shape[0] - 1,
                                                                      self.nlc_mask_shape[1],
                                                                      self.nlc_mask_shape[2])))

                    # if the technology has achieved its full expansion, then mask the rest of its suitable area so
                    #  other technologies can now compete for the grid cells it previously won but now no longer needs
                    if self.expansion_dict[tech_id]['n_sites'] == 0:
                        self.nlc_mask[tech_index, :, :] = np.ma.masked_array(self.nlc_mask[tech_index, :, :],
                                                                             np.ones_like(self.nlc_mask[tech_index, :, :]))

                    # show cheapest option, add 1 to the index to represent the technology number
                    self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

                    # flatten cheapest array to be able to use random
                    self.cheapest_arr_1d = self.cheapest_arr.flatten()

                    # check for any available grids to site in
                    self.avail_grids = np.where(self.cheapest_arr_1d > 0)[0].shape[0]

                    # are there any sites left to site
                    left_to_site = sum([self.expansion_dict[i]['n_sites'] for i in self.expansion_dict.keys()])

                    # stop technology iteration if all area is consumed or if all sites have been sited
                    if self.avail_grids == 0 or left_to_site == 0:
                        keep_siting = False

                    if self.verbose:
                        logging.info(f'\nAvailable grid cells:  {self.avail_grids}')

                # there are no more suitable grid cells
                elif self.avail_grids == 0:
                    keep_siting = False

                # if there are available grids and a cheapest option available but no more required sites
                elif self.avail_grids > 0 and tech.shape[0] > 0 and required_sites == 0:

                    # if there are no required sites, then mask the rest of the techs suitable area so
                    #  other technologies can now compete for the grid cells it previously won but now no longer needs
                    self.nlc_mask[tech_index, :, :] = np.ma.masked_array(self.nlc_mask[tech_index, :, :],
                                                                         np.ones_like(self.nlc_mask[tech_index, :, :]))

                    # show cheapest option, add 1 to the index to represent the technology number
                    self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

                    # flatten cheapest array to be able to use random
                    self.cheapest_arr_1d = self.cheapest_arr.flatten()

                    # check for any available grids to site in
                    self.avail_grids = np.where(self.cheapest_arr_1d > 0)[0].shape[0]

                # if there are suitable cells AND no winners and some or no sites left to site pass until next round
                else:
                    pass

        # create sited data frame
        df = pd.DataFrame(self.sited_dict).astype(util.sited_dtypes())

        # reshape output array to 2D
        return self.sited_arr_1d.reshape(self.cheapest_arr.shape), df
