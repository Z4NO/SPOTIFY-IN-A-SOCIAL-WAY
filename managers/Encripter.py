from cryptography.fernet import Fernet

class Encripter:
    def __init__(self, key):
        self.key = key
        self.cipher_suite = Fernet(self.key)

    def _encript(self, content):
        return self.cipher_suite.encrypt(content.encode())

    def _decript(self, conetent):
        return self.cipher_suite.decrypt(conetent).decode()
