from flask import Flask, render_template, request,redirect, url_for,g,session, send_from_directory, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask import flash
from passlib.hash import sha256_crypt
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.apps import custom_app_context as pwd_context
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import csv
#from sklearn.externals import joblib
import joblib
import random
import os
import numpy as np
import pandas as pd
import camelot
from datetime import datetime, timedelta
import pickle



app = Flask(__name__)

app.config.from_pyfile('config.cfg')
mail = Mail(app)
s = URLSafeTimedSerializer('Thisisasecret!')

app.config['MySQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sih'


mysql = MySQL(app)

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to login first","error")
			return redirect(url_for('login'))

	return wrap


def login_required_company(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in_company' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to login first","error")
			return redirect(url_for('login'))

	return wrap

#***********************Submit test part begins*******************************************



@app.route('/takethetest/<aid>')
@login_required
def read_celltemp(aid):
    score = 0
    inc = 0

    sql = "SELECT * FROM app_status WHERE appid = %s"
    cur = mysql.connection.cursor()

    aresult = cur.execute(sql, [aid])
    adata = cur.fetchall()
    isattempted = 0
    if adata[0][6] != 'Not Attempted':
        isattempted = 1

    return render_template("button.html", isattempted = isattempted, aid = aid, inc = int(inc), score=int(score))




@app.route("/read_cell/<aid>", methods=['POST','GET'])
@login_required
def read_cell(aid):
    

    inc = request.form['inc']
    score = request.form['score']
    # Reading the CSV file of questions
    with open('./static/ques_data.csv') as csvfile:
        readCSV = list(csv.reader(csvfile, delimiter=','))

        # Displaying First question to the user of Medium Level 0 Difficulty


        
        qid = random.choice(range(0,651,1)) # Randomly selecting one question index
        row_you_want = readCSV[qid]
        question=row_you_want[2]
        option1=row_you_want[3]
        option2=row_you_want[4]
        option3=row_you_want[5]
        option4=row_you_want[6]
        correct_answer1=row_you_want[8] 
        ID = qid

        return render_template('12.html', question=question, option1=option1, option2=option2, option3=option3, option4=option4,score=score, ID = ID, correct_answer = correct_answer1, inc = int(inc), a = aid)


@app.route('/check_answer/<aid>', methods=['POST','GET'])
@login_required
def check_answer(aid):
    # Retriving timer value from 12.html(this value is hidden in 12.html).This value is retrived only when user clicks the Next button.
    if request.method == 'POST':
      user = int(request.form['nm'])
    else:
      user = int(60) # If the user runs out of time and doesn't click the next button then the respopnse time 60 seconds is stored here
    

    inc = int(request.form['inc'])
    score = int(request.form['score'])
    correct_answer1 = request.form['correct_answer1']

    with open('./static/ques_data.csv') as csvfile:
        readCSV = list(csv.reader(csvfile, delimiter=','))

        
        given_answer = request.form.get('option')
        correct_answer = correct_answer1

        if  given_answer == correct_answer1:
            correct_answer1 = 1
            score+=1
            return test(user = user, aid = aid, inc = inc, score = score)

        else:
            correctness=0
            return test(user = user, aid = aid, inc = inc, score = score)



       

@app.route('/test', methods=['POST','GET'])

@login_required
def test(user, aid, inc, score):
    

    res_time=user

    
    correctness=0
    with open('./static/Test.csv') as csvfile:
        pred_read = list(csv.reader(csvfile, delimiter=','))
        with open('./static/ques_data.csv') as csvfile:
            readCSV = list(csv.reader(csvfile, delimiter=','))
            # Displaying 30 questions to the user
            if(inc<9):

                qid = random.choice(range(0,651,1))
                row_you_want1 = readCSV[qid]
                question=row_you_want1[2]
                option1=row_you_want1[3]
                option2=row_you_want1[4]
                option3=row_you_want1[5]
                option4=row_you_want1[6]
                correct_answer1 = row_you_want1[8]
                curr_level=int(float(row_you_want1[12]))
                ID=qid
                inc+=1
                return render_template('12.html', question=question, option1=option1, option2=option2, option3=option3, option4=option4,score=score,res_time=res_time,ID=ID,user=user, correct_answer = correct_answer1, inc= inc, a = aid)
                
            if(inc==9):
                # Calculating and displaying final score after the user has attempted all the 30 questions
                score = score
                return redirect(url_for('final_score', score=score, aid = aid))

@app.route('/final_score')
def final_score():

    s = request.args['score']
    a = request.args['aid']
    
    cur = mysql.connection.cursor()

    sql = "UPDATE app_status SET test_score = %s WHERE appid = %s"
    cur.execute (sql, (s,a))
    mysql.connection.commit()
    cur.close()
    
    return render_template('final.html', score=s, aid = a)




#****************************Submit Test ends***********************************************


	  
@app.route('/')
def home():
	session.clear()
	return render_template('index.html')

@app.route('/create_account', methods = ['GET', 'POST'])
def create_account():
	global fields
	fields = ()
	choice = request.form.get('role')
	if request.method == 'POST':
		if(choice == "candidate" ):
			cursor = mysql.connection.cursor()
			uname = request.form.get('uname')
			cursor.execute("SELECT * FROM register WHERE uname = %s", [uname])
			if cursor.fetchone() is not None:
				flash("The username is already taken...", "error")
				return render_template('create-account.html')
			else:
				fname = request.form.get('fname')
				mname = request.form.get('mname')
				lname = request.form.get('lname')
				email = request.form.get('email')
				dob = request.form.get('dob')
				phone = request.form.get('phone')
				address = request.form.get('address')
				state = request.form.get('state')
				city = request.form.get('city')
				gender = request.form.get('gender')
				description = request.form.get('description')
				password = request.form.get('password')
				password = pwd_context.hash(password)
				
				fields = (uname, fname, mname, lname,phone, email, dob, address, gender, city, state, password, description)
				flash(fields)
				
				token = s.dumps(email, salt='email-confirm')
				msg = Message('Confirm Email', sender='code.crunch.sih@gmail.com', recipients=[email])
				link = url_for('confirm_email', token=token, _external=True)
				msg.body = 'Your link is {}'.format(link)
				mail.send(msg)

				return '<h1>The email you entered is {}. Please click the link in your mail for account verification!'.format(email)
   

				

		elif(choice == "company"):
			cursor = mysql.connection.cursor()
			compid = request.form.get('compid')
			cursor.execute("SELECT * FROM company_register WHERE compid = %s", [compid])
			if cursor.fetchone() is not None:
				flash("The username is already taken...", "error")
				return render_template('create-account.html')
			else:
				compname = request.form.get('compname')
				estdate = request.form.get('estdate')
				compaddress = request.form.get('compaddress')
				compemail = request.form.get('compemail')
				compurl = request.form.get('compurl')
				compphone = request.form.get('compphone')
				compdescription = request.form.get('compdescription')
				comppassword = request.form.get('comppassword')
				comppassword = pwd_context.hash(comppassword)
				
				fields = (compid, compname, estdate, compaddress, compemail, compurl, compphone, compdescription, comppassword)

				token = s.dumps(compemail, salt='email-confirm')
				msg = Message('Confirm Email', sender='code.crunch.sih@gmail.com', recipients=[compemail])
				link = url_for('confirm_email_company', token=token, _external=True)
				msg.body = 'Your link is {}'.format(link)
				mail.send(msg)

				return '<h1>The email you entered is {}. Please click the link in your mail for account verification!'.format(compemail)
		
				

	return render_template('create-account.html')


@app.route('/confirm_email/<token>')
def confirm_email(token):
	try:
		email = s.loads(token, salt='email-confirm', max_age=3600)
		cursor = mysql.connection.cursor()
		sql_insert_blob_query = """ INSERT INTO register(uname, fname, mname, lname,phone, email, dob, address, sex, city, state, password, descr) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
		global fields
		print(fields)
		cursor.execute(sql_insert_blob_query,fields)
		del(fields)
		mysql.connection.commit()
		cursor.close()

		flash('You are now registered and can log in', 'success')
		return redirect(url_for('login'))
	except SignatureExpired:
		return '<h1>The token is expired!</h1>'


@app.route('/confirm_email_company/<token>')
def confirm_email_company(token):
	try:
		email = s.loads(token, salt='email-confirm', max_age=3600)
		cursor = mysql.connection.cursor()
		sql_insert_blob_query = """ INSERT INTO company_register(compid, compname, doe, compaddress, compemail, compurl, compphone, compdescription, comppassword) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
		global fields
		print(fields)
		cursor.execute(sql_insert_blob_query,fields)
		del(fields)
		mysql.connection.commit()
		cursor.close()

		flash('You are now registered and can log in', 'success')
		return redirect(url_for('login'))
	except SignatureExpired:
		return '<h1>The token is expired!</h1>'
	

def convertToBinaryData(filename):
	# Convert digital data to binary format
	with open(filename, 'rb') as file:
		binaryData = file.read()
	return binaryData

@app.route('/login', methods = ['GET', 'POST'])
# @login_required
def login():

	if request.method == 'POST':
		session.pop('username', None)
		session.pop('comp_username', None)
		cursor = mysql.connection.cursor()
		choice = request.form.get('role')
		if(choice == "candidate"):
			uname = request.form.get('uname')
			password = request.form.get('password')
			result = cursor.execute("SELECT * FROM register WHERE uname = %s", [uname])
			if result > 0:
				data = cursor.fetchone()
				password_db = data[11]
				if (pwd_context.verify(password, password_db)):
					session['logged_in'] = True
					session['username'] = uname
					flash('You are now logged in', 'success')
					return redirect(url_for('cdashboard'))
				else:
					flash('Invalid Login', 'error')
					return render_template('login.html')
				cursor.close()
			else:
				flash('User not found', 'error')
				return render_template('login.html')

		elif(choice == "company"):
			uname = request.form.get('uname')
			password = request.form.get('password')
			result = cursor.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
			if result > 0:
				data = cursor.fetchone()
				password_db = data[8]
				if (pwd_context.verify(password, password_db)):
					session['logged_in_company'] = True
					session['comp_username'] = uname
					flash('You are now logged in', 'success')
					return redirect(url_for('compdashboard'))
				else:
					flash('Invalid Login', 'error')
					return render_template('login.html')
				cursor.close()
			else:
				flash('User not found', 'error')
				return render_template('login.html')

	return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

@app.route('/logout_company')
@login_required_company
def logout_company():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))



