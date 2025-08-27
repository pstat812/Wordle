"""
MongoDB Database Connection and User Management Module

This module handles all database operations including user authentication,
registration, and game data management using MongoDB.
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

# Get logger
logger = logging.getLogger('wordle_server')


class DatabaseManager:
    """
    MongoDB database manager for user authentication and game data.
    """
    
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.gameplay_collection = None
        self._connect()
    
    def _connect(self) -> bool:
        """
        Establish connection to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            uri = "mongodb+srv://admin:admin123@wordle.vhfgxe8.mongodb.net/?retryWrites=true&w=majority&appName=Wordle"
            
            # Create a new client and connect to the server
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            
            # Send a ping to confirm a successful connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
            # Access the wordle database
            self.db = self.client.wordle
            self.users_collection = self.db.user
            self.gameplay_collection = self.db.gameplay
            
            # Create indexes for better performance
            self._create_indexes()
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    def _create_indexes(self) -> None:
        """Create database indexes for optimized queries."""
        try:
            # Create unique index on username
            self.users_collection.create_index("username", unique=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Username for the new user
            password: Plain text password
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Validate input
            if not username or not password:
                return {"success": False, "error": "Username and password are required"}
            
            if len(username) < 3:
                return {"success": False, "error": "Username must be at least 3 characters long"}
            
            if len(password) < 6:
                return {"success": False, "error": "Password must be at least 6 characters long"}
            
            # Hash the password
            hashed_password = self._hash_password(password)
            
            # Create user document
            user_doc = {
                "username": username.lower(),  # Store username in lowercase for consistency
                "password": hashed_password,
                "games_played": 0,
                "games_won": 0
            }
            
            # Insert user into database
            result = self.users_collection.insert_one(user_doc)
            
            if result.inserted_id:
                logger.info(f"New user registered: {username}")
                return {"success": True, "message": "User registered successfully"}
            else:
                return {"success": False, "error": "Failed to register user"}
                
        except DuplicateKeyError:
            logger.warning(f"Registration attempt with existing username: {username}")
            return {"success": False, "error": "Username already exists"}
        except PyMongoError as e:
            logger.error(f"Database error during registration: {e}")
            return {"success": False, "error": "Database error occurred"}
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            return {"success": False, "error": "An unexpected error occurred"}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            dict: Result with success status and user data if successful
        """
        try:
            # Validate input
            if not username or not password:
                return {"success": False, "error": "Username and password are required"}
            
            # Hash the password for comparison
            hashed_password = self._hash_password(password)
            
            # Find user in database
            user = self.users_collection.find_one({
                "username": username.lower(),
                "password": hashed_password
            })
            
            if user:
                logger.info(f"User authenticated successfully: {username}")
                return {
                    "success": True,
                    "user": {
                        "username": user["username"],
                        "games_played": user.get("games_played", 0),
                        "games_won": user.get("games_won", 0)
                    }
                }
            else:
                # Check if user exists but password is wrong
                existing_user = self.users_collection.find_one({"username": username.lower()})
                if existing_user:
                    logger.warning(f"Wrong password attempt for user: {username}")
                    return {"success": False, "error": "Incorrect password"}
                else:
                    logger.warning(f"Login attempt for non-existent user: {username}")
                    return {"success": False, "error": "User does not exist"}
                    
        except PyMongoError as e:
            logger.error(f"Database error during authentication: {e}")
            return {"success": False, "error": "Database error occurred"}
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return {"success": False, "error": "An unexpected error occurred"}
    
    def update_user_stats(self, username: str, won: bool) -> bool:
        """
        Update user game statistics.
        
        Args:
            username: Username to update
            won: Whether the user won the game
            
        Returns:
            bool: True if update successful
        """
        try:
            update_data = {"$inc": {"games_played": 1}}
            if won:
                update_data["$inc"]["games_won"] = 1
            
            result = self.users_collection.update_one(
                {"username": username.lower()},
                update_data
            )
            
            return result.modified_count > 0
            
        except PyMongoError as e:
            logger.error(f"Database error updating user stats: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating user stats: {e}")
            return False
    
# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager
