import datetime
import os
import sqlite3

from os import listdir

import utility
import discord
import requests

import studip_secrets as secrets
from configuration import Configuration
from db_utility import DatabaseConnection
from alias_resolver import AliasResolver
from exceptions import *

CONFIG = Configuration.from_yaml_file('studip_config.yml')
data_directory = CONFIG.get('directory')
db_file = CONFIG.get('db_file')
url = CONFIG.get('url')
alias_resolver = AliasResolver.from_yaml_file('aliases.yml')
db = DatabaseConnection(data_directory, db_file)


def init():
    secrets.init()


def setup_user(user, username, password):
    r = api_request('/user', (username, password))
    if r:
        secrets.input_user(user, username, password)
        input_user(user, r['user_id'])
        input_courses(user)
        return True
    return False


def api_request(path, user_auth):
    try:
        r = requests.get(url + path, auth=user_auth)
        if r.status_code != 200:
            raise APIError
        data = r.json()
        try:
            if data['pagination']:
                if data['pagination']['total'] > data['pagination']['offset'] + 50:
                    return data['collection'] + api_request(path[:-2] + (data['pagination']['offset'] + 50).__str__(),
                                                            user_auth) if 'offset' in path else api_request(
                        path + '?offset=50', user_auth)
                else:
                    return data['collection']
        except KeyError:
            return data
    except requests.exceptions.HTTPError as error:
        print(error)
        return None


def is_in_db(user):
    result = db.db_query('SELECT * FROM users WHERE discord_id = ?', (user,))
    if result:
        return True
    return False


def input_user(user, user_id):
    db.db_query('REPLACE INTO users(discord_id, studip_id) VALUES (?,?)', (user, user_id))


def get_course_name(id):
    result = db.db_query('SELECT title FROM courses WHERE course_id = ?', (id,))
    return result[0]


def input_courses(user):
    data = api_request('user/' + get_studip_id(user) + '/courses?semester=' + get_semester(user),
                       secrets.get_user_login(user))

    if type(data) is dict:
        for key, value in data.items():
            if value['type'] is '1':
                db.db_query('INSERT OR IGNORE INTO courses(course_id,number,title,lecturers) VALUES (?,?,?,?)',
                               (value['course_id'], value['number'], value['title'],
                                next(iter(value['lecturers'].values()))['name']['formatted']))
    if type(data) is list:
        for value in data:
            if value['type'] is '1':
                db.db_query('INSERT OR IGNORE INTO courses(course_id,number,title,lecturers) VALUES (?,?,?,?)',
                                   (value['course_id'], value['number'], value['title'],
                                    next(iter(value['lecturers'].values()))['name']['formatted']))


def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield (key, value)
            yield from recursive_items(value)
        else:
            yield (key, value)


def get_semester(user):
    if CONFIG.get('semester_id'):
        return CONFIG.get('semester_id')
    else:
        r = api_request('semesters', secrets.get_user_login(user))
        for key, value in r.items():
            if value['begin'] <= int(datetime.datetime.utcnow().timestamp()) <= value['end']:
                CONFIG.set('semester_id', value['id'])
                return CONFIG.get('semester_id')


def get_studip_id(user):
    query_result = db.db_query('SELECT studip_id FROM users WHERE discord_id = ?', (user,))
    return query_result[0]


def get_local_folders(course):
    if os.path.exists(data_directory + course):
        return course, listdir(data_directory + course)


def check_new_files(course, user, main_directory=data_directory):
    course_id = course
    if not db.db_query('SELECT * FROM courses WHERE course_id = ?', (course,)):
        course_id = alias_resolver.get(course_id)
    data = api_request('course/' + course_id + '/top_folder', secrets.get_user_login(user))
    if not os.path.exists(main_directory + data['id']):
        os.mkdir(main_directory + data['id'])
    return recursive_folder(data['id'], user, main_directory + data['id'] + '/')


