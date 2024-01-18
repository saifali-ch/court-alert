from flask import Flask, render_template, request, redirect, url_for

from db import get_criteria_from_db, update_criteria_in_db

app = Flask(__name__)


@app.route('/')
def index():
    criteria = get_criteria_from_db()
    return render_template('index.html', criteria=criteria)


@app.route('/update_criteria', methods=['POST'])
def update_criteria():
    # Extract criteria from the form
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    duration = request.form['duration']

    update_criteria_in_db(date, start_time, end_time, duration)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
    # app.run(debug=True)
