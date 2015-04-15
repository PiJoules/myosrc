## Private Directory
The `private` directory which contains stuff you guys shouldn't know like usernames and passwords.


### secret.py
```py
class Secret:
	def __init__(self):
		self.session_secret = "<session secret key>"
		self.github_client_id = "<github client id>"
		self.github_client_secret = "<github client secret>"
```