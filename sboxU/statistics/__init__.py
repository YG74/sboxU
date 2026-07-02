# -*- python -*-

"""This module provides tools to study the "statistical" properties of vectorial Boolean functions.

"Statistical" should be understood in the sense of "statistical cryanalysis"...
"""

from sboxU.statistics.cython_functions import \
    differential_spectrum, ddt, differential_uniformity, is_differential_uniformity_smaller_than, early_differential_spectrum_compare, \
    walsh_transform, walsh_spectrum, absolute_walsh_spectrum, lat, invert_lat, linearity, \
    boomerang_spectrum, bct, boomerang_uniformity, \
    fbct_spectrum, bct, boomerang_uniformity, \
    fbct_spectrum, fbct,xddt,yddt,zddt, linear_structures, linear_structures_vectorial, linear_structures_vectorial_spectrum


from sboxU.statistics.anomalies import \
    ddt_coeff_probability, expected_differential_uniformity_distribution_permutation, \
    lat_coeff_probability_permutation, lat_coeff_probability_function, expected_linearity_distribution_permutation, expected_linearity_distribution_function, \
    bct_coeff_probability, expected_boomerang_uniformity_distribution_permutation, \
    probability_of_max_and_occurrences, get_proba_func, \
    table_anomaly, table_negative_anomaly