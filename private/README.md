## Private Directory
The `private` directory which contains stuff you guys shouldn't know like usernames and passwords. Though I will give you the contents of them since they are required for running @channel.


### secret.py
```py
class Secret:
	def __init__(self):
		self.session_secret = "<session secret key>"
		self.github_client_id = "<github client id>"
		self.github_client_secret = "<github client secret>"
```