from google.cloud import resourcemanager_v3

# Permissions needed at Org Level: 
#   FolderViewer
class GetGCPFoldersAndProjects:
    def __init__(self, organization_id):
        self.organization_id = organization_id
        self.client_folders = resourcemanager_v3.FoldersClient()
        self.client_projects = resourcemanager_v3.ProjectsClient()

    def get_folders_hierarchy(self, client, parent, path="", folders_id_list=None):
        if folders_id_list is None:
            folders_id_list = []
        try:
            request = resourcemanager_v3.ListFoldersRequest(parent=parent)
            response = client.list_folders(request=request)
            hierarchy = []
            for folder in response:
                current_path = f"{path}/{folder.display_name}" if path else folder.display_name
                print(f"Folder Path: {current_path}, Folder ID: {folder.name}")
                folder_id = folder.name.split('/')[1]
                folders_id_list.append(folder_id)
                sub_hierarchy = self.get_folders_hierarchy(client, folder.name, current_path, folders_id_list)
                hierarchy.append({
                    'name': folder.display_name,
                    'id': folder.name,
                    'path': current_path,
                    'subfolders': sub_hierarchy
                })
        except Exception as e:
            print(f"Error in get_folders_hierarchy: {e}")
        return folders_id_list

    def print_hierarchy(self, hierarchy, level=0):
        indent = "  " * level
        try:
            for folder in hierarchy:
                print(f"{indent}- {folder['name']} (ID: {folder['id']}, Path: {folder['path']})")
                if folder['subfolders']:
                    self.print_hierarchy(folder['subfolders'], level + 1)
        except Exception as e:
            print(f"Error in print_hierarchy: {e}")

    def get_folder_ids_from_hierarchy(self, hierarchy, folder_ids_list=None):
        if folder_ids_list is None:
            folder_ids_list = []
        try:
            for folder in hierarchy:
                folder_id = folder['id'].split('/')[1]
                folder_ids_list.append(folder_id)
                if folder['subfolders']:
                    self.get_folder_ids_from_hierarchy(folder['subfolders'], folder_ids_list)
        except Exception as e:
            print(f"Error in get_folder_ids_from_hierarchy: {e}")
        return folder_ids_list

    def get_all_projects_in_folder(self, folder_ids_list):
        project_list = []
        try:
            for folder_id in folder_ids_list:
                print(f"Listing projects for Folder: {folder_id}")
                request = resourcemanager_v3.ListProjectsRequest(parent=f"folders/{folder_id}")
                page_result = self.client_projects.list_projects(request=request)
                for project in page_result:
                    print(f"Found project: {project.project_id}")
                    project_list.append(project.project_id)
        except Exception as e:
            print(f"Error in get_all_projects_in_folder: {e}")
            
        return project_list
    
    def get_all_projects_no_org(self):
        project_list = []
        try:
            # No 'parent' parameter needed for listing all projects
            page_result = self.client_projects.search_projects()
            for project in page_result:
                print(f"Found project: {project.project_id} ({project.name})")
                project_list.append(project.project_id)
        except Exception as e:
            print(f"Error in get_all_projects: {e}")
            
        return project_list

    def get_all_projects_with_org(self):
        folders_id_list = self.get_folders_hierarchy(self.client_folders, f"organizations/{self.organization_id}")
        projects = self.get_all_projects_in_folder(folders_id_list)
        
        return projects
    
    # ### USAGE:
    #             if organization_id == "0":
    #             get_projects_class = GetGCPFoldersAndProjects(organization_id)
    #             get_projects = get_projects_class.get_all_projects_no_org()
    #         else:          
    #             get_projects_class = GetGCPFoldersAndProjects(organization_id)
    #             get_projects = get_projects_class.get_all_projects_with_org()