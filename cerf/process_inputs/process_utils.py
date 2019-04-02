import os

import untangle


def get_states_dict(states_xml_file, state_id_attr='id'):
    """Generate a dictionary of {state_id: state_name, ...}

    :param states_xml_file:             Full path with file name and extension to
                                        the input states.xml file.

    :param state_id_field:              Name of the state ID XML attribute. Default `id`.

    :return:                            A dictionary of {state_id: state_name, ...}.

    """
    xml = untangle.parse(states_xml_file)

    return {i[state_id_attr]: i.cdata for i in xml.states.state}


