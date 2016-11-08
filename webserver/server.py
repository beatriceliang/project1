#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
img = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
app = Flask(__name__, static_folder = img, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)



#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
DATABASEURI = "postgresql://bsl2127:28fah@104.196.175.120/postgres"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)



#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
#
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
#
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
#
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
# engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
# #
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None



def is_foodie(uname):
  queryStr = 'SELECT is_foodie FROM users WHERE uid=:u'
  cursor = g.conn.execute(text(queryStr),u = uname)
  for r in cursor:
      identity = r[0]
      break
  return identity


@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
  if 'username' in session:
    context = dict(is_foodie = is_foodie(session.get('username')))
    return render_template("landing.html",**context)
    # if is_foodie(session.get('username')):
    #   return redirect(url_for('foodie'))
    # elif is_foodie(session.get('username')):
    #   return redirect(url_for('foodCritic'))
  else:
    return redirect('login')


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/register')
def register():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  #cursor = g.conn.execute("SELECT name FROM test")
  #names = []
  #for result in cursor:
    #names.append(result['name'])  # can also be accessed using result[0]
  #cursor.close()


  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  #context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  #return render_template("index.html", **context)
  return render_template("register.html")


@app.route('/foodie')
def foodie():
  if 'username' in session:
    return render_template("foodie.html")
  else:
    return redirect(url_for('login'))

@app.route('/foodCritic')
def foodCritic():
  if 'username' in session:
    return render_template("foodCritic.html")
  else:
    return redirect(url_for('login'))


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')



@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == "POST":
    uname = request.form['username']
    print(uname)
    queryStr = 'SELECT EXISTS (SELECT uid FROM users WHERE uid=:u)'
    cursor = g.conn.execute(text(queryStr),u = uname)
    for r in cursor:
      existing_user = r[0]
      break
    if existing_user:
      session['username'] = request.form['username']
      print("redirect")
      return redirect('/')
  return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('username', None)
    return index()



################### MY FUNCTIONS ########################
@app.route('/categories')
def categories():
    cursor = g.conn.execute("SELECT DISTINCT neighborhood FROM restaurant_is_at")

    neighborhoods = []
    for result in cursor:
        neighborhoods.append(result['neighborhood'])  # can also be accessed using result[0]
    cursor.close()

    cursor = g.conn.execute("SELECT DISTINCT cuisine FROM restaurant_description")
    cuisines = []
    for result in cursor:
        cuisines.append(result['cuisine'])
    cursor.close()
    context = dict(neighborhoods = neighborhoods, cuisines = cuisines)

    return render_template("categories.html",**context)

@app.route('/nearby', methods=['POST'])
def nearby():
    neighborhood = request.form["neighbor"]
    cmd = 'SELECT name, restaurant.rid AS rid\
            FROM restaurant, restaurant_is_at\
            WHERE restaurant_is_at.rid = restaurant.rid\
            AND neighborhood = (:x)'
    cursor = g.conn.execute(text(cmd), x = neighborhood)
    restaurants = []
    rid = []
    for result in cursor:
        restaurants.append(result['name'])
        rid.append(result['rid'])
    context  = dict(type = neighborhood, restaurants = zip(restaurants, rid));
    return render_template("restaurants.html", **context)

@app.route('/pricerange', methods=['POST'])
def pricerange():
    price = request.form["price"]
    cmd = 'SELECT name, restaurant.rid AS rid\
            FROM restaurant, restaurant_description\
            WHERE restaurant_description.rid = restaurant.rid\
            AND price = (:p)'
    cursor = g.conn.execute(text(cmd), p = price)

    restaurants = []
    rid = []
    for result in cursor:
        restaurants.append(result['name'])
        rid.append(result['rid'])

    pricerange = ""
    for i in range(int(price)):
        pricerange+="$"

    context  = dict(type = pricerange, restaurants = zip(restaurants, rid));

    return render_template("restaurants.html", **context)

@app.route('/cuisines', methods=['POST'])
def cuisines():
    cuisine = request.form["cuisine"]
    cmd = 'SELECT name, restaurant.rid AS rid\
            FROM restaurant, restaurant_description\
            WHERE restaurant_description.rid = restaurant.rid\
            AND cuisine = (:c)'
    cursor = g.conn.execute(text(cmd), c = cuisine)
    restaurants = []
    rid = []
    for result in cursor:
        restaurants.append(result['name'])
        rid.append(result['rid'])

    context  = dict(type = cuisine, restaurants = zip(restaurants, rid));
    return render_template("restaurants.html", **context)

