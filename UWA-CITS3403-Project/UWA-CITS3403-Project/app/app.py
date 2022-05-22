import json
import random
import sqlite3 as sql

from flask import Flask, render_template, request

app = Flask(__name__, static_folder='templates/static/')


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/sign_up", methods=['POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = sql.connect("app.db")
        cur = con.cursor()
        cur.execute("insert into user(username,password) values (?,?)", (username, password))
        con.commit()
        cur.execute("select last_insert_rowid()")
        user_id = cur.fetchone()[0]
        data = {'result': True, 'id': user_id, 'username': username}
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response


@app.route("/sign_in", methods=['POST'])
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        con = sql.connect("app.db")
        cur = con.cursor()
        cur.execute("select * from  user where username = ? and password = ?", (username, password))
        row = cur.fetchone()
        if row:
            user_id = row[0]
        else:
            user_id = 0
        data = {'result': True if row else False, 'id': user_id}
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response


@app.route('/next_word', methods=['POST'])
def next_word():
    con = sql.connect("app.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    user_id = random.randint(1, 478)
    cur.execute("select word from words where id = ?", [user_id])
    row = cur.fetchone()
    word = row[0]
    print('next word:', word)
    sorted_word = sorted(word)
    sorted_word = ''.join(sorted_word)
    data = {'word': sorted_word}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/check", methods=['POST'])
def check():
    if request.method == "POST":
        word = request.form['word']
        con = sql.connect("app.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("select count(*) from words where word = ?", [word])
        row = cur.fetchone()
        number = row[0]
        data = {'result': True if number > 0 else False}
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response


@app.route("/save", methods=['POST'])
def save():
    if request.method == 'POST':
        user_id = request.form['id']
        words = request.form['words']
        number = request.form['number']
        con = sql.connect("app.db")
        cur = con.cursor()
        save_sql = '''
        insert into game(user_id, words, number, time) values (?,?, ?, datetime('now'))
        '''
        cur.execute(save_sql, (user_id, words, number))
        con.commit()
        data = {'result': True}
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response


@app.route("/statistics", methods=['POST'])
def statistics():
    if request.method == 'POST':
        user_id = request.form['id']

        # total_played
        sql_1 = '''
        select count(*)
        from game
        where user_id = ?
        '''

        # max_number, max_number_time, average_number
        sql_2 = '''
        select max(number), time, avg(number)
        from game
        where user_id = ?
        '''

        # world_rank
        sql_3 = '''
        select rank
        from (SELECT u.id        AS uid,
                     rank() over (
                         order by MAX(number) desc
                         )       AS rank
              FROM game g
                       join user u
                            on g.user_id = u.id
              GROUP BY u.id)
        where uid = ?
        '''

        # no1_username, no1_max_number
        sql_4 = '''
        select u.username, max(g.number)
        from user u
                 join game g
                      on u.id = g.user_id
        group by u.id
        order by max(g.number) desc
        limit 1;
        '''

        con = sql.connect("app.db")
        cur = con.cursor()

        cur.execute(sql_1, [user_id])
        row = cur.fetchone()
        total_played = row[0]

        cur.execute(sql_2, [user_id])
        row = cur.fetchone()
        max_number = row[0]
        max_number_time = row[1]
        average_number = int(row[2])

        cur.execute(sql_3, [user_id])
        row = cur.fetchone()
        world_rank = row[0]

        cur.execute(sql_4)
        row = cur.fetchone()
        no1_username = row[0]
        no1_max_number = row[1]

        data = {
            'total_played': total_played,
            'max_number': max_number,
            'max_number_time': max_number_time,
            'average_number': average_number,
            'world_rank': world_rank,
            'no1_username': no1_username,
            'no1_max_number': no1_max_number
        }

        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
        return response


if __name__ == '__main__':
    app.secret_key = 'PUZZlE'
    app.run(debug=True)
