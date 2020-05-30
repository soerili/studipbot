import json
import requests
from requests.auth import HTTPBasicAuth
import os
import datetime
import sqlite3
import studip_secrets as secrets
from configuration import Configuration
import discord

CONFIG = Configuration.from_yaml_file('studip_config.yml')
data_directory = CONFIG.get('directory')
db_file = CONFIG.get('db_file')
url = CONFIG.get('url')


def init():
    os.makedirs(data_directory, exist_ok=True)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS courses (course_id text, number text, title text, lecturers text, UNIQUE(course_id))')
        conn.commit()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS users (discord_id text, studip_id text, UNIQUE(discord_id))')
        conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        if conn:
            conn.close()
    secrets.init()


def setup_user(user, username, password):
    if is_in_db(user):
        input_courses(user)
        return False
    r = api_request('/user', (username, password))
    if r:
        secrets.input_user(user, username, password)
        input_user(user, r['user_id'])
        input_courses(user)
        return True
    return False


def get_db_connection():
    return sqlite3.connect(data_directory + db_file)


def api_request(path, user_auth):
    try:
        print(url + path, user_auth)
        r = requests.get(url + path, auth=user_auth)
        if r.status_code != 200:
            return None
        data = r.json()
        print(data)
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE discord_id = ?', (user,))
        userdata = cursor.fetchone()
        return True if userdata else False
    except sqlite3.Error as error:
        print(error)
        return False
    finally:
        if conn:
            conn.close()


def input_user(user, user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users(discord_id, studip_id) VALUES (?,?)',
                       (user, user_id))
        conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        if conn:
            conn.close()


def input_courses(user):
    data = api_request('user/' + get_studip_id(user) + '/courses?semester=' + get_semester(user),
                       secrets.get_user_login(user))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print(data)
        print(type(data))
        if type(data) is dict:
            for key, value in data.items():
                if value['type'] is '1':
                    cursor.execute('INSERT INTO courses(course_id,number,title,lecturers) VALUES (?,?,?,?)',
                                   (value['course_id'], value['number'], value['title'], next(iter(value['lecturers'].values()))['name']['formatted']))
                    conn.commit()
        if type(data) is list:
            for value in data:
                if value['type'] is '1':
                    cursor.execute('INSERT INTO courses(course_id,number,title,lecturers) VALUES (?,?,?,?)',
                                   (value['course_id'], value['number'], value['title'], next(iter(value['lecturers'].values()))['name']['formatted']))
                    conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        if conn:
            conn.close()


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
            print(value['begin'])
            print(int(datetime.datetime.utcnow().timestamp()))
            if value['begin'] <= int(datetime.datetime.utcnow().timestamp()) <= value['end']:
                CONFIG.set('semester_id', value['id'])
                return CONFIG.get('semester_id')


def get_studip_id(user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT studip_id FROM users WHERE discord_id = ?', (user,))
        userdata = cursor.fetchone()
        return userdata[0]
    except sqlite3.Error as error:
        print(error)
        return None
    finally:
        if conn:
            conn.close()


def check_new_files(course, user, main_directory=data_directory):
    data = api_request('course/' + course + '/top_folder', secrets.get_user_login(user))
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
                if not os.path.exists(main_directory + value['name']):
                    os.mkdir(main_directory + value['name'])
                recursive_folder(value['id'], user, main_directory + value['name'] + '/', new_files)
        if type(data) is list:
            for value in data:
                if not os.path.exists(main_directory + value['name']):
                    os.mkdir(main_directory + value['name'])
                recursive_folder(value['id'], user, main_directory + value['name'] + '/', new_files)
    files = api_request('folder/' + folder_id + '/files', secrets.get_user_login(user))
    for file in files:
        if not os.path.isfile(main_directory + file['name']) and not os.path.isfile(
                os.path.splitext(main_directory + file['name'])[0] + '.html'):
            new_files.append(file['name'])
            print(new_files)
            if file['size'] < 8000000:
                with open(main_directory + file['name'], mode='wb') as response_file:
                    r = requests.get(url + 'file/' + file['id'] + '/download', auth=secrets.get_user_login(user))
                    response_file.write(r.content)
                    print("Download von: " + file['name'])
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

    return new_files


def get_news(user, course=None):
    if course is None:
        r = api_request('studip/news', secrets.get_user_login(user))
        embed = discord.Embed(title='Global News')
        titles = []
        news_id = []
        for key, value in r.items():
            titles.append(value['topic'])
            news_id.append(value['news_id'])
        embed.add_field(name=titles[1], value=f'[Full News](https://elearning.uni-oldenburg.de/dispatch.php/start?contentbox_type=news&contentbox_open={news_id[1]}#{news_id[1]})', inline=False)
        embed.add_field(name=titles[2], value=f'[Full News](https://elearning.uni-oldenburg.de/dispatch.php/start?contentbox_type=news&contentbox_open={news_id[2]}#{news_id[2]})', inline=False)
        embed.add_field(name=titles[3], value=f'[Full News](https://elearning.uni-oldenburg.de/dispatch.php/start?contentbox_type=news&contentbox_open={news_id[3]}#{news_id[3]})', inline=False)
        return embed


# json_data = api_request('user/73d56ceb7dd2ed7d621efe9bed6232a6/courses', ('afji2257', 'werder12'))
# json_data = api_request('folder/c744f8d61a28cd77b1b8abf78a4b09b3/subfolders', ('afji2257','werder12'))
# json_data = api_request('folder/42671366629332aaba3a58f9938b6085/files',('afji2257','werder12'))
# for key, value in recursive_items(json_data):
#    print(key, value)
# print(json_data[0])
# if json_data:
#    for x in json_data:
#        print(x['name'])
#    print(key, value)
#    print(value['type'])
#    if value['type'] is '1':
#        print(value)
# if value['type'] is '1' and 'a2eae20475c9dc0f5a0bc24778e4d6a9' in value['start_semester']:
#    print(value)
#    print(type(key))

#CONFIG.get(None)
#test = check_new_files("546e25ec8421471f23f7067ebcc8e8ed", "Test2", data_directory)
#print(test)