@app.route('/restaurant', methods=['POST'])
def restaurant(rid = None):
    if rid is None:
        rid = request.form["rid"]

    isFoodie = None
    uid = None
    content = None
    # get review for restaurant if user has reviewed the restaurant
    if 'username' in session:
        uid = session.get('username')
        isFoodie = is_foodie(uid)
        if isFoodie:
            cmd = 'SELECT content \
                    FROM reviews, rates\
                    WHERE rid = :r AND foodie_id = :f AND reviews.review_id = rates.review_id'
            cursor = g.conn.execute(text(cmd), r = rid, f = uid)
            for result in cursor:
                content = result["content"]
        else:
            cmd = 'SELECT content \
                    FROM write_about, reports\
                    WHERE rid = :r AND uid = :u AND reports.report_id = write_about.report_id'
            cursor = g.conn.execute(text(cmd), r = rid, u = uid)
            for result in cursor:
                content = result["content"]
    print content
    # get percent of foodies who liked this restaurant
    cmd = 'SELECT\
            CAST(SUM(CASE WHEN like_dislike THEN 1 ELSE 0 END) AS FLOAT)/COUNT(like_dislike) \
            AS liked\
        FROM rates, reviews\
        WHERE rates.rid = (:r)\
        AND rates.review_id = reviews.review_id'
    cursor = g.conn.execute(text(cmd), r = rid)
    for result in cursor:
        liked = result['liked']
        if liked is not None:
            liked*=100

    cmd = 'SELECT\
            CAST(SUM(rating) AS FLOAT)/COUNT(rating) \
            AS rate\
        FROM reports, write_about\
        WHERE write_about.rid = (:r)\
        AND reports.report_id = write_about.report_id'
    cursor = g.conn.execute(text(cmd), r = rid)
    for result in cursor:
        rate = result['rate']

    cmd = 'SELECT name, contact, cuisine, price, neighborhood, zipcode\
            FROM restaurant, restaurant_description, restaurant_is_at\
            WHERE restaurant.rid =(:r)\
            AND restaurant_description.rid = restaurant.rid\
            AND restaurant_is_at.rid = restaurant.rid'

    cursor = g.conn.execute(text(cmd), r = rid)
    for result in cursor:
        name = result['name']
        contact = result['contact']
        cuisine = result['cuisine']
        price = int(result['price'])
        neighborhood = result['neighborhood']
        zipcode = result['zipcode']

    pricerange = ""
    for i in range(price):
        pricerange+="$"


    cmd = 'SELECT foodie_id, review_id\
            FROM rates\
            WHERE rid = (:r)'
    cursor = g.conn.execute(text(cmd), r = rid)

    foodies =[]
    review = []
    for result in cursor:
        foodies.append(result['foodie_id'])
        review.append(result['review_id'])


    cmd = 'SELECT uid, report_id\
            FROM write_about\
            WHERE rid = (:r)'
    cursor = g.conn.execute(text(cmd), r = rid)

    critic =[]
    report = []
    for result in cursor:
        critic.append(result['uid'])
        report.append(result['report_id'])

    context = dict(liked = liked, rate = rate, name = name, contact = contact,
                cuisine = cuisine, price = pricerange, neighborhood = neighborhood,
                zipcode = zipcode,
                foodies = zip(foodies, review),
                critic = zip(critic, report),
                review = review,
                isFoodie = isFoodie, rid = rid,
                content = content
                )
    return render_template("restaurant.html", **context)

@app.route('/foodie_review', methods=['POST'])
def foodie_review():
    review_id = request.form["review"]
    cmd = 'SELECT like_dislike, content FROM reviews WHERE review_id = (:r)'
    cursor = g.conn.execute(text(cmd), r = review_id)
    for result in cursor:
        like_dislike = result['like_dislike']
        content = result['content']

    like = u'\U00002639'
    if like_dislike:
        like = u'\U0001f604'
    context = dict(like = like, content = content)
    return render_template("foodie_review.html",**context)

@app.route('/critic_report', methods=['POST'])
def critic_report():
    report_id = request.form["report"]
    cmd = 'SELECT rating, content FROM reports WHERE report_id = (:r)'
    cursor = g.conn.execute(text(cmd), r = report_id)

    for result in cursor:
        rating = result['rating']
        content = result['content']

    cmd = 'SELECT name, uid, restaurant.rid AS rid\
            FROM write_about, restaurant\
            WHERE write_about.report_id = (:r) \
            AND restaurant.rid = write_about.rid'
    cursor = g.conn.execute(text(cmd), r = report_id)
    for result in cursor:
        name = result['name']
        uid = result['uid']
        rid = result['rid']

    context = dict(rating = rating, content = content, name = name, uid= uid, rid = rid)
    return render_template("critic_report.html",**context)