@app.route('/changepassword',methods=['POST','GET'])
@login_required
def changepassword():
	if request.method =='POST':
		curpw=request.form.get('curpw')
		newpw=request.form.get('newpw')
		newcpw= request.form.get('newcpw')
		if(newpw != newcpw):
			flash("Passwords dont match!","error")
			return redirect(url_for('cdashboard'))
		else:
			newpw = pwd_context.hash(newpw)
			sql=""" UPDATE register SET password = %s WHERE uname= %s"""
			cursor = mysql.connection.cursor()
			cursor.execute(sql,(newpw,session['username']))
			mysql.connection.commit()
			cursor.close()
			flash("Password Changed Successfully","success")
			return redirect(url_for('cdashboard'))          
	return redirect(url_for('cdashboard'))

@app.route('/changepasswordcompany',methods=['POST','GET'])
@login_required_company
def changepasswordcompany():
	if request.method =='POST':
		curpw=request.form.get('curpw')
		newpw=request.form.get('newpw')
		newcpw= request.form.get('newcpw')
		if(newpw != newcpw):
			flash("Passwords dont match!","error")
			return redirect(url_for('compdashboard'))
		else:
			newpw = pwd_context.hash(newpw)
			sql=""" UPDATE company_register SET comppassword = %s WHERE compid= %s"""
			cursor = mysql.connection.cursor()
			cursor.execute(sql,(newpw,session['comp_username']))
			mysql.connection.commit()
			cursor.close()
			flash("Password Changed Successfully","success")
			return redirect(url_for('compdashboard'))          
	return redirect(url_for('compdashboard'))


@app.route('/sendemail', methods=['POST','GET'])
def sendemail():
	if request.method =="POST":
		rstpw = request.form.get("rstpw")
		token = s.dumps(rstpw, salt='passwordreset')
		msg = Message('Click link to reset password', sender='code.crunch.sih@gmail.com', recipients=[rstpw])
		link = url_for('resetpassword', token=token, _external=True)
		msg.body = 'Your link is {}'.format(link)
		mail.send(msg)

		return '<h1>The email you entered is {}. Please click the link in your mail for password reset!'.format(rstpw)

