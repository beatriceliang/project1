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
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash

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
    return landing()
  else:
    return redirect('login')

@app.route('/register')
def register():
  if 'username' in session:
    return redirect('/')
  return render_template("register.html")



@app.route('/foodieRegister', methods=['POST','GET'])
def foodieRegister():
    queryStr = 'SELECT cuisine FROM categories'
    cursor = g.conn.execute(text(queryStr))
    cat = []
    for r in cursor:
        cat.append(r[0])
    context = dict(data = cat)
    if request.method == 'GET':
        return render_template("foodieRegister.html",**context)
    if request.method == 'POST':
        uname = request.form['username']
        homeaddr = int(request.form['HomeAddress'])
        workaddr = int(request.form['WorkAddress'])
        category = request.form.get('category')
        price = int(request.form.get('price'))
        print(uname,homeaddr,workaddr,category,price)

        queryStr = 'SELECT EXISTS (SELECT uid FROM users WHERE uid=:u)'
        cursor = g.conn.execute(text(queryStr),u = uname)
        for r in cursor:
            existing_user = r[0]
            print(existing_user)
            break

        if existing_user == True:
            flash("The username already exists...")
            return render_template("foodieRegister.html",**context)

        print("insert")
        insertUsers = "INSERT INTO users VALUES (:u,true)"
        cursor = g.conn.execute(text(insertUsers),u=uname)
        insertFoodies = "INSERT INTO foodies VALUES (:u)"
        cursor = g.conn.execute(text(insertFoodies),u=uname)

        insertLocations = "INSERT INTO locations VALUES (' ',:l)"
        try:
            cursor = g.conn.execute(text(insertLocations),l=homeaddr)
        except exc.IntegrityError:
            pass

        try:
            cursor = g.conn.execute(text(insertLocations),l=workaddr)
        except exc.IntegrityError:
            pass

        # set location

        insertSetLocation = "INSERT INTO foodie_Set_location VALUES(:u,:l1,:l2);"
        try:
            cursor = g.conn.execute(text(insertSetLocation),u=uname,l1=homeaddr,l2=workaddr)
        except exc.IntegrityError:
            pass


        insertCategories = "INSERT INTO categories VALUES (:c,:p);"
        try:
            cursor = g.conn.execute(text(insertCategories),c=category,p=price)
        except exc.IntegrityError:
            pass


        insertFoodiesPrefer = "INSERT INTO foodies_prefer_categories VALUES (:u,:c,:p);"
        try:
            cursor = g.conn.execute(text(insertFoodiesPrefer),u=uname,c=category,p=price)
        except exc.IntegrityError:
            pass

        session['username'] = uname
        return redirect('/')

    return redirect('/')

@app.route('/foodCriticRegister',methods=['POST','GET'])
def foodCriticRegister():
  print("foodCriticRegister function top")
  if request.method == 'GET':
    print('GET REQUEST')
    return render_template("foodCriticRegister.html")
  if request.method == 'POST':
    print("POST request")
    uname = request.form['username']
    print(uname)
    queryStr = 'SELECT EXISTS (SELECT uid FROM users WHERE uid=:u)'
    cursor = g.conn.execute(text(queryStr),u = uname)
    for r in cursor:
      existing_user = r[0]
      print(existing_user)
      break

    if existing_user == True:
      flash("The username already exists...")
      return render_template("foodCriticRegister.html")
    else:
      insertUsers = "INSERT INTO users VALUES (:u,false)"
      cursor = g.conn.execute(text(insertUsers),u=uname)
      insertFoodCritic = "INSERT INTO food_critic VALUES (:u)"
      cursor = g.conn.execute(text(insertFoodCritic),u=uname)
      session['username'] = uname
      return redirect('/')
  return redirect('/')



@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == "POST":
    uname = request.form['username']
    queryStr = 'SELECT EXISTS (SELECT uid FROM users WHERE uid=:u)'
    cursor = g.conn.execute(text(queryStr),u = uname)
    for r in cursor:
      existing_user = r[0]
      break
    if existing_user:
      session['username'] = request.form['username']
      print("redirect")
      return redirect('/')
    flash("No matched username. Please register...")
  return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('username', None)
    return index()


