import datetime

from flask import Flask, render_template, request, url_for
from deliverai_utils import Person, Ticket, Bot
from server import DeliverAIServer

app = Flask(__name__)
with app.app_context():
    # users
    people = Person.from_file("people.txt")
    people_map = {person.username: person for person in people}
    user = people_map.pop("ash.ketchum", None)

    # robots
    bots = Bot.from_file("bots.txt")

    tickets = []

    deliver_server = DeliverAIServer()


@app.route('/')
def index():
    return render_template(
        'index.html',
        title="Secure Office Delivery",
    )


@app.route('/admin/')
def admin_page():
    return render_template(
        'admin.html',
        bots=bots
    )


@app.route('/send/')
def send():
    return render_template(
        'recipients.html',
        recipients=people_map.values(),
    )


@app.route('/send/<string:username>', methods=['GET', 'POST'])
def schedule_pickup(username):
    if request.method == 'GET':

        if username == user.username:
            return error_page(
                error='',
                icon="far fa-check-circle",
                line1="Hey",
                line2="looks like you've found yourself!",
                button_text="View inbox",
                button_href=url_for('send')
            )

        if username not in people_map:
            return error_page(
                error='',
                icon="fas fa-robot",
                line1="Oops...",
                line2="it looks like that person doesn't exist!",
            )
        else:
            recipient = people_map[username]    
            return render_template(
                'schedule_pickup.html',
                recipient=recipient,
            )
    else:
        return process_delivery(recipient)


def validate_delivery(form):
    assert request.method == 'POST'
    # do some validation here as well

    return [k for (k, v) in form.items() if not v]

    # if not all(form.values()):
    #     # some parameters not filled correctly
    #     return "{}".format([k for (k, v) in form.items() if not v])
    # return True


def create_ticket(form):
    return Ticket(
        form['pickup-time'],
        user,
        people_map[form['recipient-username']],
        form['delivery-message'],
    )


def send_delivery(ticket):
    # orig = ticket.sender.coordinates
    orig = (1, 1)
    dest = ticket.recipient.coordinates

    # print("sending bot for pickup @ {} \n"
    #       "  |--> to deliver @ {} !".format(orig, dest))

    deliver_server.send_pickup(orig, dest)


def process_delivery(recipient):
    form = {
        arg: request.form.get(arg) for arg in
        [
            'pickup-time',
            'recipient-username',
            'delivery-message',
            # 'hello',
        ]
    }
    # exit if invalid
    bad_fields = validate_delivery(form)
    if bad_fields:
        return "invalid input: {}".format(bad_fields)

    # if request.form.get('urgent'):
    #     # treat request as urgent?
    #     pass
    # if request.form.get('pickup-now'):
    #     # summon bot directly
    #     pass

    # create a record of submission
    ticket = create_ticket(form)
    tickets.append(ticket)
    # TODO make delivery not instant, go to queue
    send_delivery(ticket)

    return render_template(
        'schedule_pickup_confirm.html',
        recipient=ticket.recipient,
        ticket=ticket,
    )
    # return "{}".format(ticket)
    # return "{}".format(request.form)


@app.route('/receive/')
def receive():
    return render_template(
        'receive.html',
        # username=username,
        # offices=offices,
    )


@app.route('/history/')
def history():
    return render_template(
        'history.html',
        # username=username,
        # offices=offices,
    )


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO authenticate the user
        pass
    return "this is a login screen"


@app.route('/tickets/')
def show_tickets():
    return render_template(
        'tickets.html',
        tickets=tickets
    )


@app.route('/debug/')
def debug_mode():
    return render_template(
        'debug.html',
    )


@app.route('/cmd/<string:command>', methods=['GET', 'POST'])
def send_cmd(command):
    deliver_server.send_encoded_message(command)
    return "sending command: '{}'".format(command)


@app.errorhandler(404)
def error_page(
        error,
        icon='far fa-question-circle',
        line1="Whoa!",
        line2="<em>This is not the page you're looking for</em>",
        button_href='/',
        button_text='Go back'):
    return render_template(
        'error.html',
        error=error,
        icon=icon,
        line1=line1,
        line2=line2,
        button_href=button_href,
        button_text=button_text,
    )


@app.context_processor
def inject_template_globals():
    return {
        # an html-friendly time construct to force CSS refresh
        'now': datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S"),
        'dt': datetime,
        'user': user,
    }


if __name__ == '__main__':
    app.run()
