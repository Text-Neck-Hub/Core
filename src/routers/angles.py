# from fastapi import APIRouter, HTTPException, status
# from src.models.users import User, UserSignIn
# from src.database.connection import Database

# user_router = APIRouter(
#     prefix="/users",
#     tags=["Users"]
# )
# user_db = Database(User)


# @user_router.post("/signup")
# async def create_(user: User):
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


# @user_router.post("/signin")
# async def sign_user_in(credentials: UserSignIn):
#     """회원가입이 끝난 회원 로그인하는 API"""
#     if credentials.email not in users:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#     stored_user = users[credentials.email]
#     if stored_user.password != credentials.password:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Invalid password"
#         )
#     return {"message": "User successfully signed in"}