def recursive_folder(folder_id, user, main_directory, new_files=None):
    if new_files is None:
        new_files = []
    data = api_request('folder/' + folder_id + '/subfolders', secrets.get_user_login(user))
    if data:
        if type(data) is dict:
            for key, value in data.items():
                if not value['is_readable']:
                    continue
                if value['folder_type'] == 'CourseGroupFolder':
                    continue
                if '/' in value['name']:
                    continue
                if not os.path.exists(main_directory + value['name']):
                    os.mkdir(main_directory + value['name'])
                recursive_folder(value['id'], user, main_directory + value['name'] + '/', new_files)
        if type(data) is list:
            for value in data:
                if not value['is_readable']:
                    continue
                if value['folder_type'] == 'CourseGroupFolder':
                    continue
                if '/' in value['name']:
                    continue
                if not os.path.exists(main_directory + value['name']):
                    os.mkdir(main_directory + value['name'])
                recursive_folder(value['id'], user, main_directory + value['name'] + '/', new_files)
    files = api_request('folder/' + folder_id + '/files', secrets.get_user_login(user))
    for file in files:
        if not os.path.isfile(main_directory + file['name']) and not os.path.isfile(
                os.path.splitext(main_directory + file['name'])[0] + '.html'):
            if file['size'] < 8000000:
                with open(main_directory + file['name'], mode='wb') as response_file:
                    r = requests.get(url + 'file/' + file['id'] + '/download', auth=secrets.get_user_login(user))
                    response_file.write(r.content)
                print("Download von: " + file['name'])
                new_files.append(discord.File(main_directory + file['name']))
            else:
                with open(os.path.splitext(main_directory + file['name'])[0] + '.html', 'w') as response_file:
                    link = url + 'file/' + file['id'] + '/download'
                    response_file.write(f'''<html>
   <body>
      <script type="text/javascript">
    window.location.href = "{link}";
      </script>
   </body>
</html>''')
                new_files.append(discord.File(main_directory + os.path.splitext(file['name'])[0] + '.html'))

    return new_files


def get_news(user, course=None, page=1):
    if course is None:
        r = api_request('studip/news', secrets.get_user_login(user))
        embed = discord.Embed(title='Globale Ankündigungen')
    else:
        r = api_request(f'course/{alias_resolver.get(course)}/news', secrets.get_user_login(user))
        embed = discord.Embed(title=f'Ankündigungen von {get_course_name(alias_resolver.get(course))[0]}')
    titles = []
    news_id = []
    bodies = []
    if type(r) is list:
        embed.description = 'Diese Veranstaltung hat noch keine Ankündigungen erstellt'
        return embed
    for key, value in r.items():
        titles.append(value['topic'])
        news_id.append(value['news_id'])
        bodies.append(value['body'])
    for i in range(3):
        try:
            if course is None:
                embed.add_field(name=titles[i + (page - 1) * 3],
                                value=utility.remove_html_tags(bodies[i + (page - 1) * 3]) if len(
                                    utility.remove_html_tags(bodies[i + (
                                                page - 1) * 3])) < 1025 else f'[Full News](https://elearning.uni-oldenburg.de/dispatch.php/start?contentbox_type=news&contentbox_open={news_id[i + (page - 1) * 3]}#{news_id[i + (page - 1) * 3]})', inline=False)
            else:
                embed.add_field(name=titles[i + (page - 1) * 3],
                                value=utility.remove_html_tags(bodies[i + (page - 1) * 3]) if len(
                                    utility.remove_html_tags(bodies[i + (page - 1) * 3])) < 1025 else f"News zu lang um dargestellt zu werden, bitte geh zu [Studip](https://elearning.uni-oldenburg.de/dispatch.php/course/overview?cid={course})", inline=False)
        except IndexError:
            break
    if len(embed.fields) is 0:
        embed.description = 'Auf dieser Seite sind keine Ankündigungen mehr.'
    return embed


def add_alias(alias, course):
    query_result = db.db_query('SELECT course_id FROM courses WHERE number = ?', (course,))
    if query_result:
        alias_resolver.set(alias, query_result[0])
    result = db.db_query('SELECT number, title FROM courses WHERE number = ?', (course,))
    alias_resolver.to_yaml_file('aliases.yml')
    return convert_list(result, ' ')


def convert_list(list, seperator):
    s = seperator.join(list)
    return s


def formatted_courses_list():
    result = db.db_query('SELECT number, title FROM courses', fetchall=True)
    course_list = []
    for i in result:
        course_list.append(convert_list(i, ' '))
    formatted_string = convert_list(sorted(course_list), '\n')
    return formatted_string
