import bcrypt

MIN_LENGTH = 1
MAX_LENGTH = 72  # bcrypt limitation
SALT_LENGTH = 20
    
def validate(password: str):
    if len(password) < MIN_LENGTH:
        raise ValueError(f"Password too short (min {MIN_LENGTH} characters)")
    if len(password) > MAX_LENGTH:
        raise ValueError(f"Password too long (max {MAX_LENGTH} characters)")

def hash(password: str, salt: str|None = None) -> str:
    if salt is None:
        salt = bcrypt.gensalt()
    else:
        salt = salt.encode("ascii")
    hash_bytes = bcrypt.hashpw(password.encode("ascii"), salt)
    return hash_bytes.decode("ascii")

def compare(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("ascii"), hashed_password.encode("ascii"))
