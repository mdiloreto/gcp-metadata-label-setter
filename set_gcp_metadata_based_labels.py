import json
import re
from google.cloud import resourcemanager_v3
from google.cloud import asset_v1   
from google.cloud import compute_v1
from get_all_projects import GetGCPFoldersAndProjects
from google.protobuf import json_format

class SetMetadatabasedLabels:
    def __init__(self):
        self.required_label_keys = [
            'env',
            'data_center_location',
            'infrastructure_type',
            'region',
            'country',
            'network',
            'subnet',
            'os',
            'cloud',
            'zone',
            'machinetype',
            'project'
        ]

    def fetch_resources(self, project_id):
        try:
            client = asset_v1.AssetServiceClient()
            parent = f"projects/{project_id}"
            assets = client.list_assets(request={"parent": parent, "content_type": asset_v1.ContentType.RESOURCE, "asset_types": ["compute.googleapis.com/Instance"]})
            assets_json = json_format.MessageToJson(assets._pb)
            assets_data = json.loads(assets_json)
                    # Check if the 'assets' key exists and has data
            if assets_data.get('assets'):
                return assets_data
            else:
                print(f"No assets found for project: {project_id}")
                return []  # Return an empty list if no assets are found
        
        except Exception as e:
            print(f"Error in fetch_resources: {e}")
            return {}

    def merge_labels(self, metadata_labels, current_labels):
        if current_labels is None:
            current_labels = {}  # Initialize as an empty dict if None
        
        resultant_labels = {**current_labels, **metadata_labels}
        
        # Remove safe to remove keys... 
        safe_to_remove_keys = ['vpc', 'network', 'subnet', 'data_center', 'device_type']       
        
        for key in safe_to_remove_keys:
            resultant_labels.pop(key, None)  # Use pop to avoid KeyError if the key doesn't exist
        
        # Count total labels
        total_labels = len(resultant_labels)
        if total_labels > 64:
            # Prioritize keeping labels with non-empty, non-None values
            labels_with_values = {k: v for k, v in resultant_labels.items() if v not in [None, '']}
            labels_without_values = {k: v for k, v in resultant_labels.items() if v in [None, '']}

            # If reducing empty/non-None labels is enough
            excess_count = total_labels - 64
            
            if len(labels_without_values) > excess_count:
                # Remove some labels without values
                sorted_labels_without_values_keys = sorted(labels_without_values.keys())
                for key in sorted_labels_without_values_keys[:excess_count]:
                    del labels_without_values[key]
            # else:
            #     # If reducing empty/non-None labels not enough, sort all labels by their keys, and keep the first 64, prioritizing labels with values
            #     combined_labels_sorted = dict(sorted({**labels_with_values, **labels_without_values}.items(), key=lambda item: item[0]))
            #     resultant_labels = dict(list(combined_labels_sorted.items())[:64])
            #     return resultant_labels

            # Combine remaining labels with values and without values after removal
            resultant_labels = {**labels_with_values, **labels_without_values}
   
        return resultant_labels
    
    def create_metadata_labels(self, asset, project_id, asset_type, asset_name, asset_zone):

        asset_zone = asset.get('resource', {}).get('location', '').split('/')[-1]
        asset_machinetype = asset.get('resource', {}).get('data', {}).get('machineType', '').split('/')[-1]
        asset_os = 'unknown'

        # Get the disks list
        disks = asset.get('resource', {}).get('data', {}).get('disks', [])
        # Initialize os_features to store OS features from all disks
        os_features = []
        for disk in disks:
            guest_os_features = disk.get('guestOsFeatures', [])
            for feature in guest_os_features:
                os_features.append(feature.get('type'))

        # Checking guest OS features first
        for feature in os_features:
            if feature == 'WINDOWS':
                asset_os = 'windows'
                break

        # Then check licenses if OS is still unknown.
        if asset_os == 'unknown':
            for disk in disks:
                licenses = disk.get('licenses', [])  # Check all disks for licenses
                for license_url in licenses:
                    license_os = license_url.split('/')[-1].lower()  # Normalize for case-insensitive comparison
                    if 'windows' in license_os:
                        asset_os = 'windows'
                        break
                    if any(substring in license_os for substring in ['debian', 'redhat', 'ubuntu', 'centos', 'fedora', 'suse', 'opensuse', 'arch', 'almalinux', 'rocky']):
                        asset_os = 'linux'
                if asset_os != 'unknown':  # Exit if OS is determined
                    break

        project_name_lower = project_id.lower()
        if 'dev' in project_name_lower:
            asset_env = 'development'
        elif 'test' in project_name_lower:
            asset_env = 'testing'
        elif 'prod' in project_name_lower:
            asset_env = 'production'
        elif 'dr' in project_name_lower:
            asset_env = 'dr'
        elif 'hub' in project_name_lower:
            asset_env = 'hub'
        else:
            asset_env = 'Unknown'
        
        if 'nonpci' in project_name_lower:
            asset_pci_env = "false"
        elif 'pci' in project_name_lower:
            asset_pci_env = "true"
        else:
            asset_pci_env = "false"
           
        network_info = asset.get('resource', {}).get('data', {}).get('networkInterfaces', [])   
        network_labels = {}
        
        for index, interface in enumerate(network_info):
            network_key = f'network{index+1}'
            subnet_key = f'subnet{index+1}'
            
            network_url = interface.get('network', None)
            subnet_url = interface.get('subnetwork', None)

            network_id = network_url.split('/')[-1] if network_url else None
            subnet_id = subnet_url.split('/')[-1] if subnet_url else None

            network_labels[network_key] = network_id
            network_labels[subnet_key] = subnet_id
            
                    
        asset_name_lower = asset_name.lower()
        #AMERICAS
        if 'usa' in asset_name_lower:
            asset_country = 'usa'
        elif 'bra' in asset_name_lower:
            asset_country = 'brazil'
        elif 'ecu' in asset_name_lower:
            asset_country = 'ecuador'
        elif 'mex' in asset_name_lower:
            asset_country = 'mexico'
        elif 'hub' in asset_name_lower:
            asset_country = 'dr'
            
        #APAC
        elif 'phi' in asset_name_lower:
            asset_country = 'philippines'
        elif 'aus' in asset_name_lower:
            asset_country = 'australia'

        #EMEA
        elif 'ger' in asset_name_lower:
            asset_country = 'germany'            
           
        #UNKNOWN    
        else:
            asset_country = 'unknown'
            
        ### ASSET Region
        
        if 'na' in project_id:
            asset_region = "amer"
        elif 'amr' in project_id:
            asset_region = "amer"
        elif 'amer' in project_id:
            asset_region = "amer"
        elif 'emea' in project_id:
            asset_region = "emea"
        elif 'apac' in project_id: 
            asset_region = "apac"
        else: 
            asset_region = "unknown"
        
        if 'us-east4' in asset_zone:
            asset_datacenter = "ashburn northern virginia usa"
        elif 'europe-west3' in asset_zone:
            asset_datacenter = "frankfurt germany"
        elif 'asia-southeast1' in asset_zone:
            asset_datacenter = "singapore jurong west"
        elif 'us-west2' in asset_zone:
            asset_datacenter = "los angeles usa"
        elif 'europe-north1' in asset_zone:
            asset_datacenter = "hamina finland"
        elif 'europe-west2' in asset_zone:
            asset_datacenter = "london england"
        else:
            asset_datacenter = asset_zone
    
        metadata_labels = {
            'env': asset_env,
            'data_center_location': asset_datacenter,
            'infrastructure_type': asset_type,
            'region': asset_region, 
            'country': asset_country,
            'zone': asset_zone,
            'cloud': "google cloud",
            'project': project_id,  
            'pci_compliance': asset_pci_env,
            }
        
        ### >>>>>>>>>>>> ONLY FOR VM INSTANCES <<<<<<<<<<<<<<
        
        if asset_type == 'Instance':
            asset_status = asset.get('resource', {}).get('data', {}).get('status')
            metadata_labels.update(network_labels)
            metadata_labels.update({'os': asset_os, 'machinetype': asset_machinetype, 'status': asset_status})
            

        return metadata_labels
    
    def sanitize_label_value(self, value):
        """Sanitize label values to conform to Compute Engine's requirements."""
        if value is None:
            return None  # You may want to return 'unknown' or some default value instead
        # Replace any disallowed characters with '-', ensure lowercase, and trim to 63 characters
        return re.sub(r'[^a-z0-9_-]', '-', value.lower())[:63]

    def set_instance_labels(self, project_id, zone, instance_name, labels):
        try:
            sanitized_labels = {k: self.sanitize_label_value(v) for k, v in labels.items() if v is not None}

            compute_client = compute_v1.InstancesClient()
            # Retrieve the current instance to get its label fingerprint.
            instance = compute_client.get(project=project_id, zone=zone, instance=instance_name)
            
            # Prepare the request to set labels.
            label_request = compute_v1.SetLabelsInstanceRequest(
                project=project_id,
                zone=zone,
                instance=instance_name,
                instances_set_labels_request_resource=compute_v1.InstancesSetLabelsRequest(
                    label_fingerprint=instance.label_fingerprint,
                    labels=sanitized_labels  # Here, labels is a dictionary of labels you want to set/update.
                )
            )
            
            # Execute the request to set labels.
            operation = compute_client.set_labels(request=label_request)
            
            # Wait for the operation to complete.
            operation_client = compute_v1.ZoneOperationsClient()
            wait_request = compute_v1.WaitZoneOperationRequest(
                project=project_id,
                zone=zone,
                operation=operation.name
            )
            result = operation_client.wait(request=wait_request)
            
            print(f"Set labels {sanitized_labels} on instance {instance_name}")
            return result
        except Exception as e:
            print(f"Error in set_instance_labels: {e}")                    
    
    def main(self, organization_id):
        try:
            if organization_id == "0":
                get_projects_class = GetGCPFoldersAndProjects(organization_id)
                get_projects = get_projects_class.get_all_projects_no_org()
            else:          
                get_projects_class = GetGCPFoldersAndProjects(organization_id)
                get_projects = get_projects_class.get_all_projects_with_org()
                
            print(get_projects)
            
            #projects = ["apac-sgp-dr-nonpci-prj"] # only for 1 project to test
            resources = {}
            for project_id in get_projects:
                print(f"Fetching Resources in Project {project_id}", flush=True)
                resources = self.fetch_resources(project_id)
                if resources and "assets" in resources and resources["assets"]:
                    for asset in resources["assets"]:
                        # Get main attributes
                        asset_type = asset.get('assetType').split('/')[-1]
                        asset_name = asset.get('name').split('/')[-1]
                        asset_zone = asset.get('resource', {}).get('location')

                        current_label_status = asset.get('resource', {}).get('data', {}).get('labels')
                        metadata_labels = self.create_metadata_labels(asset, project_id, asset_type, asset_name, asset_zone)
                        resultant_labels = self.merge_labels(metadata_labels, current_label_status)
                        print(resultant_labels)
                        if asset_type == "Instance":
                            self.set_instance_labels(project_id, asset_zone, asset_name, resultant_labels)
                    
                    resources = self.fetch_resources(project_id)
                    for asset in resources["assets"]:
                        current_label_status = asset.get('resource', {}).get('data', {}).get('labels')
                else:
                    print(f"No assets to process for project: {project_id}")
                    
        except Exception as e:
            print(f"An error occurred during processing: {e}")

### USAGE: 

# organization_id = "0"
# # Initialize the SetMetadatabasedLabels class with a project ID
# label_setter = SetMetadatabasedLabels()

# # Run the main function to start setting labels based on metadata
# label_setter.main(organization_id)