@app.route('/critic_profile', methods=['POST'])
def critic_profile():
    uid = request.form["uid"]
    cmd = 'SELECT CAST(SUM(CASE WHEN like_dislike THEN 1 ELSE 0 END) AS FLOAT)/COUNT(like_dislike)\
            AS percent\
            FROM foodies_assess_critic\
            WHERE critic_id = (:u)'
    cursor = g.conn.execute(text(cmd), u = uid)
    for result in cursor:
        liked = result['percent']
        if liked is not None:
            liked *=100
    cmd = 'SELECT foodie_id\
            FROM foodies_assess_critic\
            WHERE critic_id = (:u)'
    cursor = g.conn.execute(text(cmd), u = uid)
    foodie_id = []
    for result in cursor:
        foodie_id.append(result['foodie_id'])

    cmd = 'SELECT report_id, name\
            FROM write_about, restaurant\
            WHERE write_about.rid = restaurant.rid\
            AND uid =(:u)'
    cursor = g.conn.execute(text(cmd), u = uid)
    restaurant = []
    report_id = []
    for result in cursor:
        restaurant.append(result['name'])
        report_id.append(result['report_id'])

    context = dict(critic_id = uid, foodie_id = foodie_id, restaurant = zip(restaurant,report_id), liked = liked)
    return render_template("critic_profile.html",**context)

@app.route('/foodie_review_critic', methods=['POST'])
def foodie_review_critic():
    ids = request.form["review"]
    ids = ids.split(",")
    critic_id = ids[0]
    foodie_id = ids[1]
    cmd = 'SELECT like_dislike, content\
            FROM foodies_assess_critic \
            WHERE foodie_id = (:f) AND critic_id = (:c)'

    cursor = g.conn.execute(text(cmd), f = foodie_id, c = critic_id)
    for result in cursor:
        like_dislike = result['like_dislike']
        content = result['content']

    like = u'\U00002639'
    if like_dislike:
        like = u'\U0001f604'
    context = dict(like = like, content = content)
    return render_template("foodie_review.html",**context)

@app.route('/landing', methods=['POST'])
def landing():
    uid = request.form["uid"]
    cmd = 'SELECT is_foodie FROM users WHERE uid = (:u)'
    cursor = g.conn.execute(text(cmd), u = uid)
    for result in cursor:
        is_foodie = result["is_foodie"]
    context = dict(is_foodie = is_foodie)
    return render_template("landing.html", **context)

@app.route('/make_review/<rid>', methods = ['POST'])
def make_review(rid):
    foodie_id = session.get('username')
    like_dislike = request.form["like_dislike"]
    like = like_dislike == 'like'
    content = request.form["content"]
    cmd = "SELECT review_id FROM rates WHERE rid = :r AND foodie_id = :f"
    cursor = g.conn.execute(text(cmd),r = rid, f = foodie_id)
    review_id = None
    for result in cursor:
        review_id = result['review_id']
    if review_id is None:
        review_id = hash(foodie_id+rid)
        cmd = "INSERT INTO reviews VALUES(:i, :c,:l)"
        cursor = g.conn.execute(text(cmd),  i = review_id, c = content, l = like )
        cmd = "INSERT INTO rates VALUES(:i,:r, :f)"
        cursor = g.conn.execute(text(cmd), i = review_id, r = rid, f = foodie_id)
    else:
        cmd = "UPDATE reviews SET content = :c, like_dislike = :l WHERE review_id = :i"
        cursor = g.conn.execute(text(cmd), c = content, l = like, i = review_id)
    return restaurant(rid)

@app.route('/make_report/<rid>', methods = ['POST'])
def make_report(rid):
    uid = session.get('username')
    rating = request.form["rating"]
    content = request.form["content"]
    cmd = "SELECT report_id FROM write_about WHERE rid = :r AND uid = :u"
    cursor = g.conn.execute(text(cmd),r = rid, u = uid)
    report_id = None
    for result in cursor:
        report_id = result['report_id']
    if report_id is None:
        report_id = hash(uid+rid)
        cmd = "INSERT INTO reports VALUES(:i, :c,:r)"
        cursor = g.conn.execute(text(cmd),  i = report_id, c = content, r = rating )
        cmd = "INSERT INTO write_about VALUES(:i, :u,:r)"
        cursor = g.conn.execute(text(cmd), i = report_id, r = rid, u = uid)
    else:
        cmd = "UPDATE reports SET content = :c, rating = :r WHERE report_id = :i"
        cursor = g.conn.execute(text(cmd), c = content, r = rating, i = report_id)
    return restaurant(rid)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8112, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
