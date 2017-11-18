import os
import pandas as pd
import math
from flask import Flask, render_template, request, \
    redirect, url_for, flash
from flask_mail import Mail, Message
from werkzeug import secure_filename

# config parameters

WTF_CSRF_ENABLED = True
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_STATIC = os.path.join(APP_ROOT, 'static')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/home/klac7050/mysite/uploads"
app.secret_key = os.getenv('SECRET_KEY')

app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['MAIL_USERNAME'] = 'resultsklac@gmail.com'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/racehq2slam', methods=['GET','POST'])
def racehq2slam_pro():

    if request.method == 'POST':

        if 'file' not in request.files:
            flash('No file part in form submission!')
            return redirect(request.url)

        f = request.files['file']

        if f.filename == '':
            flash('Invalid filename!')
            return redirect(request.url)

        input_file = os.path.join(app.config['UPLOAD_FOLDER'],
                            secure_filename(f.filename))

        f.save(input_file)

        attach_file = request.form['outputfile']

        process_img(input_file, attach_file)

        # email to specified address ?
        if request.form.get('toemail') == '1':
            msg = Message('KLAC results from racehq2slam.',
            sender = 'resultsklac@gmail.com',
            recipients = [request.form['eaddress']])
            msg.body = "Your data is ready for collection from "
            msg.html = "<p>Your processed .xls data is ready for collection from</p> <a href='klac7050.pythonanywhere.com%s'><strong>here</strong></a>""" % url_for('static', filename=attach_file)
            mail.send(msg)

        return render_template("downloads.html", dfile=attach_file,
        downfile = url_for('static',filename=attach_file))


    else:

        return render_template("racehq2slam.html")


# Function for converting h:m:s.ss times to seconds
# and rounding-up to nearest tenth second.

def time_convert(x):
    h,m,s = map(float,x.split(':'))
    return (h*60.0+m)*60.0 + math.ceil(s*10.0)/10.0


def process_img(input_file, output_file):

    df = pd.read_csv(input_file, header=None)

    # Expunge all rows with null in first (zeroth) column;
    # determine the number of remaining rows and reset row
    # indexing to run from 0 to n.
    clean_r1 = df.dropna(subset = [0]).iloc[:,0:11]

    no_of_valid_rows = len(clean_r1.index)
    clean_r1.index = range(no_of_valid_rows)

    # Gated (1) or non-gated (0) as determined from second line of input file

    gated = 1
    marker = 'TSGR'

    if 'N' in clean_r1.ix[1][1]:
        gated = 0
        marker = 'TSNGR'

    # Find the row indices associated with each distinct event.

    event_indices = clean_r1[clean_r1[0] == 'Age'].index

    # Loop over the individual events, extracting salient information
    # and writing it into a python list structure.

    print (event_indices)
    events_data_cleaning = []
    #
    #
    for event_index in event_indices:
        event_name =  clean_r1.ix[event_index][5]
        for idx in range(event_index + 3, no_of_valid_rows):
            if str(clean_r1.ix[idx][0]) == marker:
               break
            else:
               if gated  == 1:
                  events_data_cleaning.append(
                     {'RegNo': clean_r1.ix[idx][3],
                     'Preferred Name': clean_r1.ix[idx][5].title(),
                     'AgeID': clean_r1.ix[idx][6],
                     'GenderID': clean_r1.ix[idx][7],
                     'EventTitle': event_name,
                     'Performance': clean_r1.ix[idx][1],
                     'Competed': 0,
                     'Placing': clean_r1.ix[idx][2],
                     'Centre': clean_r1.ix[idx][10]})
               else:
                  events_data_cleaning.append(
                     {'RegNo': clean_r1.ix[idx][2],
                     'Preferred Name': clean_r1.ix[idx][5].title(),
                     'AgeID': clean_r1.ix[idx][6],
                     'GenderID': clean_r1.ix[idx][7],
                     'EventTitle': event_name,
                     'Performance': clean_r1.ix[idx][1],
                     'Competed': 0,
                     'Placing': clean_r1.ix[idx][0],
                     'Centre': clean_r1.ix[idx][10]})

    # convert the list into a pandas dataframe so it can be manipulated
    # more easily.

    events_cleaned_data = pd.DataFrame(events_data_cleaning)

    # fix ordering of columns to keep SLAM happy.

    events_cleaned_data = events_cleaned_data[['RegNo',
                                           'Preferred Name',
                                           'AgeID',
                                           'GenderID',
                                           'EventTitle',
                                           'Performance',
                                           'Competed',
                                           'Placing',
                                           'Centre']]

    # modify the format of the performances: h:m:s.ss -> s.s

    events_cleaned_data['Performance'] = \
                    events_cleaned_data.Performance.apply(time_convert)

    # replace event names with SLAM's preferred designations

    events_cleaned_data.replace(['70m', '100m', '150m',
                             '200m', '400m', '800m',
                             '1500m', '700m Walks',
                             '1100m Walks', '1500m Walks',
                             '60m Hurdles', '80m Hurdles',
                             '90m Hurdles', '100m Hurdles',
                             '200m Hurdles', '300m Hurdles'],
                            ['70 Metres', '100 Metres',
                             '150 Metres', '200 Metres',
                             '400 Metres', '800 Metres',
                             '1500 Metres', '700m Walk',
                             '1100m Walk', '1500m Walk',
                             '60m Hurdles', '80m Hurdles',
                             '90m Hurdles', '100m Hurdles',
                             '200m Hurdles', '300m Hurdles'],
                             inplace=True)

    # dump data in Excel .xls spreadsheet format

    events_cleaned_data.to_excel(os.path.join(APP_STATIC,
    output_file), sheet_name='Sheet1', index=False)

    return


if __name__ == "__main__":
    app.run(debug=True)
