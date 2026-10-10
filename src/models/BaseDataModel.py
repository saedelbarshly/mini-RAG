from helpers.config import get_settings

class BaseDataModel:
    """
    Base class for data models.
    """

    def __init__(self, db_client: object):
        self.db_client = db_client
        self.settings = get_settings()