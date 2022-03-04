#!/usr/bin/env python3
"""
Helper functions for defining types of argparse parameters
"""
import argparse
# Reference: https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    """
    Validates that an argparse argument is a boolean value.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
# ==============================================================================
# Reference:
# https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def valid_sorter(v):
    """
    Validates that argparse sort-on argument is valid value.
    """
    valid_sort_criteria = ["nickname", "first_name", "last_name", "username", "emoji"]
    if v.lower() in valid_sort_criteria:
        return v.lower()

    else:
        print(f"Got {v}")