@app.route('/resetpassword/<token>')
def resetpassword(token):
	try:
		rstpw = s.loads(token, salt='passwordreset', max_age=600)
		return redirect(url_for('passwordresetform'))
	except SignatureExpired:
		return '<h1>The token is expired!</h1>'

@app.route('/passwordresetform', methods=['POST','GET'])
def passwordresetform():
	if request.method == 'POST':
		role = request.form.get('role')
		email = request.form.get('email')
		password = request.form.get('password')
		password = pwd_context.hash(password)

		if( role == "candidate"):
			sql = """ UPDATE register SET password = %s WHERE email= %s """
			cursor = mysql.connection.cursor()
			cursor.execute(sql,(password,email))
			mysql.connection.commit()
			cursor.close()
			flash("Password Changed Successfully","success")
			return redirect(url_for('login'))
		elif( role == "company"):
			sql = """ UPDATE company_register SET password = %s WHERE email= %s """
			cursor = mysql.connection.cursor()
			cursor.execute(sql,(password,email))
			mysql.connection.commit()
			cursor.close()
			flash("Password Changed Successfully","success")
			return redirect(url_for('login'))
	return render_template('passwordresetform.html')




#*******************************company pages start***************************************



@app.route('/compdashboard')
@login_required_company
def compdashboard():
	uname=session['comp_username']


	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname] )
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydashboard.html',tcfow=tcfowd,tfow=tfowd,  detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)

@app.route('/compdashboardgeoloc')
@login_required_company
def compdashboardgeoloc():
	uname=session['comp_username']
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname])
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydashboard.html', scroll="geotag" ,tcfow=tcfowd,tfow=tfowd, detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)

@app.route('/compdashboardaward')
@login_required_company
def compdashboardaward():
	uname=session['comp_username']
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname])
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydashboard.html', scroll="awardtag" ,tcfow=tcfowd,tfow=tfowd, detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)


@app.route('/compdashboardfow')
@login_required_company
def compdashboardfow():
	uname=session['comp_username']
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname] )
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydashboard.html', scroll="aowtag" ,tcfow=tcfowd,tfow=tfowd, detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)


@app.route('/compdashboardkey')
@login_required_company
def compdashboardkey():
	uname=session['comp_username']
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname] )
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydashboard.html', scroll="keytag" , tcfow=tcfowd,tfow=tfowd, detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)


#*****************************company pages end********************************************

#******************************Candidate pages start**************************************

@app.route('/cdashboard')
@login_required
def cdashboard():
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	return render_template('candidatedashboard.html', students=edudata,detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)


@app.route('/cdashboardwork')
@login_required
def cdashboardwork():
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	print(Mdata)
	return render_template('candidatedashboard.html', scroll='worktag',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)



@app.route('/cdashboardedu')
@login_required
def cdashboardedu():
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	return render_template('candidatedashboard.html', scroll='educationtag',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)

@app.route('/cdashboardlink')
@login_required
def cdashboardlink():
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()
	print(lnkdata)

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	return render_template('candidatedashboard.html', scroll='linktag',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)

@app.route('/cdashboardskill')
@login_required
def cdashboardskill():
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	
	return render_template('candidatedashboard.html', scroll='skilltag',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)


#********************************Candidate Pages end********************************************************

#**************Details start *******************************
# @app.route('/cdashboarddetail')
# @login_required
# def cdashboarddetail():
# 	uname = session['username'] 
# 	cursoredu = mysql.connection.cursor()
# 	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
# 	edudata = cursoredu.fetchall()
# 	cursoredu.close()
# 	cursorskl = mysql.connection.cursor()
# 	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
# 	skdata = cursorskl.fetchall()
# 	cursorskl.close()
# 	cursorlnk = mysql.connection.cursor()
# 	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
# 	lnkdata = cursorlnk.fetchall()
# 	cursorskl.close()
# 	cursorlnk = mysql.connection.cursor()
# 	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
# 	workdata = cursorlnk.fetchall()
# 	cursorskl.close()
# 	cursorlnk = mysql.connection.cursor()
# 	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
# 	Mdata = cursorlnk.fetchall()
# 	cursorskl.close()
	
# 	return render_template('candidatedashboard.html', scroll='detailtag',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)




@app.route('/companydetails')
@login_required_company
def companydetails():
	uname=session['comp_username']


	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [uname] )
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()
	return render_template('companydetails.html',tcfow=tcfowd,tfow=tfowd,  detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)

@app.route('/publiccompanydetails/<compid>')
def publiccompanydetails(compid):
	#uname=session['comp_username']


	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM award WHERE compid = %s", [compid])
	skdata = cursorskl.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM geoloc WHERE compid = %s", [compid])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM keypeep WHERE compid = %s", [compid])
	workdata = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [compid])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()


	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM fow ")
	tfowd = cursorlnk.fetchall()
	cursorskl.close()

	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM compfow WHERE compid = %s", [compid] )
	tcfowd = cursorlnk.fetchall()
	cursorlnk.close()

	return render_template('companydetails.html',tcfow=tcfowd,tfow=tfowd,  detail=Mdata, tlinks=lnkdata, tskills=skdata, twork=workdata)


@app.route('/candidatedetails')
@login_required
def candidatedetails():
	
	uname = session['username'] 
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	return render_template('candidatedetails.html',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)

@app.route('/publiccandidatedetails/<duname>')
def publiccandidatedetails(duname):
	
	uname = duname
	cursoredu = mysql.connection.cursor()
	result1 = cursoredu.execute("SELECT * FROM edu WHERE uname = %s", [uname])
	edudata = cursoredu.fetchall()
	cursoredu.close()
	cursorskl = mysql.connection.cursor()
	result2 = cursorskl.execute("SELECT * FROM skills WHERE uname = %s", [uname])
	skdata = cursorskl.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result3 = cursorlnk.execute("SELECT * FROM link WHERE uname = %s", [uname])
	lnkdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM work WHERE uname = %s", [uname])
	workdata = cursorlnk.fetchall()
	cursorskl.close()
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM register WHERE uname = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorskl.close()
	return render_template('candidatedetails.html',detail=Mdata, students=edudata, twork=workdata, tlinks=lnkdata, tskills=skdata)


#********************************Details page ends*************************************************

@app.route('/candidatelist')
def candidatelist():
	return render_template('candidatelist.html')

@app.route('/companylist')
def companylist():
	return render_template('companylist.html')


