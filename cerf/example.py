if __name__ == '__main__':

    import cerf

    # sample year
    yr = 2010

    # load the sample configuration file path for the target year
    config_file = cerf.config_file(yr)

    # run the configuration for the target year and return a data frame
    result_df = cerf.run(config_file, write_output=False)

    result_df.to_csv('/Users/d3y010/Desktop/cerf_result.csv', index=False)

