"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask.ext.github import GitHub
from private.secret import Secret
import logging
import os
import math
import operator
from datetime import datetime
import json
from requests.auth import HTTPBasicAuth
import requests
from google.appengine.api import urlfetch
from flask import Flask, jsonify, render_template, request, url_for, flash, redirect, session, current_app
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

urlfetch.set_default_fetch_deadline(45)


secret = Secret()
app.secret_key = secret.session_secret

app.config['GITHUB_CLIENT_ID'] = secret.github_client_id
app.config['GITHUB_CLIENT_SECRET'] = secret.github_client_secret
github = GitHub(app)


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html", is_logged_in=is_logged_in())


@app.route('/login')
def login():
    return github.authorize()


@app.route('/logout')
def logout():
    if "access_token" in session:
        # delete the authentication
        requests.delete("https://api.github.com/applications/" + secret.github_client_id + "/tokens/" +
                        session["access_token"], auth=HTTPBasicAuth(secret.github_client_id, secret.github_client_secret))

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
    if not "access_token" in session:
        return redirect("/login")

    osrc_raw = raw_osrc_data()

    # Load the list of adjectives.
    with current_app.open_resource("json/adjectives.json") as f:
        adjectives = json.load(f)

    # Load the list of languages.
    with current_app.open_resource("json/languages.json") as f:
        language_list = json.load(f)

    # Load the list of event action descriptions.
    with current_app.open_resource("json/event_actions.json") as f:
        event_actions = json.load(f)

    # Compute the name of the best description of the user's weekly schedule.
    with current_app.open_resource("json/week_types.json") as f:
        week_types = json.load(f)

    # Load the list of event verbs.
    with current_app.open_resource("json/event_verbs.json") as f:
        event_verbs = json.load(f)

    # most used language
    used_languages = osrc_raw["cumulative_languages"].keys()
    if len(used_languages) > 0:
        most_used_language = max(
            osrc_raw["cumulative_languages"].iteritems(), key=operator.itemgetter(1))[0]
    else:
        most_used_language = None

    # events
    events_counter = dict()
    count = 0
    for event in osrc_raw["events"]:
        if not event["type"] in events_counter:
            events_counter[event["type"]] = 1
        else:
            events_counter[event["type"]] += 1
    most_done_event = max(events_counter.iteritems(),
                          key=operator.itemgetter(1))[0]

    best_dist = -1
    week_type = None
    user_vector = osrc_raw["nomralized_events_vector"]
    for week in week_types:
        vector = week["vector"]
        norm = 1.0 / math.sqrt(sum([v * v for v in vector]))
        dot = sum([(v*norm-w) ** 2 for v, w in zip(vector, user_vector)])
        if best_dist < 0 or dot < best_dist:
            best_dist = dot
            week_type = week["name"]

    # Figure out the user's best time of day.
    with current_app.open_resource("json/time_of_day.json") as f:
        times_of_day = json.load(f)
    hours = osrc_raw["events_hours_vector"]
    best_time = None
    max_val = 0
    for i in range(len(hours)):
        if hours[i] > max_val:
            max_val = hours[i]
            best_time = i
    best_time_description = None
    for tod in times_of_day:
        times = tod["times"]
        if times[0] <= best_time < times[1]:
            best_time_description = tod["name"]
            break

    return render_template("osrc.html",
                           osrc_data=osrc_raw,
                           github_chart=osrc_raw["github_chart"],
                           avatar=osrc_raw["user"]["avatar_url"],
                           user=osrc_raw["name"],
                           first_name=osrc_raw["first_name"],
                           adjectives=adjectives,
                           language_list=language_list,
                           used_languages=used_languages,
                           sorted_cumulative_languages=osrc_raw["sorted_cumulative_languages"],
                           most_used_language=most_used_language,
                           event_actions=event_actions,
                           most_done_event=most_done_event,
                           week_type=week_type,
                           best_time=best_time,
                           best_time_description=best_time_description,
                           latest_repo_contributions=osrc_raw["latest_repo_contributions"][:5],
                           event_verbs=event_verbs,
                           unique_events=osrc_raw["unique_events"].keys(),
                           unique_events_obj=osrc_raw["unique_events"],
                           events_vector=osrc_raw["events_vector"],
                           weekly_unique_events=osrc_raw["weekly_unique_events"],
                           hourly_unique_events=osrc_raw["hourly_unique_events"],
                           )


# For displaying pretty json data
@app.route('/osrc_raw', methods=["GET"])
def osrc_raw():
    if not "access_token" in session:
        return redirect("/login")

    osrc_raw = raw_osrc_data()

    return jsonify(osrc_data=osrc_raw)


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500


