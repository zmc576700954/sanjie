class UserService:
    def __init__(self):
        self.users = {"admin": "secret"}

    def authenticate(self, username: str, token: str) -> bool:
        # BUG: Anti-pattern in Python, should use 'is None' instead of '== None'
        if token is None:
            print("Token missing.")
            return False
            
        if username in self.users and self.users[username] == token:
            return True
        return False
