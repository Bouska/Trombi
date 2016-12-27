#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hello world test.

Should write something nice here.
"""

import time
import datetime
from flask import render_template, request, url_for
from sqlalchemy import or_
from flask.ext.babel import gettext

from config import LANGUAGES
from app import db, app, babel
from models import Person, Team, Trivia


@babel.localeselector
def get_locale():
    """Get the locale to use for lang."""
    locale = request.accept_languages.best_match(LANGUAGES.keys())
    print('Chosen locale : ' + locale)
    return locale


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template('404.j2')


def get_list_mode(request):
    """Get the current display mode for the dashboard."""
    list_mode = request.args.get('list')
    if (list_mode != 'true'):
        list_mode = None
    return list_mode


@app.route("/")
def main():
    """Root view."""
    return show_all()


@app.route("/all")
def show_all():
    """Show a list of all persons in the trombi."""
    person_filter = request.args.get('filter')
    title = gettext(u'Trombi')

    if (person_filter is not None):
        last_month_timestamp = time.time() - 2592000
        last_month_date = datetime.datetime.fromtimestamp(last_month_timestamp)
        print(last_month_date)
        persons = Person.query.filter(
                Person.arrival > last_month_date
            ).order_by(
                Person.surname
            ).all()
        message = gettext(u'%(number)s newbies', number=len(persons))
    else:
        persons = Person.query.order_by(Person.surname).all()
        message = gettext(u'%(number)s people', number=len(persons))
    return render_template(
        'all.j2',
        persons=persons,
        title=title,
        list_mode=get_list_mode(request),
        person_filter=person_filter,
        list_url='',
        message=message
        )


@app.route("/person/<login>")
def show_person(login=None):
    """Display information about a specific person."""
    person = Person.query.filter_by(login=login).first()
    if (person is None):
        title = gettext(u'%(login)s doesn\'t exists.', login=login)
        return render_template('person_error.j2', person=person, title=title)
    else:
        title = person.name + ' ' + person.surname
        return render_template('person.j2', person=person, title=title)


@app.route("/trivia")
def show_trivia():
    """Display various information stored in the database."""
    trivia = db.session.query(Trivia).first()
    if (trivia is None):
        text = gettext(u'Nothing here yet.')
    else:
        text = trivia.text
    return render_template('trivia.j2', text=text)


@app.route("/person/vcard/vcard-<login>.vcf")
def show_person_vcard(login=None):
    """Show a Person's VCard."""
    person = Person.query.filter_by(login=login).first()
    return person.create_vcard()


@app.route("/search/<query>")
def show_search(query=None):
    """The search screen."""
    title = gettext(u'Search')
    message = gettext(
        u'%(number)s result(s) for \"%(query)s\" :', number='{}',
        query=query
    )

    # Maybe re-do this part of the code in a more pytonic way
    hash_persons = {}
    for token in query.split(' '):
        persons = Person.query.filter(or_(
            Person.login.like('%' + token + '%'),
            Person.name.like('%' + token + '%'),
            Person.job.like('%' + token + '%'),
            Person.surname.like('%' + token + '%')))

        for person in persons.all():
            hash_persons[person.login] = person

    persons = []
    for person_key in hash_persons.keys():
        persons.append(hash_persons[person_key])

    if (len(persons) == 1):
        return show_person(persons[0].login)
    return render_template(
        'all.j2',
        persons=persons,
        message=message.format(len(persons)),
        title=title,
        list_mode=get_list_mode(request),
        list_url=url_for('show_search', query=query)
        )


@app.route('/search/', methods=['POST'])
def search():
    """Handle the search results."""
    query = request.form['search']
    return show_search(query)


