from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog.Data_Setup import Base, TractorName, ItemName,  User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
#engine = create_engine('sqlite:///tractors.db',
#                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('/var/www/catalog/catalog/client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Tractors"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
e1e5 = session.query(TractorName).all()


# login
@app.route('/login')
def showLogin():

    state = ''.join(random.choice(
                                 string.ascii_uppercase + string.digits
                                 )for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    e1e5 = session.query(TractorName).all()
    i1 = session.query(ItemName).all()
    return render_template('login.html',
                           STATE=state, e1e5=e1e5, i1=i1)
    # return render_template('myhome.html', STATE=state
    # e1e5=e1e5,i1=i1)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    User1 = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(User1)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#####
# Home


@app.route('/')
@app.route('/home')
def home():
    e1e5 = session.query(TractorName).all()
    return render_template('myhome.html', e1e5=e1e5)

#####
# Tractor category for admins


@app.route('/TractorHub')
def TractorHub():
    try:
        if login_session['username']:
            name = login_session['username']
            e1e5 = session.query(TractorName).all()
            g8 = session.query(TractorName).all()
            i1 = session.query(ItemName).all()
            return render_template('myhome.html', e1e5=e1e5,
                                   g8=g8, i1=i1, uname=name)
    except:
        return redirect(url_for('showLogin'))

######
# Showing tractors based on tractor category


@app.route('/TractorHub/<int:e0id>/AllTractors')
def showTractors(e0id):
    e1e5 = session.query(TractorName).all()
    g8 = session.query(TractorName).filter_by(id=e0id).one()
    i1 = session.query(ItemName).filter_by(tractornameid=e0id).all()
    try:
        if login_session['username']:
            return render_template('showTractors.html', e1e5=e1e5,
                                   g8=g8, i1=i1,
                                   uname=login_session['username'])
    except:
        return render_template('showTractors.html',
                               e1e5=e1e5, g8=g8, i1=i1)

#####
# Add New Tractor names


@app.route('/TractorHub/addTractorName', methods=['POST', 'GET'])
def addTractorName():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        tractorname = TractorName(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(tractorname)
        session.commit()
        return redirect(url_for('TractorHub'))
    else:
        return render_template('addTractorName.html', e1e5=e1e5)

########
# Edit Tractor Category


@app.route('/TractorHub/<int:e0id>/edit', methods=['POST', 'GET'])
def editTractorName(e0id):
    if 'username' not in login_session:
        return redirect('/login')
    editTractorName = session.query(TractorName).filter_by(id=e0id).one()
    creator = getUserInfo(editTractorName.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Tractor Name."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('TractorHub'))
    if request.method == "POST":
        if request.form['name']:
            editTractorName.name = request.form['name']
        session.add(editTractorName)
        session.commit()
        flash("Tractor Name Edited Successfully")
        return redirect(url_for('TractorHub'))
    else:
        # e1e5 is global variable we can change them in entire application
        return render_template('editTractorName.html',
                               e0=editTractorName, e1e5=e1e5)

######
# Delete Tractor Category


@app.route('/TractorHub/<int:e0id>/delete', methods=['POST', 'GET'])
def deleteTractorName(e0id):
    if 'username' not in login_session:
        return redirect('/login')
    e0 = session.query(TractorName).filter_by(id=e0id).one()
    creator = getUserInfo(e0.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Tractor Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('TractorHub'))
    if request.method == "POST":
        session.delete(e0)
        session.commit()
        flash("TractorName Deleted Successfully")
        return redirect(url_for('TractorHub'))
    else:
        return render_template('deleteTractorName.html', e0=e0, e1e5=e1e5)

######
# Add new tractor item Details


@app.route(
    '/TractorHub/addTractorName/addTractorItemDetails/<string:e0name>/add',
    methods=['GET', 'POST'])
def addTractorDetails(e0name):
    if 'username' not in login_session:
        return redirect('/login')
    g8 = session.query(TractorName).filter_by(name=e0name).one()
    # See if the logged in user is not the owner of tractor item
    creator = getUserInfo(g8.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add tractor item"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTractors', e0id=g8.id))
    if request.method == 'POST':
        name = request.form['name']
        engine = request.form['engine']
        price = request.form['price']
        liftcapacity = request.form['liftcapacity']
        itemdetails = ItemName(name=name, engine=engine,
                               price=price,
                               liftcapacity=liftcapacity,
                               date=datetime.datetime.now(),
                               tractornameid=g8.id,
                               user_id=login_session['user_id'])
        session.add(itemdetails)
        session.commit()
        return redirect(url_for('showTractors', e0id=g8.id))
    else:
        return render_template('addTractorItemDetails.html',
                               e0name=g8.name, e1e5=e1e5)

######
# Edit Tractor Item details


@app.route('/TractorHub/<int:e0id>/<string:excname>/edit',
           methods=['GET', 'POST'])
def editTractorItem(e0id, excname):
    if 'username' not in login_session:
        return redirect('/login')
    e0 = session.query(TractorName).filter_by(id=e0id).one()
    itemdetails = session.query(ItemName).filter_by(name=excname).one()
    # See if the logged in user is not the owner of tractor item
    creator = getUserInfo(e0.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this tractor item"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTractors', e0id=e0.id))
    # POST methods
    if request.method == 'POST':
        itemdetails.name = request.form['name']
        itemdetails.engine = request.form['engine']
        itemdetails.price = request.form['price']
        itemdetails.liftcapacity = request.form['liftcapacity']
        itemdetails.date = datetime.datetime.now()
        session.add(itemdetails)
        session.commit()
        flash("Item Edited Successfully")
        return redirect(url_for('showTractors', e0id=e0id))
    else:
        return render_template('editTractorItem.html',
                               e0id=e0id, itemdetails=itemdetails, e1e5=e1e5)

#####
# Delte Items in tractors hub


@app.route('/TractorHub/<int:e0id>/<string:excname>/delete',
           methods=['GET', 'POST'])
def deleteTractorItem(e0id, excname):
    if 'username' not in login_session:
        return redirect('/login')
    e0 = session.query(TractorName).filter_by(id=e0id).one()
    itemdetails = session.query(ItemName).filter_by(name=excname).one()
    # See if the logged in user is not the owner of tractor item
    creator = getUserInfo(e0.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this tractor item"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTractors', e0id=e0.id))
    if request.method == "POST":
        session.delete(itemdetails)
        session.commit()
        flash("Deleted item Successfully")
        return redirect(url_for('showTractors', e0id=e0id))
    else:
        return render_template('deleteTractorItem.html',
                               e0id=e0id, itemdetails=itemdetails, e1e5=e1e5)

####
# Logout from current user


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected....'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={
                      'content-type': 'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected user..'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('home'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#####
# Json


@app.route('/TractorHub/JSON')
def allTractorsJSON():
    tractornames = session.query(TractorName).all()
    category_dict = [c.serialize for c in tractornames]
    for c in range(len(category_dict)):
        tractors = [i.serialize for i in session.query(
            ItemName).filter_by(tractornameid=category_dict[c]["id"]).all()]
        if tractors:
            category_dict[c]["tractors"] = tractors
    return jsonify(TractorName=category_dict)

####


@app.route('/TractorHub/tractorName/JSON')
def categoriesJSON():
    tractors = session.query(TractorName).all()
    return jsonify(tractorName=[c.serialize for c in tractors])

####


@app.route('/TractorHub/tractors/JSON')
def itemsJSON():
    items = session.query(ItemName).all()
    return jsonify(tractors=[i.serialize for i in items])

#####


@app.route('/TractorHub/<path:tractor_name>/tractors/JSON')
def categoryItemsJSON(tractor_name):
    tractorName = session.query(TractorName).filter_by(name=tractor_name).one()
    tractors = session.query(ItemName).filter_by(tractorname=tractorName).all()
    return jsonify(tractorName=[i.serialize for i in tractors])

#####


@app.route('/TractorHub/<path:tractor_name>/<path:tractorItem_name>/JSON')
def ItemJSON(tractor_name, tractorItem_name):
    tractorName = session.query(TractorName).filter_by(name=tractor_name).one()
    tractorItemName = session.query(ItemName).filter_by(
           name=tractorItem_name, tractorname=tractorName).one()
    return jsonify(tractorItemName=[tractorItemName.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=9988)
