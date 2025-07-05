# # tools/create_session.py
# import sys
# import os

# # This allows the script to import from the parent directory
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# from app.core.telethon_client import get_client

# async def create_new_session():
#     session_name = input("Enter a unique session name for the new user (e.g., user_john): ")
#     if not session_name:
#         print("Session name cannot be empty.")
#         return

#     client = get_client(session_name)
    
#     async with client:
#         # The login flow will start here if the session file doesn't exist
#         me = await client.get_me()
#         print(f"\n✅ Success! Session file for {me.first_name} (@{me.username}) created.")
#         print("Please add their configuration to config.py before starting the main service.")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(create_new_session())