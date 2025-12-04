"""
Password hashing using Argon2.

Argon2 is the winner of the Password Hashing Competition and is
recommended for new applications.
"""

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError


class PasswordHasher:
    """
    Secure password hashing using Argon2id.
    
    Argon2id is a hybrid of Argon2i (side-channel resistant) and
    Argon2d (GPU resistant), providing the best of both.
    
    Default parameters are chosen for a good balance of security
    and performance on modern hardware.
    """
    
    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,  # 64 MB
        parallelism: int = 4,
    ):
        """
        Initialize the password hasher.
        
        Args:
            time_cost: Number of iterations (default: 3)
            memory_cost: Memory usage in kibibytes (default: 64 MB)
            parallelism: Number of parallel threads (default: 4)
        """
        self._hasher = Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=32,
            salt_len=16,
            type=Argon2Hasher.Type.ID,  # Argon2id
        )
    
    def hash(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Argon2id hash string
        """
        return self._hasher.hash(password)
    
    def verify(self, password: str, hash: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Plain text password to verify
            hash: Stored hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            self._hasher.verify(hash, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False
    
    def needs_rehash(self, hash: str) -> bool:
        """
        Check if a hash needs to be rehashed.
        
        This is useful when upgrading security parameters.
        
        Args:
            hash: Stored hash to check
            
        Returns:
            True if hash should be regenerated
        """
        return self._hasher.check_needs_rehash(hash)


# Singleton instance with recommended parameters
password_hasher = PasswordHasher()

