import numpy as np

from cerf.utils import buffer_flat_array


class Competition:
    """Technology competition algorithm for CERF.

    Grid cell level net locational cost (NLC) per technology and an electricity technology capacity expansion plan
    are used to compete technologies against each other to see which will win the grid cell. The technology
    that wins the grid cell is then sited until no further winning cells exist. Once sited, the location of the
    winning technology's grid cell, along with its buffer, are no longer available for siting. The competition
    array is recalculated after all technologies have passed through an iteration. This process is completed until
    there are either no cells left to site in or there are no more sites left to site for any technology. For
    technologies that have the same NLC value in multiple grid cells, random selection is available by default.  If the
    user wishes to have the outcomes be repeatable, the randomizer can be set to False.

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
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 nlc_mask,
                 randomize=True,
                 seed_value=0,
                 verbose=False):

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # dictionary containing the expansion plan
        self.expansion_dict = expansion_dict

        self.nlc_mask = nlc_mask
        self.nlc_mask_shape = self.nlc_mask.shape
        self.verbose = verbose

        # use random seed to create reproducible outcomes
        if randomize is False:
            np.random.seed(seed_value)

        # number of technologies
        self.n_techs = len(self.technology_order)

        # show cheapest option, add 1 to the index to represent the technology number
        self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

        # flatten cheapest array to be able to use random
        self.cheapest_arr_1d = self.cheapest_arr.flatten()

        # prep array to hold outputs
        self.sited_arr_1d = np.zeros_like(self.cheapest_arr_1d)

        # set initial value to for available grid cells
        self.avail_grids = 1

        # create dictionary of {tech_id: flat_nlc_array, ...}
        self.nlc_flat_dict = {i: self.nlc_mask[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}

        self.sited_array = self.compete()

    def compete(self):

        while self.avail_grids > 0:

            # evaluate by technology
            for index, tech_id in enumerate(self.technology_order):

                # assign an index as it appears in the n-dim array to the order in which it is being processed
                #  index of 0 is the default array and does not represent a technology
                tech_index = index + 1

                # get the indices of the target tech ids where the target tech is the cheapest option
                tech = np.where(self.cheapest_arr_1d == tech_index)[0]

                # if there are more power plants to site and there are grids available to site them...
                if self.avail_grids > 0 and tech.shape[0] > 0:

                    # the number of sites for the target tech
                    required_sites = self.expansion_dict[tech_id]

                    # site with buffer and exclude buffered area from further siting
                    still_siting = True
                    sited_list = []
                    while still_siting:

                        # get the NLC values associated with each winner
                        tech_nlc = self.nlc_flat_dict[tech_id][tech]

                        # get the least expensive NLC indices from the winners
                        tech_nlc_cheap = tech[np.where(tech_nlc == np.min(tech_nlc))]

                        # select a random index that has a winning cell for the check where multiple low NLC may exists
                        target_ix = np.random.choice(tech_nlc_cheap)

                        # add selected index to list
                        sited_list.append(target_ix)

                        # TODO:  make buffer inheritance to next suitability year optional
                        # TODO:  write out exclusion data after buffer applied
                        # apply buffer
                        result = buffer_flat_array(target_index=target_ix,
                                                   arr=self.cheapest_arr_1d,
                                                   nrows=self.cheapest_arr.shape[0],
                                                   ncols=self.cheapest_arr.shape[1],
                                                   ncells=self.technology_dict[tech_id]['buffer_in_km'],
                                                   set_value=0)

                        # unpack values
                        self.cheapest_arr_1d, buffer_indices_list = result

                        # update the number of sites left to site
                        required_sites -= 1

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

                    # update dictionary with how many plants are left to site
                    self.expansion_dict[tech_id] = self.expansion_dict[tech_id] - rdx.shape[0]

                    if self.verbose:
                        print('\nUpdate expansion plan to represent siting requirements:')
                        print(self.expansion_dict)

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

                    # show cheapest option, add 1 to the index to represent the technology number
                    self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

                    # flatten cheapest array to be able to use random
                    self.cheapest_arr_1d = self.cheapest_arr.flatten()

                    # check for any available grids to site in
                    self.avail_grids = np.where(self.cheapest_arr_1d > 0)[0].shape[0]

                    if self.verbose:
                        print(f'\nAvailable grid cells:  {self.avail_grids}')

        # reshape output array to 2D
        return self.sited_arr_1d.reshape(self.cheapest_arr.shape)
