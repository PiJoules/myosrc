# Github Report Card
An attempt to bring back the [previous OSRC](https://github.com/dfm/osrc) since it's currently down. Half of this code is copied from the original, the other half is made up.

## Dependencies
Running this locally depends on a `MongoDB` database and the `Google App Engine SDK` for python.

## Development
1) After cloning this repo, start the mongodb server
```sh
$ sudo mongod
```

2) Start the GAE development server (in the root directory of the repo)
```sh
$ dev_appserver.py .
```