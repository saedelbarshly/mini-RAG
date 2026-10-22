from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select

class AssetModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = db_client


    @classmethod
    async def creat_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance



    async def create_asset(self, asset: Asset) -> Asset:

        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)

            await session.refresh(asset)

        return asset


    async def get_all_project_assets(self, asset_project_id: int, asset_type: str) -> list[Asset]:

        async with self.db_client() as session:
            query = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_type == asset_type
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_asset_record(self, asset_project_id: int, asset_name: str) -> Asset:

        async with self.db_client() as session:
            query = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
