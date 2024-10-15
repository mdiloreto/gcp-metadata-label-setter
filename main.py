import json
from set_gcp_metadata_based_lables import SetMetadatabasedLabels 
from datetime import datetime
from flask import abort


def start_label_setter(request):
    try:
        organization_id = "468700285980"
        # Initialize the SetMetadatabasedLabels class with a project ID
        label_setter = SetMetadatabasedLabels()

        # Run the main function to start setting labels based on metadata
        label_setter.main(organization_id)
    except Exception as e:
        print(f'start_label_setter function ended with error: {e}')

    return 'start_label_setter function ended'