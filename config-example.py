# -*- coding: utf-8 -*-
"""A basic config file."""

import os


WTF_CSRF_ENABLED = True
SECRET_KEY = 'hello-github'
# Params
DEFAULT_FILE_STORAGE = 'filesystem'
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/lol'
UPLOADS_FOLDER = os.path.realpath('.') + '/static/photos/'
WEBSITE_URL = 'http://localhost:5000'

DATABASE_PERSONS_FILE = 'data/example-persons.csv'
DATABASE_TEAMS_FILE = 'data/example-teams.csv'
DATABASE_ROOMS_FILE = 'data/example-rooms.csv'

# Admin credentials
ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'pizza'

# Available languages
LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
}

DEBUG = True