def trimHTTP(url):
    if url.startswith("https://api.github.com/"):
        url = url[23:]  # trim the "https://api.github.com/" (23 chars)
    if url.endswith("{/privacy}"):
        url = url[:-10]  # trim last 10 chars
    return url


def raw_osrc_data():
    osrc_data = {}

    # check if user
    user_info = github.get("user")

    repos = github.get("user/repos")
    all_languages = {}
    for repo in repos:
        repo_name = repo["name"]
        languages_url = repo["languages_url"]
        languages = github.get(trimHTTP(languages_url))
        all_languages[repo_name] = languages
    events = github.get(trimHTTP(user_info["events_url"]), params={
                        "per_page": 100})  # won't return more than 100 per page

    # user
    osrc_data["user"] = user_info
    name = user_info["name"]
    osrc_data["login"] = user_info["login"]
    osrc_data["github_chart"] = "http://ghchart.rshah.org/" + \
        user_info["login"]
    osrc_data["name"] = name
    split_name = name.split()
    osrc_data["first_name"] = name.split()[0]
    if len(split_name) > 1:
        osrc_data["last_name"] = name.split()[1]

    # languages
    cumulative_languages = {}
    for repo in all_languages:
        repo_languages = all_languages[repo]
        for language in repo_languages:
            bytes_written = repo_languages[language]
            if not language in cumulative_languages:
                cumulative_languages[language] = bytes_written
            else:
                cumulative_languages[language] += bytes_written

    osrc_data["repos"] = repos
    osrc_data["all_languages"] = all_languages
    osrc_data["cumulative_languages"] = cumulative_languages
    osrc_data["sorted_cumulative_languages"] = sorted(
        cumulative_languages.items(), key=operator.itemgetter(1), reverse=True)

    # events
    osrc_data["events"] = events

    # work schedule
    event_dates = []
    events_vector = [0, 0, 0, 0, 0, 0, 0]  # sunday is first
    events_hours_vector = [0]*24  # initialize list of zeros
    latest_repo_contributions = []
    recorded_repos = []

    unique_events = {}  # unique events over past received events
    # make sure each dict has each of the event types
    for event in events:
        unique_events[event["type"]] = 0
    weekly_unique_events = [unique_events.copy()
                            for i in range(7)]  # unique events over each week
    hourly_unique_events = [unique_events.copy()
                            for i in range(24)]  # unique events over each hour
    for event in events:
        date_string = event["created_at"]
        date_obj = datetime.strptime(
            date_string, "%Y-%m-%dT%H:%M:%SZ")  # monday is first
        event_dates.append(date_obj)

        # work days vector
        # do math to shift day over by 1
        actual_day = (date_obj.weekday()+1) % 7
        events_vector[actual_day] += 1

        # most worked hour
        events_hours_vector[date_obj.hour] += 1

        # latest repo contributions
        if event["type"] == "PushEvent":
            name = event["repo"]["name"]
            url = "https://github.com/" + name
            latest_repo_contributions.append((date_obj, name, url))

        unique_events[event["type"]] += 1
        weekly_unique_events[actual_day][event["type"]] += 1
        # start at 2am instead of 12am because the original javascript code starts at 2am for some reason
        hourly_unique_events[(date_obj.hour+2) % 24][event["type"]] += 1

    norm = math.sqrt(sum([v*v for v in events_vector]))
    nomralized_events_vector = [float(v)/norm for v in events_vector]

    osrc_data["event_dates"] = event_dates
    osrc_data["events_vector"] = events_vector
    osrc_data["nomralized_events_vector"] = nomralized_events_vector
    osrc_data["events_hours_vector"] = events_hours_vector
    osrc_data["unique_events"] = unique_events
    osrc_data["weekly_unique_events"] = weekly_unique_events
    osrc_data["hourly_unique_events"] = hourly_unique_events

    # sort and add latest_repo_contributions
    sorted(latest_repo_contributions, key=operator.itemgetter(0))
    # clone array
    latest_repo_contributions_copy = latest_repo_contributions[:]
    latest_repo_contributions = []
    recorded_repos = []
    for contribution in latest_repo_contributions_copy:
        if not contribution[1] in recorded_repos:
            recorded_repos.append(contribution[1])
            latest_repo_contributions.append(contribution)
    osrc_data["latest_repo_contributions"] = latest_repo_contributions

    osrc_data["rate_limit"] = github.get("rate_limit")
    return osrc_data


def is_logged_in():
    return "access_token" in session


def is_on_appengine():
    return os.getenv('SERVER_SOFTWARE') and os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')
