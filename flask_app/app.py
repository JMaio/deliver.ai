import datetime

from flask import Flask, render_template, request
from deliverai_utils import Person, Ticket

app = Flask(__name__)
people = Person.from_file("people.txt")
people_map = {person.username: person for person in people}
user = people_map.pop("ash.ketchum", None)


@app.route('/')
def index():
    return render_template(
        'index.html',
        title="Secure Office Delivery",
    )


@app.route('/deliver/')
def recipients_index():
    return render_template(
        'recipients.html',
        recipients=people_map.values(),
    )


@app.route('/deliver/<string:username>', methods=['GET', 'POST'])
def schedule_delivery(username):
    recipient = people_map[username]
    if request.method == 'GET':
        if username == user.username:
            return error_page(
                icon="far fa-check-circle",
                line1="Hey",
                line2="looks like you've found yourself!",
                button_text="View inbox",
                button_href='/receive/'
            )
        if username not in people_map:
            return error_page(
                icon="fas fa-robot",
                line1="Oops...",
                line2="it looks like that person doesn't exist!",
            )
        return render_template(
            'schedule_delivery.html',
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
    origin = ticket.sender.coordinates
    destination = ticket.recipient.coordinates
    # send the command to the robot
    pass


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
    # TODO make delivery not instant, go to queue
    send_delivery(ticket)

    return render_template(
        'schedule_delivery_confirm.html',
        recipient=ticket.recipient,
        ticket=ticket,
    )
    return "{}".format(ticket)
    # return "{}".format(request.form)


@app.route('/receive/')
def receive():
    return render_template(
        'base.html',
        # username=username,
        # offices=offices,
    )


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO authenticate the user
        pass
    return "this is a login screen"


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