@app.route("/addRestaurant", methods=['GET', 'POST'])
def addRestaurant():
  if 'username' in session:
    if request.method == 'GET':
      context = dict(uname=session.get('username'))
      return render_template("addRestaurant.html",**context)
    if request.method == 'POST':
        restaurantName = request.form['restaurantName']
        cuisineType = request.form['cuisineType']
        price = int(request.form.get('price'))
        neighborhood = request.form['neighborhood']
        if len(neighborhood) == 0:
            neighborhood = None
        zipcode = int(request.form['zipcode'])
        contact = request.form['contact']
        contact = int(''.join(c for c in contact if c.isdigit()))
        rid = int(hash(contact)+hash(restaurantName))
        queryStr = 'SELECT EXISTS (SELECT rid FROM restaurant WHERE rid=:u)'
        cursor = g.conn.execute(text(queryStr),u = str(rid))
        for r in cursor:
            existing = r[0]
            break

        if existing == True:
            flash("The restaurant already exists...")
            context = dict(uname=session.get('username'))
            return render_template("addRestaurant.html",**context)



        insertRestaurant = "INSERT INTO restaurant VALUES (:r,:n,:c)"
        cursor = g.conn.execute(text(insertRestaurant),
                                r=rid,
                                n=restaurantName,
                                c=contact)

        insertCategories = "INSERT INTO categories VALUES (:c,:p)"
        try:
            cursor = g.conn.execute(text(insertCategories),c=cuisineType, p=price)
        except exc.IntegrityError:
            pass

        insertResDesc = "INSERT INTO restaurant_description VALUES (:r,:c,:p)"
        cursor = g.conn.execute(text(insertResDesc),
                                r=rid,
                                c=cuisineType,
                                p=price)


        insertLocations = "INSERT INTO locations VALUES (:n,:z)"
        try:
            cursor = g.conn.execute(text(insertLocations),n=neighborhood, z=zipcode)
        except exc.IntegrityError:
            pass

        insertResAt = "INSERT INTO restaurant_is_at VALUES (:r,:n,:z)"
        cursor = g.conn.execute(text(insertResAt),
                                r=rid,
                                n=neighborhood,
                                z=zipcode)

        return redirect(url_for('categories'))
    return redirect('/')

  else:
    return redirect('login')



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
    context = dict(neighborhoods = neighborhoods, cuisines = cuisines,uname=session.get('username'))

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
    context  = dict(type = neighborhood, restaurants = zip(restaurants, rid),uname=session.get('username'));
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

    context  = dict(type = pricerange, restaurants = zip(restaurants, rid),uname=session.get('username'));

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

    context  = dict(type = cuisine, restaurants = zip(restaurants, rid),uname=session.get('username'));
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
            liked = round(liked,3)

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
                content = content,
                uname=session.get('username')
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
    context = dict(like = like, content = content,uname=session.get('username'))
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

    context = dict(rating = rating, content = content, name = name, uid= uid, rid = rid,uname=session.get('username'))
    return render_template("critic_report.html",**context)

@app.route('/critic_profile', methods=['POST'])
def critic_profile(uid = None):
    if uid is None:
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
            liked = round(liked,3)
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


    isFoodie = None
    foodieId = None
    content = None
    # get review for restaurant if user has reviewed the restaurant
    if 'username' in session:
        userid = session.get('username')
        isFoodie = is_foodie(userid)
        if isFoodie:
            cmd = 'SELECT content \
                    FROM foodies_assess_critic\
                    WHERE critic_id = :c AND foodie_id = :f'
            cursor = g.conn.execute(text(cmd),c = uid, f = userid)
            for result in cursor:
                content = result["content"]

    context = dict(critic_id = uid, foodie_id = foodie_id,
                  restaurant = zip(restaurant,report_id), liked = liked,
                  content = content, isFoodie = isFoodie,
                  uname=session.get('username'))

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
    context = dict(like = like, content = content,uname=session.get('username'))
    return render_template("foodie_review.html",**context)

@app.route('/landing', methods=['POST'])
def landing():
    uid=session.get('username')
    isFoodie = is_foodie(uid)
    cmd = 'SELECT rates.rid,restaurant.name,\
            CAST(SUM(CASE WHEN like_dislike THEN 1 ELSE 0 END) AS FLOAT)/COUNT(like_dislike) \
            AS liked\
        FROM rates, reviews, restaurant\
        WHERE rates.review_id = reviews.review_id AND restaurant.rid = rates.rid\
        GROUP BY rates.rid,restaurant.name\
        ORDER BY liked DESC\
        LIMIT 10\
        '
    cursor = g.conn.execute(text(cmd))

    f_rid = []
    f_name = []
    f_rate = []
    for result in cursor:
        f_rid.append(result['rid'])
        f_name.append(result['name'])
        f_rate.append(str(100*result['liked'])+"%")

    cmd = 'SELECT restaurant.rid, restaurant.name,\
            CAST(SUM(rating) AS FLOAT)/COUNT(rating) \
            AS rate\
        FROM reports, write_about, restaurant\
        WHERE write_about.rid = restaurant.rid\
        AND reports.report_id = write_about.report_id\
        GROUP BY restaurant.rid, restaurant.name\
        ORDER BY rate DESC\
        LIMIT 10'
    cursor = g.conn.execute(text(cmd))
    c_rid = []
    c_name= []
    c_rate = []
    for result in cursor:
        c_rid.append(result['rid'])
        c_name.append(result['name'])
        c_rate.append(str(result['rate'])+"/5.0")

    context = dict(is_foodie = isFoodie,uname=session.get('username'), topFoodie = zip(f_rid,f_name, f_rate), topCritic = zip(c_rid, c_name, c_rate))

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

