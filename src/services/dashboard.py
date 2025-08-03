from ..database.orm import Database


class DashBoard:
    @staticmethod
    async def get_dashboard(user_id):
        Database.get(user_id)
