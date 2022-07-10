import json

class Database:
    def __init__(self, path, contents = None):
        self.path = path
        self.contents = contents
        self.connect()

    def connect(self):
        with open(self.path, "r") as f:
            self.contents = json.loads(f.read())
        self.connected = True
    
    def commit(self):
        with open(self.path, "w") as f:
            f.write(json.dumps(self.contents, indent = 2))

    def update(self, contents):
        self.contents = contents

    def disconnect(self):
        self.connected = False
        # self.commit()
