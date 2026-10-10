from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum


 
class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = db_client[DataBaseEnum.Collection_PROJECTS.value]


    async def create_project(self, project_data: dict) -> Project:
        """
        Create a new project in the database.

        Args:
            project_data (dict): The data for the new project.

        Returns:
            Project: The created project object.
        """
        project = Project(**project_data)
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        return project

    async def get_project(self, project_id: str) -> Project:
        """
        Retrieve a project from the database by its project_id.

        Args:
            project_id (str): The ID of the project to retrieve.

        Returns:
            Project: The retrieved project object.
        """
        project = await self.collection.find_one({"project_id": project_id})
        return Project(**project)


    async def get_project_or_create_one(self, project_id: str) -> Project:
        """
        Retrieve a project from the database by its project_id.
        If the project does not exist, create a new one.

        Args:
            project_id (str): The ID of the project to retrieve or create.

        Returns:
            Project: The retrieved or created project object.
        """  
        project = await self.get_project(project_id=project_id)
        if not project:
            project = await self.create_project(project_data={"project_id": project_id})
        return project



    async def get_all_projects(self, page: int=1, page_size: int=10) -> list[Project]:
        """
        Retrieve all projects from the database.

        Args:
            page (int): The page number to retrieve.
            page_size (int): The number of projects to retrieve per page.
      
        Returns:
            list[Project]: A list of all project objects.
        """
        # projects = await self.collection.find().skip((page - 1) * page_size).limit(page_size).to_list(length=None)
        # return [Project(**project) for project in projects] 

        total_documents = await self.collection.count_documents({})

        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        projects = []

        async for project in cursor:
            projects.append(Project(**project))

        return projects, total_pages