@app.route('/make_critic_review/<critic_id>', methods = ['POST'])
def make_critic_review(critic_id):
    foodie_id = session.get('username')
    like_dislike = request.form["like_dislike"]
    like = like_dislike == 'like'
    content = request.form["content"]
    cmd = "SELECT foodie_id FROM foodies_assess_critic WHERE foodie_id = :f AND critic_id = :c"
    cursor = g.conn.execute(text(cmd),c = critic_id, f = foodie_id)
    exists = False
    for result in cursor:
        if result['foodie_id'] is not None:
            exists = True
    if not exists:
        review_id = hash(foodie_id+critic_id)
        cmd = "INSERT INTO foodies_assess_critic VALUES(:f, :cr, :c,:l)"
        cursor = g.conn.execute(text(cmd),  f = foodie_id, cr = critic_id, c = content, l = like )
    else:
        cmd = "UPDATE foodies_assess_critic SET content = :c, like_dislike = :l WHERE foodie_id = :f AND critic_id = :cr"
        cursor = g.conn.execute(text(cmd), c = content, l = like, f = foodie_id, cr = critic_id)
    return critic_profile(critic_id)

@app.route("/recommendation", methods = ['POST','GET'])
def recommendation():
  if 'username' in session:
    uid = session.get('username')
    cmd = "SELECT cuisine, price FROM foodies_prefer_categories WHERE foodie_id = :u"
    cursor = g.conn.execute(text(cmd), u = uid)
    for result in cursor:
        cuisine = result['cuisine']
        price = result['price']
    cmd = "SELECT home,work FROM foodie_set_location WHERE uid = :u"
    cursor = g.conn.execute(text(cmd), u = uid)
    for result in cursor:
        home = result['home']
        work = result['work']

    #home
    cmd = "SELECT restaurant.rid,  restaurant.name\
            FROM restaurant_is_at, restaurant_description,restaurant\
            WHERE zipcode = :h AND cuisine = :c AND price = :p\
            AND restaurant.rid = restaurant_description.rid\
            AND restaurant.rid = restaurant_is_at.rid"
    cursor = g.conn.execute(text(cmd), h = home, c = cuisine, p = price)
    home_rid =[]
    home_name= []
    for result in cursor:
        home_rid.append(result["rid"])
        home_name.append(result["name"])
    homeRestaurants = zip(home_rid, home_name)

    #work
    cmd = "SELECT restaurant.rid,  name\
            FROM restaurant_is_at, restaurant_description,restaurant\
            WHERE zipcode = :w AND cuisine = :c AND price = :p\
            AND restaurant.rid = restaurant_description.rid\
            AND restaurant.rid = restaurant_is_at.rid"
    cursor = g.conn.execute(text(cmd), w = work, c = cuisine, p = price)
    work_rid =[]
    work_name= []
    for result in cursor:
        work_rid.append(result["rid"])
        work_name.append(result["name"])
    workRestaurants = zip(work_rid, work_name)

    #near office
    cmd = "SELECT restaurant.rid, name\
            FROM restaurant, restaurant_is_at\
            WHERE restaurant.rid = restaurant_is_at.rid\
            AND zipcode = :w"
    cursor = g.conn.execute(text(cmd),  w = work)
    near_work_rid = []
    near_work_name = []
    for result in cursor:
        near_work_rid.append(result['rid'])
        near_work_name.append(result['name'])

    near_work = zip(near_work_rid, near_work_name)
    #near home
    cmd = "SELECT restaurant.rid, name\
            FROM restaurant, restaurant_is_at\
            WHERE restaurant.rid = restaurant_is_at.rid\
            AND zipcode = :h"
    cursor = g.conn.execute(text(cmd),  h = home)
    near_home_rid = []
    near_home_name = []
    for result in cursor:
        near_home_rid.append(result['rid'])
        near_home_name.append(result['name'])

    near_home = zip(near_home_rid, near_home_name)


    #critic recommendation
    cmd = "SELECT restaurant.rid, restaurant.name\
            FROM \
                (foodies_assess_critic INNER JOIN write_about \
                    ON foodies_assess_critic.critic_id = write_about.uid)\
                INNER JOIN reports ON reports.report_id = write_about.report_id\
                INNER JOIN restaurant ON write_about.rid = restaurant.rid\
            WHERE foodies_assess_critic.like_dislike = true\
                AND foodies_assess_critic.foodie_id = :f\
                AND reports.rating > 3"
    cursor = g.conn.execute(text(cmd), f = uid)
    critic_rid= []
    critic_name =[]
    for result in cursor:
        critic_rid.append(result['rid'])
        critic_name.append(result['name'])
    critic_recommend = zip(critic_rid,critic_name)

    context = dict(critic_recommend = critic_recommend, homeRestaurants = homeRestaurants,
                workRestaurants = workRestaurants,
                near_work = near_work,
                near_home = near_home, lenHome = len(homeRestaurants),
                lenWork = len(workRestaurants), lenNearHome = len(near_home),
                lenNearWork = len(near_work),foodie_id = uid, uname=session.get('username'))
    return render_template("recommendation.html",**context)
  else:
    return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
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
