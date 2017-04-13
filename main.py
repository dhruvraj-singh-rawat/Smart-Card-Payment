from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, UserTable, StatementHistory,StatementTable
from flask import session as login_session
import random
import string
import time
# IMPORTS FOR AUTHENTICATION

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from oauth2client.client import AccessTokenCredentials

#import for flask admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin 
# from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)
admin=Admin(app)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Digital Payment System"


# Connect to Database and create database session
engine = create_engine('sqlite:///digitalpayment.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

admin.add_view(ModelView(UserTable,session))
admin.add_view(ModelView(StatementTable,session))
admin.add_view(ModelView(StatementHistory,session))

@app.route('/dashboard')
def dashboard():

    if 'email' not in login_session:
        return redirect('/login')

    user_info = session.query(UserTable).filter_by(email=login_session.get('email')).one()

    return render_template('dashboard.html',token=login_session['access_token'],username=login_session['username'],
            email=login_session['email'],userinfo=user_info)

###################################################################################################


@app.route('/redirector')
def redirecter():

    

    if login_session.get('email')==None:
        return redirect('/login')

    email=login_session.get('email')
    user_type=getUserID(email)

    if user_type is not None:
        return redirect('/dashboard')
    else:

        domain=email[email.find("@"):]
        if domain.lower() == "@lnmiit.ac.in":

            return redirect('/createUser')


        else:
            gdisconnect()

            response=make_response(json.dumps('Login through LNMIIT Domain ID',400))
            response.headers['Content-Type']='application/json'
            return response




@app.route('/createUser', methods=['GET', 'POST'])
def createUser():

    if (login_session.get('email')==None):
        
        return redirect('/login')


    if request.method =='POST':
        email=login_session.get('email')
        rollno=email[:email.find("@")]

        if (request.form['rfid_no']!= None and request.form['rfid_pin']!= None ):

            newUser=UserTable(rollno=rollno,name=login_session.get('username'),email=login_session.get('email'),picture=login_session.get('picture'),
                pin=request.form['rfid_pin'],rfidno=request.form['rfid_no'],userLevel=1,
                )         

            session.add(newUser)
            session.commit()

            newUser_statement=StatementTable(balance=0,email=login_session.get('email'),account_holder=newUser)
            session.add(newUser_statement)
            session.commit()
            user=session.query(UserTable).filter_by(email=login_session.get('email')).one()
            if user is not None:
                return redirect('/dashboard')
            else:
                output="<p>Cannot save it to database.Try Again</p>"
                return output
        else:

            return redirect('/createUser')
    else:
        return render_template('createuser.html',username=login_session['username'],email=login_session['email'])


###################################################################################################

# API IMPLEMENTATION 

@app.route("/api_responce", methods = ['GET', 'POST'])
def api_responce():
    if request.method=='POST':

        rfid_no=request.args.get('rfid_no')

        menu_level=request.args.get('menu_level') 
        if menu_level!=None:
            menu_level=int(request.args.get('menu_level'))

        #shop_id=request.args.get('shop_id')
        pin=request.args.get('pin')
        payment=request.args.get('payment')
        if payment == None:
            payment=0

        
        remark=request.args.get('remark')
        

        if menu_level==None:

            if session.query(UserTable).filter_by(rfidno=rfid_no).count() > 0:            
                user_info = session.query(UserTable).filter_by(rfidno=rfid_no).one()
                name=user_info.name
                rollno=user_info.rollno
                # if menu_level==None:
                menu_level=1

                output={
                        'Name':name,
                        'Rfid_no':rfid_no,
                        'Status':1,
                        'rollno':rollno,
                        'Menu_level':menu_level,
                }

                return json.dumps(output)

                #return "This reply is from Server! RFID NO:%r and name:%r menu%r"%(rfid_no,name,menu_level)
            else:
                output={
                        'Status':0,
                        'Rfid_no':rfid_no,
                }
                return json.dumps(output)
                #return "This reply is from Server! RFID NO:%r NEW User"%(rfid_no)

        elif menu_level==1:
            user_info = session.query(UserTable).filter_by(rfidno=rfid_no).one()
            if user_info.pin==pin:
                menu_level=menu_level+1

                output={
                    'rfid_no':rfid_no,
                    'menu_level':menu_level,
                    'status':1,
                }
                return json.dumps(output)
            else:
                output={
                    'rfid_no':rfid_no,
                    'status':0,
                }
                return json.dumps(output)

        elif menu_level==2:
            user_info = session.query(UserTable).filter_by(rfidno=rfid_no).one()
            # user_statement=session.query(StatementTable).filter_by(email=user_info.email).one()
            # he=user_info.statementtable.one()
            balance_available=int(user_info.statementtable.one().balance)
            payment=int(payment)

            if balance_available>=payment:
                balance_available=balance_available-payment
                user_info.statementtable.one().balance=balance_available
                session.commit()
                output={
                    'status':1,

                }
                return json.dumps(output)
            else:
                output={
                    'status':0,
                }
                return json.dumps(output)



    elif request.method=='GET':

        response=make_response(json.dumps('GET is working',200))
        response.headers['Content-Type']='application/json'
        return response
        


####################################################################################################




####################################################################################################


def getUserInfo(user_id):
    user = session.query(UserTable).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(UserTable).filter_by(email=email).one()
        return user.id
    except:
        return None










####################################################################################################





# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)



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
    access_token = login_session.get('credentials')
    login_session['access_token']=access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'%credentials.access_token)
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output



@app.route('/gdisconnect')
def gdisconnect():

    access_token=login_session.get('credentials')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':

        del login_session['gplus_id']
        #del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token for given user. Access token %s'%access_token, 400))
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='127.0.0.1', port=5000)
    #app.run(host='127.0.0.1', port=5000)
