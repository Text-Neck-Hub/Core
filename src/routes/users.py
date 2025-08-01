from fastapi import APIRouter, HTTPException, status
from ..models.users import User
from ..database.connection import Database


user_router = APIRouter(
    prefix="core/users",
    tags=["Users"]
)
user_db = Database(User)


# @user_router.get("/dashboard")
# async def sign_new_user(user: User):
#     user_exist = await User.find_one(User.email == user.email)
#     if user_exist:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="User with email provided exists already"
#         )
#     await user_db.save(user)
#     return {
#         "message": "User created successfully!!"
#     }
