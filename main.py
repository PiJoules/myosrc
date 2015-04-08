"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, jsonify, render_template, request, url_for, flash, redirect, session
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

import requests
import json

from private.secret import Secret
secret = Secret()
app.secret_key = secret.session_secret

from flask.ext.github import GitHub
app.config['GITHUB_CLIENT_ID'] = secret.github_client_id
app.config['GITHUB_CLIENT_SECRET'] = secret.github_client_secret
github = GitHub(app)

"""
session keys:
access_token
user
"""


@app.route('/', methods=["GET"])
def index():
    if "user" in session:
        return render_template("index.html",user=session["user"])
    else:
        return render_template("index.html")

@app.route('/login')
def login():
    return github.authorize()

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect("/")

    session["access_token"] = oauth_token
    return redirect("/osrc")


@github.access_token_getter
def token_getter():
    if "access_token" in session:
        return session["access_token"]


@app.route('/osrc', methods=["GET"])
def osrc():
    """Return a friendly HTTP greeting."""
    """user="jmal0"
    response = json.load(urllib2.urlopen("https://api.github.com/users/" + user + "/repos"))
    repos = dict()
    allLanguages = dict()
    for repo in response:
    	repoName = repo["name"]
    	languages = json.load(urllib2.urlopen("https://api.github.com/repos/" + user + "/" + repoName + "/languages"))
    	for language in languages:
            if not language in allLanguages:
                allLanguages[language] = languages[language]
            else:
                allLanguages[language] += languages[language]
    	repos[repoName] = languages

    return jsonify(
    	repos=repos,
    	languages=allLanguages
    )"""
    repo_dict = github.get('user')
    return str(repo_dict)


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
