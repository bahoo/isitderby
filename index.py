from flask import Flask, jsonify, make_response, render_template, request
from math import ceil
from datetime import datetime, timedelta
import pytz


app = Flask(__name__)

EASTERN = pytz.timezone("US/Eastern")


def request_wants_json():
    best_match = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best_match == 'application/json' and \
        request.accept_mimetypes[best_match] > request.accept_mimetypes['text/html']:
        return True
    return False


def is_derby(date=None):
    
    if date is None:
        date = EASTERN.localize(datetime.today())

    first_day = date.replace(day=1)

    if first_day.weekday() == 6:
        adjusted_dom = (1 + first_day.weekday()) / 7
    else:
        adjusted_dom = date.day + first_day.weekday()

    week_of_month = int(ceil(adjusted_dom/7.0))

    return '%s/%s/%s' % (date.month, week_of_month, date.weekday()) == '5/1/5'


def calculate_derby_by_year(year):
    first_day_of_may = EASTERN.localize(datetime(year=year, month=5, day=1, hour=0, minute=0, second=0, microsecond=0))

    # todo: this is buggy.
    day = (6-first_day_of_may.weekday())
    if day == 0:
        day = 1

    return first_day_of_may.replace(day=day, hour=18, minute=30)


def get_next_derby():
    midnight = EASTERN.localize(datetime.today()).replace(hour=0, minute=0, second=0, microsecond=0)
    
    derby = calculate_derby_by_year(midnight.year)

    if derby < midnight + timedelta(days=1):
        derby = calculate_derby_by_year(midnight.year + 1)

    return derby



@app.route('/')
def index():

    is_it_derby = is_derby()
    midnight = EASTERN.localize(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))
    next_derby = get_next_derby()

    context = {
        'is_it_derby': is_it_derby,
        'next_derby_number': next_derby.year - 1874,
        'next_derby_date': next_derby,
        'days_til_next_derby': (next_derby - midnight).days
    }

    if request_wants_json():
        context['next_derby_date'] = next_derby.isoformat()
        return jsonify(**context)

    return render_template('index.html', **context)


@app.route('/feed')
def feed():

    is_it_derby = is_derby()
    midnight = EASTERN.localize(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))

    description = "No." if not is_it_derby else "YES, FRIENDS! YES! IT'S THE DERBY! IT'S THE GODDAMN KENTUCKY DERBY, GO AND TELL THE NEWS!"

    content = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Is It Derby?</title>
        <link>http://www.isitderby.com/feed</link>
        <atom:link href="http://www.isitderby.com/feed" rel="self" type="application/rss+xml" />
        <description>Well, is it?</description>
        <language>en-us</language>
        <item>
            <title>Is It Derby?</title>
            <description>%(description)s</description>
            <link>http://www.isitderby.com/?%(midnight_isoformat)s</link>
            <pubDate>%(midnight_utc_string)s</pubDate>
            <guid>http://www.isitderby.com/?%(midnight_isoformat)s</guid>
        </item>
    </channel>
</rss>""" % {
        'description': description,
        'midnight_isoformat': midnight.isoformat(),
        'midnight_utc_string': midnight.strftime("%a, %d %b %Y %H:%M:%S %z")
    }

    return make_response(content, {'Content-Type': "application/rss+xml"})


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')