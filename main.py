import flask
import flask.ext.sqlalchemy
from flask import render_template, redirect, request
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Column, Integer, ForeignKey, or_
from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired

from app import db, app
from models import Person, Team

@app.route("/")
def main():
    return show_all()

@app.route("/all")
def show_all():
    title = "Trombi"
    persons = Person.query.order_by(Person.surname).all()
    return render_template('all.html', persons=persons, title=title)

@app.route("/person/<login>")
def show_person(login=None):
    person = Person.query.filter_by(login=login).first()
    title = person.name + " " + person.surname

    print('Name : ' + person.name)
    print('Manager : ' + str(person.manager))
    print('Subordinates : ' + str(person.subordinates))

    return render_template('person.html', person=person, title=title)

@app.route("/person/vcard/vcard-<login>.vcf")
def show_person_vcard(login=None):
    person = Person.query.filter_by(login=login).first()
    return create_vcard(person)

def create_vcard(person):
    vcard = 'BEGIN:VCARD\n'
    vcard += 'VERSION:3.0\n'
    vcard += 'N:' + person.surname + ';' + person.name + '\n'
    vcard += 'FN:' + person.name + ' ' + person.surname + '\n'
    vcard += 'TITLE:' + person.job + '\n'
    vcard += 'EMAIL;TYPE=PREF,INTERNET:' + person.email + '\n'
    vcard += 'END:VCARD'
    return vcard

@app.route("/search/<query>")
def show_search(query=None):
    title = "Search"
    message = "Results for \"" + query + "\" :"
    query = '%' + query + '%'
    persons = Person.query.filter(or_(\
            Person.login.like(query),\
            Person.name.like(query),\
            Person.job.like(query),\
            Person.surname.like(query)))

    if (len(persons.all()) == 1):
        return show_person(persons.first().login)
    return render_template('all.html', persons=persons, message=message, title=title)

@app.route('/search/', methods=['POST'])
def search():
    query = request.form['search']
    return show_search(query)

@app.route("/calendar")
def show_calendar():
    title = "Calendar"

    persons = Person.query.all()

    events_list = []

    # Birthday events
    birthday_events = '['
    for person in persons:
        if (person.birthday != ''):
            birthday_events += '{title: "' + person.name + ' ' + person.surname + '", start: "' + person.birthday + '", url: "/person/' + person.login + '"},'
    birthday_events += '], color: "#e74c3c", textColor: "#ffffff"'

    events_list.append(birthday_events)

    # events = '[{title: "Pizza", start: "2016-05-06"}]'

    return render_template('calendar.html', title=title, events_list=events_list)

@app.route("/team")
def show_all_teams():
    title = "Teams"
    head_team = Team.query.filter_by(high_team=None).first()
    return show_team(head_team.name)

@app.route("/team/<team>")
def show_team(team=None):
    team = Team.query.filter_by(name=team).first()
    title = "Team " + team.name

    print("subteam : " + str(team.sub_teams))

    # If the team has sub-teams, we display them. Otherwise we list the persons inside
    if (team.sub_teams is None or team.sub_teams == []):
        # We show the persons
        root_manager = team.get_manager()
        print(root_manager)
        tree = build_tree_persons(root_manager, True)
    else:
        # We show the teams inside
        tree = build_tree_teams(team)

    print(team.persons)

    return render_template('team.html', team=team, tree=tree, title=title)

def build_tree_teams(team):
    print(team)
    result = ''

    # The first item is the manager of all other teams
    team_manager = team.get_manager()
    result += get_node_person(team_manager, '')

    for subteam in team.sub_teams:
         result += get_node_team(subteam, team_manager.login)
         for subsubteam in subteam.sub_teams:
              result += get_node_team(subsubteam, subteam.name)

    return result

def get_node_team(team, parent):
    # TODO : make render_template
    return "[{v:'" + team.name + "', f:'<a href=\"/team/"+ team.name +"\"><div class=\"rootTreeNodeElementTeam\">\
        <div class=\"treeNodeTeam\">\
            <div class=\"treeNodeTextTeam\">"+ team.name +"</div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + team.name + "'],\n"

