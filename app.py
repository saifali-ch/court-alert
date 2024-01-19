import secrets

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from db import get_criteria, update_criteria_in_db, update_criteria_status, delete_criteria_from_db, \
    add_criteria_to_db

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    criteria = get_criteria()
    return render_template('index.html', criteria=criteria)


@app.route('/add_criteria', methods=['POST'])
def add_criteria():
    # Extract criteria from the form
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    duration = request.form['duration']
    active = request.form.get('active', 0)  # default to 0 if not provided

    add_criteria_to_db(date, start_time, end_time, duration, active)
    flash('Criteria added successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/update_criteria', methods=['POST'])
def update_criteria():
    # Extract criteria from the form
    criteria_id = request.form['criteria_id']
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    duration = request.form['duration']
    active = request.form.get('active', 0)  # default to 0 if not provided

    update_criteria_in_db(criteria_id, date, start_time, end_time, duration, active)
    flash('Criteria updated successfully!', 'primary')
    return redirect(url_for('index'))


@app.route('/enable_criteria/<int:criteria_id>')
def enable_criteria(criteria_id):
    update_criteria_status(criteria_id, active=1)
    return jsonify({'message': 'Criteria enabled successfully!'})


@app.route('/disable_criteria/<int:criteria_id>')
def disable_criteria(criteria_id):
    update_criteria_status(criteria_id, active=0)
    return jsonify({'message': 'Criteria disabled successfully!'})


@app.route('/delete_criteria/<criteria_id>')
def delete_criteria(criteria_id):
    delete_criteria_from_db(criteria_id)
    flash('Criteria deleted successfully!', 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