#**************************** details operations start ****************************
@app.route('/updatedetails', methods = ['POST'])
@login_required
def updatedetails():
	if request.method == "POST":
		fname = request.form.get('fname')
		mname = request.form.get('mname')
		lname = request.form.get('lname')
		email = request.form.get('email')
		dob = request.form.get('dob')
		phone = request.form.get('phone')
		address = request.form.get('address')
		state = request.form.get('state')
		city = request.form.get('city')
		gender = request.form.get('gender')
		description = request.form.get('description')
		uname = session['username'] 
		cur = mysql.connection.cursor()
		cur.execute("""
			   UPDATE register
			   SET fname=%s, mname=%s, lname=%s,phone=%s, email=%s, dob=%s, address=%s, sex=%s, city=%s, state=%s, descr=%s
			   WHERE uname=%s
			""", (fname, mname, lname,phone, email, dob, address, gender, city, state, description,uname))
		mysql.connection.commit()
		return redirect(url_for('cdashboarddetail'))
		
				
#**************************** Details operations end****************************


#**************************** Education operations start ****************************
@app.route('/insertedu', methods = ['POST'])
@login_required
def insertedu():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		Titleedu = request.form['Titleedu']
		degree = request.form['Degreeedu']
		inst = request.form['Instedu']
		year = request.form['Yearedu']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `edu` (`uname`, `title`, `degree`, `institute`, `year`) VALUES (%s, %s, %s, %s, %s)", (uname, Titleedu, degree, inst, year))
		mysql.connection.commit()
		return redirect(url_for('cdashboardedu'))





@app.route('/deleteedu/<string:id_data>', methods = ['GET'])
@login_required
def deleteedu(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM edu WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('cdashboardedu'))