def build_tree_persons(root_person, is_root):
    print(root_person)
    result = ''

    parent = ''
    if (not is_root):
        parent = root_person.manager.login

    result +=get_node_person(root_person, parent)
    for subordinate in root_person.subordinates:
        result += build_tree_persons(subordinate, False)

    return result

def get_node_person(person, parent):
    # TODO : make render_template
    return "[{v:'" + person.login + "', f:'<a href=\"/person/"+ person.login +"\"><div class=\"rootTreeNodeElement\">\
        <div class=\"treeNode\" style=\"background: url(/static/images/photos/" + person.login + ".jpg) center / cover;\" >\
            <div class=\"treeNodeTextContainer\"><div class=\"treeNodeText\">" + person.name + " <br /> " + person.surname + "</div></div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + person.name + " " + person.surname + "'],"

def load_persons():
    # Init teams

    persons = []
    managers = {}
    teams = []
    teams_order = {}
    existing_teams = {}

    with open('test_teams.csv', 'r') as f:
    #with open('update_teams.csv', 'r') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                split = line[:-1].split(',')
                print(split)
                team = split[0]
                subteam = split[1]

                if (not team in teams):
                    teams.append(team)
                if (not subteam in teams):
                    teams.append(subteam)

                if team in teams_order:
                    teams_order[team].append(subteam)
                else:
                    teams_order[team] = [subteam]

    print(teams)
    print(teams_order)

    for team_name in teams:
        print(team_name)
        neo_team = Team(team_name)
        existing_teams[team_name] = neo_team
        db.session.add(neo_team)

    for team_name in teams_order:
        current_team = existing_teams[team_name]
        for subteam in teams_order[team_name]:
            existing_teams[subteam].high_team = current_team



    # DEPT,SERVICE,LOGIN,NOM,PRENOM,NAISSANCE,FONCTION,MAIL,SKYPE,FIXE,PORTABLE,MANAGER
    with open('update_persons.csv', 'r') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                # print(line)
                neo = Person()

                #print('LEUL : ' + str(type(unicode(line))))
                split = line[:-1].split(';')
                neo.login = split[2].strip().lower().decode('utf-8')
                neo.surname = split[3].decode('utf-8')
                neo.name = split[4].decode('utf-8')
                neo.birthday = format_birth_date(split[5]).decode('utf-8')
                neo.job = split[6].decode('utf-8')
                neo.email = split[7].decode('utf-8')
                neo.skype = split[8].decode('utf-8')
                neo.fixe = split[9].decode('utf-8')
                neo.mobile = split[10].decode('utf-8')


                team = split[1]
                manager = split[11]

                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                if (team in existing_teams):
                    neo.team = existing_teams[team]
                else:
                    print('Error: Missing team ' + team)

                persons.append(neo)


    for person in persons:
        # We link the managers
        if person.login in managers:
            print('Manager : ' + person.login)
            person.subordinates = managers[person.login]
            # for lol in person.subordinates:
            #     print('     -> ' + lol.login)
        db.session.add(person)

    # print('PERSONS : ' + str(persons))
    # print('MANAGERS : ' + str(managers))
    # print('TEAMS : ' + str(existing_teams))

    db.session.commit()

def format_birth_date(date):
    if (date is None or date == ''):
        return ''

    result = '2016-'
    split = None
    if (' ' in date):
        split = date.split(' ')
    elif ('-' in date):
        split = date.split('-')

    # TODO : remove this, the date should be correct in the csv
    date_dict = {'jan': '01', 'fev' : '02', 'mar' : '03', 'apr' : '04', 'may': '05', 'jun' : '06', 'jul' : '07', 'aout' : '08', 'sep' : '09', 'oct' : '10', 'nov' : '11', 'dec' : '12'}

    try:
        day = split[0]
        if (len(split[0]) == 1):
            day = '0' + day
        result += date_dict[split[1].lower()] + '-' + day
    except:
        print('Cannot convert : ' + date)
        return ''

    # print("new date : " + result)

    return result

if __name__ == "__main__":
    db.create_all()

    persons = Person.query.all()
    if (len(persons) == 0):
        load_persons()

    app.run()
