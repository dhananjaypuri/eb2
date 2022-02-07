from urllib.parse import uses_fragment
from flask import Flask, redirect , render_template, request , sessions
from flask_sqlalchemy import SQLAlchemy
import datetime
import pytz
import smtplib
import csv
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import os

application = Flask(__name__);

application.secret_key = "nssjhsjhsjsh";
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db';
location = 'userdatafiles/';
application.config['UPLOAD_FOLDER'] = location;

db = SQLAlchemy(application);


eid = "dhananjay.singer.puri@gmail.com";
password = "lrrgaafmduiifylv";

def send_mail(mess_to , body):
    msg = EmailMessage();

    msg['To'] = mess_to;
    msg['Subject'] = "Fill Survey"
    msg['From'] = eid;
    msg.set_content(body);

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(eid, password);
        smtp.send_message(msg);

class User(db.Model):
    id = db.Column(db.Integer, primary_key= True);
    uname = db.Column(db.String(200) , nullable=False);
    email = db.Column(db.String(200) , nullable=False);
    score = db.relationship('Scores');

class Scores(db.Model):
    id = db.Column(db.Integer, primary_key= True);
    srvops = db.Column(db.Integer, nullable = True);
    slmr = db.Column(db.Integer, nullable = True);
    techcap = db.Column(db.Integer, nullable = True);
    gc = db.Column(db.Integer, nullable = True);
    si = db.Column(db.Integer, nullable = True);
    overallrate = db.Column(db.Integer, nullable = True);
    datesent = db.Column(db.DateTime, default=datetime.datetime.now(tz=pytz.timezone('Asia/Kolkata')));
    daterec = db.Column(db.DateTime);
    replied = db.Column(db.Boolean, nullable = False, default = False);
    remarks = db.Column(db.Text , nullable=True);
    uid = db.Column(db.Integer, db.ForeignKey('user.id'));

@application.route('/', methods=['GET', 'POST'])
def home():
    
    return "This is home";

@application.route('/sendmail', methods=['GET', 'POST'])
def sendmail():

    user = User.query.all();
    emailList = [];
    for item in user:
        emailList.append(item.email);
    
    currentMonth = datetime.datetime.now().month;
    currentYear = datetime.datetime.now().year;
    sentDate = datetime.datetime(currentYear,currentMonth,1).date();
    print(sentDate);
    for email in emailList:
        user = User.query.filter_by(email=email).first();
        check_score = Scores.query.filter_by(uid=user.id).all();
        if(check_score):
            for score in check_score:
                date_from_score = score.datesent.date();
                # print(date_from_score);
                if(date_from_score == sentDate):
                    print("Do not send email");
                else:
                    print("Send Email");
                    user_score = Scores(uid=user.id, datesent=datetime.datetime(currentYear,currentMonth,1));
                    db.session.add(user_score);
                    db.session.commit();
                    
                    todayDate = datetime.datetime(currentYear,currentMonth,1);
                    user2 = User.query.filter_by(email=email).first();
                    score2 = Scores.query.filter_by(uid=user2.id, datesent=todayDate).first();
                    body = f'''Hi {user.uname}, \n\nRequest you to please fill the below survey.\n\n Link : http://127.0.0.1:8000/survey?uname={user.uname}&id={score2.id} \n\nRegards\nDhananjay Puri''';
                    print(body);
                    send_mail(email, body);
        else:
            print("No Data");
            print("Send Email");
            user_score = Scores(uid=user.id, datesent=datetime.datetime(currentYear,currentMonth,1));
            db.session.add(user_score);
            db.session.commit();
                    
            todayDate = datetime.datetime(currentYear,currentMonth,1);
            user2 = User.query.filter_by(email=email).first();
            score2 = Scores.query.filter_by(uid=user2.id, datesent=todayDate).first();
            body = f'''Hi {user.uname}, \n\nRequest you to please fill the below survey.\n\n Link : http://127.0.0.1:8000/survey?uname={user.uname}&id={score2.id} \n\nRegards\nDhananjay Puri''';
            print(body);
            send_mail(email, body);

    return "hi";

@application.route('/sendmail2/<dt>', methods=['GET', 'POST'])
def sendmail2(dt):
    dtList = str(dt).split('-');
    newdate = datetime.datetime(int(dtList[0]),int(dtList[1]),1);
    scores = Scores.query.filter_by(datesent=newdate, replied = False).all();
    emailList = [];

    print(scores);

    for score in scores:
        uid = score.uid;
        user = User.query.filter_by(id=uid).first();
        uname = user.uname;
        body = body = f'''Hi {user.uname}, \n\nRequest you to please fill the below survey.\n\n Link : http://127.0.0.1:8000/survey?uname={uname}&id={score.id} \n\nRegards\nDhananjay Puri''';
        print(body);
        email = user.email;
        send_mail(email, body);
    
    return "This is sendmail 2";


@application.route('/upload', methods=['GET', 'POST'])
def upload():

    if(request.method == 'POST'):
        print("Hello");
        f = request.files['file1']
        fname = f.filename;
        allowedExt = ['csv', 'txt'];

        ext = fname.split('.')[-1];
        if(ext in allowedExt):
            result = f.save(os.path.join(application.config['UPLOAD_FOLDER'], secure_filename(fname)));
            if(result == None):
                print("File Saved Successfully ");
                users = User.query.all();
                emailList = [];
                
                for user in users:
                    emailList.append(user.email);
                print(emailList);
                with open(f'userdatafiles/{fname}', 'r') as readfile:
                    data = csv.reader(readfile);
                    next(data);
                    for item in data:
                        if(item[1] not in emailList):
                            udata = User(uname=item[0], email=item[1]);
                            db.session.add(udata);
                            db.session.commit();
                            print(f"Added {item[1]}");
                        else:
                            continue;

                return redirect('/upload');
        else:
            print("Extention Not allowed");
            return redirect('/upload');
    return render_template('upload.html');

@application.route('/survey', methods=['GET', 'POST'])
def fill_survey():

    if(request.method == 'POST'):
        try:
            srvops = request.form.get('srvops', default=0, type=int);
            slmr = request.form.get('slmr', default=0, type=int);
            techcap = request.form.get('techcap', default=0, type=int);
            gc = request.form.get('gc', default=0, type=int);
            si = request.form.get('si', default=0, type=int);
            overallrate = request.form.get('overallrate', default=0, type=int);
            remarks = request.form.get('remarks');
            daterec = datetime.datetime.now(tz=pytz.timezone('Asia/Kolkata'));

            id = int(request.form.get('id'));

            score = Scores.query.filter_by(id=id).first();
            score.srvops = int(srvops);
            score.slmr = int(slmr);
            score.techcap = int(techcap);
            score.gc = int(gc);
            score.si = int(si);
            score.overallrate = int(overallrate);
            score.remarks = remarks;
            score.replied = True;
            score.daterec = daterec;

            db.session.add(score);
            db.session.commit();
            return redirect('/');

        except Exception as e:
            print(e);

    id = request.args.get('id', default=None, type=int);
    uname = request.args.get('uname', default=None, type=str);
    user = User.query.filter_by(uname=uname).first();
    score = Scores.query.filter_by(id=id).first();
    if(score.replied == False):
        return render_template('survey.html', score=score);

    else:
        return "You have already filled the survey!!!!!!";

if(__name__ == '__main__'):
    application.run(debug=True, port=8000);