@app.route('/updateedu',methods=['POST','GET'])
@login_required
def updateedu():

	if request.method == 'POST':
		Titleedu = request.form['Titleedu']
		degree = request.form['Degreeedu']
		inst = request.form['Instedu']
		year = request.form['Yearedu']
		srno = request.form['srno']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		s=(Titleedu, degree, inst, year, srno)
		print(s)
		cur.execute("""
			   UPDATE edu
			   SET title=%s, degree=%s, institute=%s, year=%s
			   WHERE srno=%s
			""", (Titleedu, degree, inst, year, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('cdashboardedu'))
#**************************** Education operations end****************************


#****************************skill operations start****************************
@app.route('/insertskill', methods = ['POST'])
@login_required
def insertskill():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		percent = request.form['prcnt']
		skname = request.form['skname']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `skills` (`uname`, `skname`, `percent`)VALUES (%s, %s, %s)", (uname, skname, percent))
		mysql.connection.commit()
		return redirect(url_for('cdashboardskill'))





@app.route('/deleteskill/<string:id_data>', methods = ['GET'])
@login_required
def deleteskill(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM skills WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('cdashboardskill'))





@app.route('/updateskill',methods=['POST','GET'])
@login_required
def updateskill():

	if request.method == 'POST':
		percent = request.form['prcnt']
		skname = request.form['skname']
		uname = session['username'] 
		srno = request.form['srno']
		cur = mysql.connection.cursor()
		print((skname, percent, uname))
		cur.execute("""
			   UPDATE skills
			   SET skname=%s, percent=%s
			   WHERE srno=%s
			""", (skname, percent, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('cdashboardskill'))

#****************************skill operations end****************************

#****************************Work operations end****************************
@app.route('/insertwork', methods = ['POST'])
@login_required
def insertwork():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		jobtitle = request.form['jobtitle']
		org = request.form['org']
		duration = request.form['dur']
		yearwork = request.form['yearwork']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `work` (`uname`, `jobtitle`, `org`, `duration`, `year`) VALUES (%s, %s, %s, %s, %s)", (uname, jobtitle, org, duration, yearwork))
		mysql.connection.commit()
		return redirect(url_for('cdashboardwork'))





@app.route('/deletework/<string:id_data>', methods = ['GET'])
@login_required
def deletework(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM work WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('cdashboardwork'))





@app.route('/updatework',methods=['POST','GET'])
@login_required
def updatework():

	if request.method == 'POST':
		jobtitle = request.form['jobtitle']
		org = request.form['org']
		duration = request.form['dur']
		yearwork = request.form['yearwork']
		srno = request.form['srno']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		print((jobtitle, org, duration, yearwork, srno))
		cur.execute("""
			   UPDATE work
			   SET jobtitle=%s, org=%s, duration=%s, year=%s
			   WHERE srno=%s
			""", (jobtitle, org, duration, yearwork, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('cdashboardwork'))
#**************************** Work operations end****************************



#****************************link operations start****************************

@app.route('/insertlink', methods = ['POST'])
@login_required
def insertlink():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		value = request.form['value']
		link = request.form['link']
		uname = session['username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `link` (`link`, `value`, `uname`)VALUES (%s, %s, %s)", (link, value, uname))
		mysql.connection.commit()
		return redirect(url_for('cdashboardlink'))





@app.route('/deletelink/<string:id_data>', methods = ['GET'])
@login_required
def deletelink(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM link WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('cdashboardlink'))





@app.route('/updatelink',methods=['POST','GET'])
@login_required
def updatelink():

	if request.method == 'POST':
		value = request.form['value']
		link = request.form['link']
		uname = session['username'] 
		srno = request.form['srno']
		cur = mysql.connection.cursor()
		print((link, value, uname,srno))
		cur.execute("""
			   UPDATE link
			   SET link=%s, value=%s
			   WHERE srno=%s
			""", (link, value, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('cdashboardlink'))
#****************************link operations end****************************



@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contactform', methods=['GET','POST'])
def contactform():
	if request.method == "POST":
		flash("Data Inserted Successfully")
		name = request.form.get('name')
		email = request.form.get('email')
		phone_number = request.form.get('phone_number')
		msg_subject = request.form.get('msg_subject')
		message = request.form.get('message') 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `contact` (`name`, `email`, `phone_number`, `msg_subject`, `message`) VALUES (%s, %s, %s, %s, %s)", (name, email, phone_number, msg_subject, message))
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('contactform'))
	return render_template('contact.html') 


@app.route('/addblog', methods = ['GET', 'POST'])
def addblog():
	if request.method == 'POST':
		cursor = mysql.connection.cursor()

		pname = request.form.get('pname')
		email = request.form.get('email')
		dob = request.form.get('dob')
		phone = request.form.get('phone')
		blogg = request.form.get('blogg')

		sql_insert_blob_query = """ INSERT INTO blog(pname, email,dob,phone, blogg) VALUES (%s,%s,%s,%s,%s)"""
		cursor.execute(sql_insert_blob_query,(pname, email, dob, phone, blogg ))
		mysql.connection.commit()
		cursor.close()

	return render_template('addblog.html')

@app.route('/blog')
def blog():
	return render_template('blog.html')





#**************************** company details operations start ****************************
@app.route('/updatecompdetails', methods = ['POST'])
@login_required_company
def updatecompdetails():
	if request.method == "POST":

		compname = request.form.get('compname')
		estdate = request.form.get('estdate')
		compaddress = request.form.get('compaddress')
		compemail = request.form.get('compemail')
		compurl = request.form.get('compurl')
		compphone = request.form.get('compphone')
		compdescription = request.form.get('compdescription')
		uname = session['comp_username'] 
		cur = mysql.connection.cursor()
		cur.execute(""" 
					UPDATE company_register
					SET compname=%s, doe=%s, compaddress=%s, compemail=%s, compurl=%s, compphone=%s, compdescription=%s
					where compid = %s
				""",(compname, estdate, compaddress, compemail, compurl, compphone, compdescription,uname ))
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('compdashboard'))
		
				
#**************************** company Details operations end****************************



#**************************** Field of work operations start ****************************
@app.route('/insertaow', methods = ['POST'])
@login_required_company
def insertaow():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		cfow = request.form.getlist('cfow')
		uname = session['comp_username'] 
		cur = mysql.connection.cursor()
		print(cfow)

		for i in cfow:
			cur.execute("INSERT INTO `compfow` (`compid`, `fow`) VALUES (%s, %s)", (uname, i))
			mysql.connection.commit()
		return redirect(url_for('compdashboardfow'))





@app.route('/deleteaow/<string:id_data>', methods = ['GET'])
@login_required_company
def deleteaow(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM compfow WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('compdashboardfow'))



#**************************** field of work operations end****************************

#**************************** Geo Location operations start ****************************
@app.route('/insertgeo', methods = ['POST'])
@login_required_company
def insertgeo():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		compcity = request.form['compcity']
		compcount = request.form['compcount']
		uname = session['comp_username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `geoloc` (`compid`, `city`,`country`) VALUES (%s, %s, %s)", (uname, compcity,compcount))
		mysql.connection.commit()
		return redirect(url_for('compdashboardgeoloc'))





@app.route('/deletegeo/<string:id_data>', methods = ['GET'])
@login_required_company
def deletegeo(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM geoloc WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('compdashboardgeoloc'))


@app.route('/updategeo',methods=['POST','GET'])
@login_required_company
def updategeo():

	if request.method == 'POST':
		compcity = request.form['compcity']
		compcount = request.form['compcount']
		srno = request.form['srno']
		cur = mysql.connection.cursor()
		cur.execute("""
			   UPDATE geoloc
			   SET compcity=%s, compcount=%s
			   WHERE srno=%s
			""", (compcity, compcount, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('compdashboardgeoloc'))
#**************************** geo location operations end****************************

#**************************** Awards operations start ****************************
@app.route('/insertaward', methods = ['POST'])
@login_required_company
def insertaward():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		awardtitle = request.form['awardtitle']
		from_org = request.form['from_org']
		awardyear = request.form['awardyear']
		uname = session['comp_username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `award` (`compid`, `title`,`from_org`,`year`) VALUES (%s, %s, %s, %s)", (uname, awardtitle,from_org,awardyear))
		mysql.connection.commit()
		return redirect(url_for('compdashboardaward'))





@app.route('/deleteaward/<string:id_data>', methods = ['GET'])
@login_required_company
def deleteaward(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM award WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('compdashboardaward'))


@app.route('/updateaward',methods=['POST','GET'])
@login_required_company
def updateaward():

	if request.method == 'POST':
		awardtitle = request.form['awardtitle']
		from_org = request.form['from_org']
		awardyear = request.form['awardyear']
		srno = request.form['srno']
		cur = mysql.connection.cursor()
		print((link, value, uname,srno))
		cur.execute("""
			   UPDATE award
			   SET title=%s, from_org=%s, year=%s
			   WHERE srno=%s
			""", (awardtitle, from_org, awardyear, srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('compdashboardaward'))
#**************************** Awards operations end****************************

#**************************** kep people operations start ****************************
@app.route('/insertkey', methods = ['POST'])
@login_required_company
def insertkey():

	if request.method == "POST":
		flash("Data Inserted Successfully")
		name = request.form['keyname']
		designation = request.form['keydesig']
		uname = session['comp_username'] 
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `keypeep` (`compid`, `name`,`designation`) VALUES (%s, %s, %s)", (uname, name, designation))
		mysql.connection.commit()
		return redirect(url_for('compdashboardkey'))





@app.route('/deletekey/<string:id_data>', methods = ['GET'])
@login_required_company
def deletekey(id_data):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM keypeep WHERE srno=%s", (id_data,))
	mysql.connection.commit()
	return redirect(url_for('compdashboardkey'))


@app.route('/updatekey',methods=['POST','GET'])
@login_required_company
def updatekey():

	if request.method == 'POST':
		name = request.form['keyname']
		designation = request.form['keydesig']
		srno = request.form['srno']
		cur = mysql.connection.cursor()
		cur.execute("""
			   UPDATE keypeep
			   SET name=%s, designation=%s
			   WHERE srno=%s
			""", (name, designation,srno))
		flash("Data Updated Successfully")
		mysql.connection.commit()
		return redirect(url_for('compdashboardkey'))
#**************************** kep people operations end****************************



#*****************************Functions related to job**************************************#

@app.route('/postajob')
@login_required_company
def postajob():
	df = pd.DataFrame()
	return render_template('postajob.html',  tables=[df.to_html(classes='table table-hover', table_id="tblData" ,header="true")])



@app.route('/uploadajax', methods=("POST", "GET"))
def upldfile():
	basedir = os.path.abspath(os.path.dirname(__file__))
	print("Upload Ajax")
	if request.method == 'POST':
		files = request.files['file']
		#if files and allowed_file(files.filename):
		filename = secure_filename(files.filename)
		app.logger.info('FileName: ' + filename)
		updir = os.path.join(basedir, 'static/')
		files.save(os.path.join(updir, filename))
		file_size = os.path.getsize(os.path.join(updir, filename))
		print(filename)
		# myFunc(filename)s
		full_filename = os.path.join('static/', filename)
		print(full_filename)

		tables = camelot.read_pdf(full_filename)
		df = tables[0].df
		new_header = df.iloc[0] 
		df = df[1:] 
		df.columns = new_header

		print(df)
		t = df.to_html(classes='table table-hover', table_id="tblData", header="true")
		return jsonify(name=filename, size=file_size, user_image=full_filename, table = t)


@app.route('/uploadfajax', methods=("POST", "GET"))
@login_required_company
def upldjob():
	if request.method == 'POST':
		cur = mysql.connection.cursor()
		_json = request.json
		_jtl  = _json['jtl']
		_al  = _json['al'] 
		_sal  = _json['sal'] 
		_vac  = _json['vac'] 
		_loc  = _json['loc'] 
		_ld  = _json['ld'] 
		_exp  = _json['exp'] 
		_jtype  = _json['jtype'] 
		_jd  = _json['jd']
		_compid = session['comp_username']
		if _ld != "":
			_ldo = datetime.strptime(_ld, "%Y-%m-%d")
			_ld = _ldo.strftime("%Y-%m-%d")
		'''INSERT INTO `jobs`(`jtitle`, `jdescription`, `jagelimit`, `compid`, `jsalary`, `jvacancies`, `jlocation`, `jlastd`, `jtype`, `jexperience`)
		 VALUES ('Java Developer', 'developing java apps', 55, 200000, 500.0, 10, 'Banglore', STR_TO_DATE('10-09-2020', '%d-%m-%Y'), 'Full Time', 5) '''
		sql = """ INSERT INTO `jobs`(`jtitle`, `jdescription`, `jagelimit`, `compid`, `jsalary`, `jvacancies`, `jlocation`, `jlastd`, `jtype`, `jexperience`)
		 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
		cur.execute(sql,(_jtl, _jd, _al, _compid, _sal, _vac, _loc, _ld, _jtype, _exp))
		mysql.connection.commit()
		cur.close()

		resp = jsonify({'message' : 'Data Uploaded Successfully!'})
		resp.status_code = 201
		return resp


@app.route('/joblist')
def joblist():
	jcursor = mysql.connection.cursor()
	jresult = jcursor.execute("SELECT * FROM `jobs`")
	jdata = list(jcursor.fetchall())
	jcursor.close()
	for j in jdata:
		print("Job Title: {}".format(j[1]))
		print("Job Description: {}".format(j[2]))
		print("Job Age Limit: {}".format(j[3]))
		print("Job Company ID: {}".format(j[4]))
		print("Job Salary: {}".format(j[5]))
		print("Job Vacancies: {}".format(j[6]))
		print("Job Location: {}".format(j[7]))
		print("Date of Post: {}".format(j[8]))
		print("Last Date to Apply: {}".format(j[9]))
		print("Job Type: {}".format(j[10]))
		print("Expereince Required: {}".format(j[11]))
	return render_template('joblist.html', data = jdata)

@app.route('/jobdetails/<job_id>', methods = ['GET'])
def getjobdetails(job_id):
	print("Jobid: {}".format(job_id))
	jcursor = mysql.connection.cursor()
	sql = """SELECT * FROM `jobs` WHERE `jid` = %s"""
	jresult = jcursor.execute(sql,[job_id])
	job = list(jcursor.fetchall())
	jobdetlist = list(job[0])
	jcursor.close()
	print("Job Title: {}".format(jobdetlist[1]))
	print("Job Description: {}".format(jobdetlist[2]))
	print("Job Age Limit: {}".format(jobdetlist[3]))
	print("Job Company ID: {}".format(jobdetlist[4]))
	print("Job Salary: {}".format(jobdetlist[5]))
	print("Job Vacancies: {}".format(jobdetlist[6]))
	print("Job Location: {}".format(jobdetlist[7]))
	print("Date of Post: {}".format(jobdetlist[8].strftime('%d-%m-%Y')))
	print("Last Date to Apply: {}".format(jobdetlist[9].strftime('%d-%m-%Y')))

	diff = jobdetlist[9] - datetime.now()
	jobdetlist.append(diff.days)
	print("Days Left: {}".format(jobdetlist[12]))

	print("Job Type: {}".format(jobdetlist[10]))
	print("Expereince Required: {}".format(jobdetlist[11]))


	uname=jobdetlist[4]
	cursorlnk = mysql.connection.cursor()
	result4 = cursorlnk.execute("SELECT * FROM company_register WHERE compid = %s", [uname])
	Mdata = cursorlnk.fetchall()
	cursorlnk.close()


	return render_template('jobdetails.html', data = jobdetlist, jtable=Mdata)

@app.route('/companywisejobs', methods = ['GET'])
@login_required_company
def companywisejobs():
	compid = session['comp_username']
	jcursor = mysql.connection.cursor()
	jresult = jcursor.execute("SELECT * FROM `jobs` WHERE `compid` = %s", [compid])
	jdata = list(jcursor.fetchall())
	jdata = [list(i) for i in jdata]
	md = datetime.now()
	for i in jdata:
		md = i[8].strftime("%Y-%m-%d")
		i.append(md)
		md = i[9].strftime("%Y-%m-%d")
		i.append(md)
	print(jdata)
	jcursor.close()

	return render_template('companywisejobs.html', data = jdata)

@app.route('/companywisejobseditable', methods = ['GET'])
@login_required_company
def getcwisejobdetailseditable():
	compid = 200000
	jcursor = mysql.connection.cursor()
	jresult = jcursor.execute("SELECT * FROM `jobs` WHERE `compid` = %s", [compid])
	jdata = list(jcursor.fetchall())
	jdata = [list(i) for i in jdata]
	md = datetime.now()
	for i in jdata:
		md = i[8].strftime("%Y-%m-%d")
		i.append(md)
		md = i[9].strftime("%Y-%m-%d")
		i.append(md)
	print(jdata)
	jcursor.close()

	return render_template('companywisejobs.html', scroll='jobtag', data = jdata)

@app.route('/updatejob',methods=['POST','GET'])
@login_required_company
def updatejob():
	
	if request.method == 'POST':
		
		jtitle = request.form['jtl']
		jagelimit = request.form['al']
		jsalary = request.form['sal']
		jvacancies = request.form['vac']
		jlocation = request.form['loc']
		jlastd = request.form['ld']
		jexperience = request.form['exp']
		jtype = request.form['jtype']
		jdescription = request.form['jd']
		jid = request.form['jid']
		cur = mysql.connection.cursor()
		sql = """ 
				UPDATE jobs SET jtitle=%s, jdescription=%s, jagelimit=%s, 
				jsalary=%s, jvacancies=%s, jlocation=%s, jlastd=%s, jtype=%s,
				jexperience=%s WHERE jid=%s
			"""
		d = (jtitle, jdescription, jagelimit, jsalary, jvacancies, jlocation, jlastd, jtype, jexperience, jid)
		cur.execute(sql, d)
		flash("Data Updated Successfully")
		mysql.connection.commit()
		cur.close()

	return redirect(url_for('getcwisejobdetailseditable'))

@app.route('/deletejob/<jid>', methods = ['GET'])
@login_required_company
def deletejob(jid):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM jobs WHERE jid=%s", (jid,))
	mysql.connection.commit()
	return redirect(url_for('getcwisejobdetailseditable'))



#***************************************End of Functions related to job*********************************#



#***************************************Start of Functions for appying for jobs*********************************#

@app.route('/apply/<compid>/<jid>')
@login_required_company
def apply(compid,jid):
	cur = mysql.connection.cursor()
	uname = session['username']
	status = "Applied"
	sql1 = """SELECT * FROM app_status WHERE jid = %s AND uname = %s AND compid = %s"""
	result = cur.execute(sql1,(jid, uname, compid))
	if(result > 0):
		flash("Already Applied chup kar ab","error")
		return redirect(url_for('joblist'))
	sql = """ INSERT INTO `app_status`(`jid`, `uname`, `compid`, `status`) VALUES (%s, %s, %s, %s)"""
	cur.execute(sql, (jid, uname, compid, status))
	mysql.connection.commit()
	return redirect(url_for('myapplications'))

@app.route('/myapplications')
@login_required
def myapplications():
	cur = mysql.connection.cursor()
	uname = session['username']
	sql1 = """SELECT * FROM app_status WHERE uname = %s"""
	result = cur.execute(sql1, [uname])
	adata = list(cur.fetchall())
	# adata = [list(i) for i in adata]
	data = []
	for i in adata:
		appid = i[0]
		jid = i[1]
		uname = i[2]
		compid = i[3]
		status = i[4]
		applied_on = i[5].strftime("%Y-%m-%d")
		print("hello world")
		print(appid,jid,uname,compid,status,applied_on)

		sql2 = """SELECT * FROM `jobs` WHERE `jid` = %s"""
		jresult = cur.execute(sql2,[jid])
		jdata = cur.fetchall()
		print("jresult = {}".format(jdata))
		jtitle = jdata[0][1]
		sql3 = """SELECT compname FROM company_register WHERE compid = %s"""
		compresult = cur.execute(sql3, [compid])
		compdata = cur.fetchall()
		print("compresult {}".format(compdata))
		compname = compdata[0][0]

		data.append([appid, jtitle, compname, applied_on, status])
	return render_template('myapplications.html', data=data)


@app.route('/deleteapplications/<aid>')
@login_required
def deleteapplications(aid):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM app_status WHERE appid=%s", (aid,))
	mysql.connection.commit()
	return redirect(url_for('myapplications'))

# @app.route('/applyjd/<compid>/<jid>')
# @login_required
# def applyjd(compid,jid):
# 	cur = mysql.connection.cursor()
# 	uname = session['username']
# 	status = "Applied"
# 	sql1 = """SELECT * FROM app_status WHERE jid = %s AND uname = %s AND compid = %s"""
# 	result = cur.execute(sql1,(jid, uname, compid))
# 	if(result > 0):
# 		flash("Already Applied chup kar ab","error")
# 		return redirect(url_for('jobdetails',job_id=jid))
# 	sql = """ INSERT INTO `app_status`(`jid`, `uname`, `compid`, `status`) VALUES (%s, %s, %s, %s)"""
# 	cur.execute(sql, (jid, uname, compid, status))
# 	mysql.connection.commit()
# 	return redirect(url_for('applicationstatus'))

@app.route('/candappstatus/<aid>')
@login_required
def candidateappstatus(aid):
	flash("Record Has Been Deleted Successfully")
	cur = mysql.connection.cursor()
	sql  = "SELECT * FROM app_status WHERE appid = %s"
	aresults = cur.execute(sql,[aid])
	adata = cur.fetchall()

	jid = adata[0][1]
	compid = adata[0][3]
	adate = adata[0][5].strftime("%Y-%m-%d")

	sql4 = "SELECT * FROM app_status WHERE jid = %s"
	ajresult = cur.execute(sql4, [jid])

	sql2 = "SELECT jtitle FROM jobs WHERE jid = %s"
	jresult = cur.execute(sql2, [jid])
	jdata = cur.fetchall()

	jtitle = jdata[0][0]

	sql3 = "SELECT compname FROM company_register WHERE compid = %s"
	cpmpresult = cur.execute(sql3, [compid])
	compdata = cur.fetchall()

	compname = compdata[0][0]

	return render_template('candappstatus.html', data = adata[0], jtitle = jtitle, compname = compname, adate = adate, noa = ajresult)


#---------------------------------------Application Status fro Companies---------------------------------------------#

@app.route('/companywisejobsapps')
@login_required_company
def companywisejobsapps():
	compid = session['comp_username']
	cur = mysql.connection.cursor()
	sql  = "SELECT * FROM app_status WHERE compid = %s"
	aresults = cur.execute(sql,[compid])
	adata = cur.fetchall()

	data= []

	for i in adata:

		uname = i[2]
		jid = i[1]

		sql2 = "SELECT jtitle, jvacancies FROM jobs WHERE jid = %s"
		jresult = cur.execute(sql2,[jid])
		jdata = cur.fetchall()
		jtitle = jdata[0][0]
		jvacancies = jdata[0][1]

		sql3 = "SELECT fname, mname, lname FROM register WHERE uname = %s"
		uresult = cur.execute(sql3,[uname])
		udata = cur.fetchall()
		fname = udata[0][0]
		mname = udata[0][1]
		lname = udata[0][2]

		sql4 = "SELECT * FROM app_status WHERE jid = %s"
		ajresult = cur.execute(sql4,[jid])
		noa = ajresult

		data.append([i, jtitle, fname, mname, lname, jvacancies, ajresult])

	return render_template('companywisejobsapps.html', data= data)



@app.route('/compappstatus/<aid>')
@login_required_company
def companyappstatus(aid):
	
	cur = mysql.connection.cursor()
	sql  = "SELECT * FROM app_status WHERE appid = %s"
	aresults = cur.execute(sql,[aid])
	adata = cur.fetchall()

	jid = adata[0][1]
	uid = adata[0][2]
	adate = adata[0][5].strftime("%Y-%m-%d")

	sql4 = "SELECT * FROM app_status WHERE jid = %s"
	ajresult = cur.execute(sql4, [jid])

	sql2 = "SELECT jtitle, jvacancies FROM jobs WHERE jid = %s"
	jresult = cur.execute(sql2, [jid])
	jdata = cur.fetchall()

	jtitle = jdata[0][0]
	jvacancies = jdata[0][1]

	sql3 = "SELECT fname, mname, lname FROM register WHERE uname = %s"
	uresult = cur.execute(sql3, [uid])
	udata = cur.fetchall()

	uname = udata[0][0] + " " + udata[0][1] + " " + udata[0][2]

	return render_template('compappstatus.html', data = adata[0], jtitle = jtitle, uname = uname, adate = adate, noa = ajresult, jvacancies = jvacancies)

@app.route('/applicationstatus')
def applicationstatus():
	return render_template('applicationstatus.html')


#******************************Application Event Functions************************************#

@app.route('/testpage/<aid>')
@login_required
def testpage(aid):
	return render_template('testpage.html', aid = aid)

@app.route('/completetest', methods=['POST','GET'])
def completetest():
	if request.method == 'POST':
		
		marks = request.form['marks']
		aid = request.form['aid']
		status = "Test Completed"

		cur = mysql.connection.cursor()
		sql = "UPDATE app_status SET status = %s, test_score = %s WHERE appid = %s"
		cur.execute(sql, (status, marks, aid))
		mysql.connection.commit()
		cur.close()

	return redirect(url_for('myapplications'))

@app.route('/setinterview', methods=['POST','GET'])
@login_required_company
def setinterview():
	if request.method == 'POST':

		status = "Interview Scheduled"
		date = request.form['ed']
		time = request.form['et']
		aid = request.form['aid']


		cur = mysql.connection.cursor()
		sql1 = """ SELECT * from register r, app_status a WHERE r.uname = a.uname AND a.appid = %s """
		result = cur.execute(sql1, (aid))
		if result>0:
			lst = cur.fetchone()
			print(lst)
			email = lst[5]
			fname=lst[1]
			mysql.connection.commit()
			cur.close()


		date1 = str(date)
		date2 = date1.split("-")
		year = int(date2[0])
		month = int(date2[1])
		day= int(date2[2])
		time1 = str(time)
		time2 = time1.split(':')
		hour = int(time2[0])
		minute = int(time2[1])

		credentials = pickle.load(open("token.pkl", "rb"))
		service = build("calendar", "v3", credentials=credentials)
		start_time = datetime(year, month, day, hour, minute, 0)
		end_time = start_time + timedelta(hours=4)
		timezone = 'Asia/Kolkata'

		event = {
		  'summary': 'Interview',
		  'location': 'Google Meet',
		  'description': 'company details',
		  'start': {
		    'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
		    'timeZone': timezone,
		  },
		  'end': {
		    'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
		    'timeZone': timezone,
		  },
		    
		  'reminders': {
		    'useDefault': False,
		    'overrides': [
		      {'method': 'email', 'minutes': 24 * 60},
		      {'method': 'popup', 'minutes': 10},
		    ],
		  },
		    'attendees':[
		    {'email': email },
		  ]
		    ,
		  'conferenceData': {
		      'createRequest': {
		          'requestId':'its done baby',
		          'conferenceSolutionKey': {
		                  'type': 'hangoutsMeet'
		              }
		          
		      }
		  },
		    'reminders': {
		        'useDefault': False,
		        'overrides': [
		          {'method': 'email', 'minutes': 5},
		        ],
		      },
		}

		a = service.events().insert(calendarId='maheshmahajan.20998@gmail.com', body=event, conferenceDataVersion=1).execute()
		link = a['hangoutLink']



		datetime1 = str(date)+" "+str(time)+":00"
		sql = """UPDATE `app_status` SET `status` = %s, `iei` = 1, `interview_link` = %s,`idate` = %s WHERE `appid` = %s;"""
		cur = mysql.connection.cursor()
		cur.execute(sql, (status, link, datetime1, aid))
		mysql.connection.commit()
		cur.close()
		print("Time:"+str(date)+str(time)+":00")
		print(date, time, aid)
		msg = Message('Interview link and schedule.', sender='code.crunch.sih@gmail.com', recipients=[email])
		msg.html = '<h1>Hello {},<h1><br> <h5>Your Interview is scheduled on <b>{}</b> at <b>{}</b> and the link for the interview is <a href="{}">{}</a></h5>'.format(fname,date,time,link,link)
		mail.send(msg)



		return redirect(url_for('companywisejobsapps'))


@app.route('/allowtest/<aid>')
@login_required_company
def allowtest(aid):


	status = "Test Pending"
	iet = "1"
	test_link = "/takethetest/"+aid

	cur = mysql.connection.cursor()
	sql = "UPDATE app_status SET status = %s, iet = %s, test_link = %s WHERE appid = %s"

	cur.execute(sql, (status, iet, test_link, aid))
	mysql.connection.commit()
	cur.close()

	return redirect(url_for('companywisejobsapps'))


@app.route('/acceptapp/<aid>')
@login_required_company
def acceptapp(aid):
	sql = "UPDATE app_status SET status = 'Accepted' WHERE appid = %s"
	cur = mysql.connection.cursor()
	cur.execute(sql, [aid])
	mysql.connection.commit()
	cur.close()

	return redirect(url_for('companywisejobsapps'))

@app.route('/rejectapp/<aid>')
@login_required_company
def rejectapp(aid):
	sql = "UPDATE app_status SET status = 'Rejected' WHERE appid = %s"
	cur = mysql.connection.cursor()
	cur.execute(sql, [aid])
	mysql.connection.commit()
	cur.close()

	return redirect(url_for('companywisejobsapps'))

if __name__ == '__main__':
	app.secret_key =  'mahesh'
	app.run(debug=True)
