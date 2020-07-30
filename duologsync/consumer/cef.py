"""
Definition of functions for creating CEF-type logs
"""

from duologsync.config import Config
from duologsync.__version__ import __version__

# What follows are required prefix fields for every CEF message
CEF_VERSION = 'CEF:0'
DEVICE_VENDOR = 'Duo Security'
DEVICE_PRODUCT = 'DuoLogSync'
DEVICE_VERSION = __version__

# Values allowed: 0 - 10 where 10 indicates the most important event
SEVERITY = '5'

def log_to_cef(log, keys_to_labels):
    """
    Create and return a CEF-type log given a Duo log.

    @param log              The log to convert into a CEF-type log
    @param keys_to_labels   Dictionary of keys used for retrieving values and
                            the associated labels those values should be given

    @return a CEF-type log created from the given log
    """

    # Additional required prefix fields
    signature_id = log['eventtype']
    name = log['eventtype']

    # Construct the beginning of the CEF message
    header = '|'.join([
        CEF_VERSION, DEVICE_VENDOR, DEVICE_PRODUCT, DEVICE_VERSION,
        signature_id, name, SEVERITY
    ])

    extension = _construct_extension(log, keys_to_labels)
    cef_log = header + '|' + extension

    return cef_log

def _construct_extension(log, keys_to_labels):
    """
    Create the extension for a CEF message using the given log and dictionary.

    @param log              The log to convert into a CEF message
    @param keys_to_labels   Dictionary of keys used for retrieving values and
                            the associated labels those values should be given

    @return the extension field for a CEF message
    """

    # List of additional fields to add to the CEF message beyond whats required
    extensions = []

    # Keep track of the number for the custom string being created
    custom_string = 1

    for keys, label in keys_to_labels.items():
        value = Config.get_value_from_keys(log, keys)
        label_name = label['name']

        # Need to generate a custom label
        if label['is_custom']:
            custom_label = f"cs{custom_string}"
            custom_extension = custom_label + 'Label' + '=' + label_name
            extensions.append(custom_extension)
            custom_string += 1
            label_name = custom_label

        extension = label_name + '=' + str(value)
        extensions.append(extension)

    extensions = ' '.join(extensions)
    return extensions
