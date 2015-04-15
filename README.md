# Github Report Card
[View at http://myosrc.appspot.com/](http://myosrc.appspot.com/)

An attempt to bring back the [previous OSRC](https://github.com/dfm/osrc) since it's currently down. Half of this code is copied from the original, the other half is made up.

## Dependencies
Running this locally requires the [Google App Engine SDK](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python) for python, and `pip` to install all the python dependencies.

You will also need to create a new [Github application](https://github.com/settings/applications) to be able to use Github's API locally with your own `client ID` and `client secret`.

## First time setup
This part is just installing the dependencies and only needs to be done once. Skip to Development if you did this part already.

1) Login into Github and create a new application at [https://github.com/settings/applications](https://github.com/settings/applications)
2) Enter a name, homepage url, and callback url. The name doesn't really matter. (I named mine along the lines of `osrc-development`.) The homepage url should be `http://localhost:8080` since this is the default url of GAE's dev server. The callback url should be `http://localhost:8080/callback`.
3) Register your application, and keep note of the `Client ID` and `Client Secret` for later.
4) In the `private` diretory, create the file `secret.py`. This will contain the client id, client secret, and a `session secret` for Flask. `secret.py` will contain the following content:
```py
class Secret:
	def __init__(self):
		self.session_secret = "<session secret key>"
		self.github_client_id = "<github client id>"
		self.github_client_secret = "<github client secret>"
```
Replace `<session secret key>` the a randomly generated string of your choice, `<github client id>` with your app's client id, and `<github client secret>` with your app's client secret.
5) Run the following script to create and pupulate a `lib/` directory which will contain all the python dependencies used in this app.
```sh
$ ./refresh_lib.sh
```


## Development
1) After cloning this repo, start the mongodb server
```sh
$ sudo mongod
```

2) Start the GAE development server (in the root directory of the repo)
```sh
$ dev_appserver.py .
```