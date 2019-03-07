import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    current_app, abort)
from werkzeug.security import check_password_hash, generate_password_hash

from deliver_ai import Ticket
import deliver_ai.deliverai_utils as util
from deliver_ai.server import get_server

bp = Blueprint('send', __name__, url_prefix='/send')


@bp.route('/')
def send():
    return render_template(
        'send/recipients.html',
        recipients=util.people_map.values(),
    )


@bp.route('/send/<string:username>', methods=['GET', 'POST'])
def schedule_pickup(username):
    try:
        recipient = util.people_map[username]
    except KeyError:
        return abort(
            404,
            error='',
            icon="fas fa-robot",
            line1="Oops...",
            line2="it looks like that person doesn't exist!",
        )

    if request.method == 'GET':
        if username == util.user.username:
            return abort(
                404,
                error='',
                icon="far fa-check-circle",
                line1="Hey",
                line2="looks like you've found yourself!",
                button_text="View inbox",
                button_href=url_for('send')
            )
        else:
            return render_template(
                'send/schedule_pickup.html',
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
        g.user,
        g.people_map[form['recipient-username']],
        form['delivery-message'],
    )


def send_delivery(ticket):
    # orig = ticket.sender.coordinates
    orig = (1, 1)
    dest = ticket.recipient.coordinates

    # print("sending bot for pickup @ {} \n"
    #       "  |--> to deliver @ {} !".format(orig, dest))

    g.tcp_server.send_pickup(orig, dest)


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
    util.tickets.append(ticket)
    # TODO make delivery not instant, go to queue
    send_delivery(ticket)

    return render_template(
        'send/schedule_pickup_confirm.html',
        recipient=ticket.recipient,
        ticket=ticket,
    )
    # return "{}".format(ticket)
    # return "{}".format(request.form)
