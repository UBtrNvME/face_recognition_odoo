class UnrecognizableDocument(Exception):
    """Document which has been parsed as an image cannot be recognised"""
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload