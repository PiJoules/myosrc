## Private Directory
The `private` directory which contains stuff you guys shouldn't know like usernames and passwords. Though I will give you the contents of them since they are required for running @channel.


### secret.py
```py
class Secret:
	def __init__(self):
		self.session_secret = "<session secret key>""
		self.github_client_id = "<github client id>"
		self.github_client_secret = "<github client secret>"
```

### mongoClientConnection.py
```py
from pymongo import MongoClient
import os

class MongoClientConnection:
	def __init__(self):
		# check if on GAE
		if (os.getenv('SERVER_SOFTWARE') and os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
			self.connection = MongoClient("<MongoDB URI>")
		# otherwise, connect to localhost
		else:
			self.connection = MongoClient("mongodb://127.0.0.1:27017/osrc")
```