@app.route("/calendar")
def show_calendar():
    """The calendar screen."""
    title = gettext(u'Calendar')
    persons = Person.query.all()

    events_list = []

    # Persons events
    birthday_events = '['
    arrival_events = '['
    for year in [2016, 2017]:
        for person in persons:
            if (person.birthday != ''):
                birth_date = person.birthday
                birthday_events += u'{{title: "{} {}", start: "{}", url: "/person/{}"}},'.format(person.name, person.surname, u'{}-{}-{}'.format(year, str(birth_date.month).zfill(2), str(birth_date.day).zfill(2)), person.login)
            if (person.arrival != ''):
                arr_date = person.arrival
                # TODO : don't harcode the current year
                if (year - arr_date.year <= 0):
                    arrival_text = gettext(u'arrival')
                else:
                    format_date = year - arr_date.year
                    arrival_text = gettext(u'%(number)s years', number=format_date)

                arrival_events += u'{{title: "{}", start: "{}", url: "/person/{}"}},'.format(
                        u'{} {} ({})'.format(
                            person.name,
                            person.surname,
                            arrival_text
                        ),
                        u'{}-{}-{}'.format(
                            year,
                            str(arr_date.month).zfill(2),
                            str(arr_date.day).zfill(2)
                        ),
                        person.login
                    )
    birthday_events += '], color: "#a9d03f", textColor: "#ffffff"'
    arrival_events += '], color: "#368cbf", textColor: "#ffffff"'

    events_list.append(birthday_events)
    events_list.append(arrival_events)

    # events = '[{title: "Pizza", start: "2016-05-06"}]'

    return render_template(
        'calendar.j2',
        title=title,
        events_list=events_list)


@app.route("/team")
def show_all_teams():
    """Show a graph with all teams."""
    head_team = Team.query.filter_by(high_team=None).first()
    return show_team(head_team.name)


@app.route("/team/<team>")
def show_team(team=None):
    """Show a graph for a specific team."""
    team = Team.query.filter_by(name=team).first()
    title = gettext(u'Team %(team_name)s', team_name=team.name)

    # If the team has sub-teams, we display them.
    # Otherwise we list the persons inside
    if (team.sub_teams is None or team.sub_teams == []):
        # We show the persons
        team_root_persons = team.get_root_persons()
        tree = build_tree_persons(team_root_persons, True)
    else:
        # We show the teams inside
        tree = build_tree_teams(team)

    return render_template(
        'team.j2',
        team=team,
        tree=tree,
        title=title,
        list_mode=get_list_mode(request),
        list_url=''
        )


def build_tree_teams(team):
    """Default method to build a tree for a given team."""
    result = get_node_team(team, '')

    for subteam in team.sub_teams:
        result += get_node_team(subteam, team.name)
        for subsubteam in subteam.sub_teams:
            result += get_node_team(subsubteam, subteam.name)

    return result


def get_node_team(team, parent):
    """Default method to build a node for a given team."""
    # TODO : make render_template
    # TODO : add a better way to handle invisible blocks
    if (team.name == '1'):
        # We display only a vertical bar
        return "[{v:'" + team.name + "', f:'<div class=\"rootTreeNodeElement\" >\
                    <div class=\"verticalLine\"></div>\
                    </div>'}, '" + parent + "', '" + team.name + "'],\n"
    else:
        return "[{v:'" + team.name + "', f:'<div class=\"rootTreeNodeElement\" >\
                    <a href=\"/team/" + team.name + "\"><div class=\"rootTreeNodeElementFiller\" >\
                    <div class=\"rootTreeNodeLinkCenter\"><div class=\"rootTreeNodeLinkCenterChild\">" + team.name + "</div></div></div></a>\
                    </div>'}, '" + parent + "', '" + team.name + "'],\n"


def build_tree_persons(team_root_persons, is_root):
    """Default method to build a tree for a given person."""
    result = ''
    parent = ''

    if (is_root):
        parent_team_manager = team_root_persons[0].manager
        result += get_node_person(parent_team_manager, '')
        parent = parent_team_manager.login
    else:
        parent = team_root_persons[0].manager.login

    for root_person in team_root_persons:
        result += get_node_person(root_person, parent)
        for subordinate in root_person.subordinates:
            result += build_tree_persons([subordinate], False)

    return result


def get_node_person(person, parent):
    """Default method to build a node for a given person."""
    # TODO : make render_template
    return "[{v:'" + person.login + "', f:'<div class=\"rootTreeNodeElement\"><a href=\"/person/" + person.login + "\">\
        <div class=\"rootTreeNodeElementFiller\" style=\"background: url(/static/images/photos/" + person.login + ".jpg) center / cover;\" >\
            <div class=\"treeNodeTextContainer\"><div class=\"treeNodeText\">" + person.name + " <br /> " + person.surname.upper() + "</div></div>\
        </div>\
    </a></div>'}, '" + parent + "', '" + person.name + " " + \
        person.surname + "'],"
