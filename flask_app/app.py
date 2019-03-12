import datetime

from flask import Flask, render_template, request, url_for, \
    render_template_string, abort
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, current_user

from deliverai_utils import Person, Ticket, Bot, Map, TicketRegister
from server import DeliverAIServer


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'dev'

    # Flask-SQLAlchemy settings
    # File-based SQL database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///deliver_ai.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    # Shown in and email templates and page footers
    USER_APP_NAME = "deliver.ai"
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = False  # Simplify register form


def create_app():
    """ Flask application factory """
    app = Flask(__name__)

    app.config.from_object(__name__ + '.ConfigClass')

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False,
                           server_default='1')

        # User authentication information. The collation='NOCASE' is required
        #  to search case insensitively when USER_IFIND_MODE is
        # 'nocase_collation'.
        username = db.Column(db.String(100, collation='NOCASE'),
                             nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        email_confirmed_at = db.Column(db.DateTime())

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'),
                               nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'),
                              nullable=False, server_default='')

    # Create all database tables
    db.create_all()

    # Setup Flask-User and specify the User data-model
    class UserManagerNoValidation(UserManager):
        def password_validator(self, form, field):
            return

    user_manager = UserManagerNoValidation(app, db, User)  # noqa

    # with app.app_context():
    # users
    people = Person.from_file("map_1.txt")
    people_map = {person.username: person for person in people}
    # user = people_map.pop("ash.ketchum", None)
    print("reading office map")
    office_map = Map(people_map)

    def get_current_user_as_person():
        if current_user.is_authenticated:
            return office_map.get(current_user.username)
        else:
            return None

    # robots
    bots = Bot.from_file("bots.txt")

    tickets = TicketRegister()

    tcp_server = DeliverAIServer()

    debug_log = tcp_server.log

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
            bots=bots,
        )

    @app.route('/send/')
    def send():
        user = get_current_user_as_person()
        if not user:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="Nothing here!",
                line2="Please sign in or register to start sending.",
                button_text="Home page",
                button_href=url_for('index'),
            )
        r = office_map.get_without_me(user)
        return render_template(
            'send/index.html',
            recipients=r,
        )

    @app.route('/send/<string:username>', methods=['GET', 'POST'])
    @login_required
    def schedule_pickup(username):
        try:
            sender = get_current_user_as_person()
            recipient = office_map.get(username)
        except KeyError:
            return error_page(
                error='',
                icon="fas fa-robot",
                line1="Oops...",
                line2="it looks like that person doesn't exist!",
            )
        if request.method == 'GET':
            if username == current_user.username:
                return error_page(
                    error='',
                    icon="far fa-check-circle",
                    line1="Hey",
                    line2="looks like you've found yourself!",
                    button_text="View inbox",
                    button_href=url_for('receive')
                )
            else:
                return render_template(
                    'send/schedule_pickup.html',
                    sender=sender,
                    recipient=recipient,
                )
        elif request.method == 'POST':
            return process_delivery(sender, recipient)

    def validate_delivery(form):
        assert request.method == 'POST'
        # do some validation here as well

        return [k for (k, v) in form.items() if not v]

        # if not all(form.values()):
        #     # some parameters not filled correctly
        #     return "{}".format([k for (k, v) in form.items() if not v])
        # return True

    def create_ticket(sender, recipient, form):
        return Ticket(
            form['pickup-time'],
            sender,
            recipient,
            form['delivery-message'],
        )

    def send_delivery(ticket):
        # orig = ticket.sender.coordinates
        orig = ticket.sender.coordinates
        dest = ticket.recipient.coordinates

        # print("sending bot for pickup @ {} \n"
        #       "  |--> to deliver @ {} !".format(orig, dest))
        lion = bots.get('lion', None)
        lion.props['dest'] = dest
        lion.props['route'] = "{} --> {} --> {}".format(
            (lion.props['x_loc'], lion.props['y_loc']), orig, dest)
        tcp_server.send_pickup(orig, dest)

    def process_delivery(sender, recipient):
        form = {
            arg: request.form.get(arg) for arg in
            [
                'pickup-time',
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
        ticket = create_ticket(sender, recipient, form)
        tickets.new_ticket(ticket)
        # TODO make delivery not instant, go to queue
        send_delivery(ticket)

        return render_template(
            'send/schedule_pickup_confirm.html',
            sender=ticket.sender,
            recipient=ticket.recipient,
            ticket=ticket,
        )
        # return "{}".format(ticket)
        # return "{}".format(request.form)

    @app.route('/receive/')
    def receive():
        user = get_current_user_as_person()
        if not user:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="Nothing here!",
                line2="Please sign in or register to view your deliveries.",
                button_text="Home page",
                button_href=url_for('index'),
            )
        return render_template(
            'receive.html',
            pending_tickets=tickets.get_received(user)
            # offices=offices,
        )

    @app.route('/history/')
    def history():
        user = get_current_user_as_person()
        if not user:
            return error_page(
                error='',
                icon="fas fa-ticket-alt",
                line1="Nothing here!",
                line2="Please sign in or register to view your tickets.",
                button_text="Home page",
                button_href=url_for('index')
            )
        sent, received = tickets.get_sent(user), tickets.get_received(user)
        if not sent and not received:
            return error_page(
                error='',
                icon="fas fa-ticket-alt",
                line1="No tickets yet!",
                line2="Your tickets will appear here.",
                button_text="Send something!",
                button_href=url_for('send')
            )
        else:
            return render_template(
                'history.html',
                user=user,
                sent=sent,
                received=received,
            )

    @app.route('/user/<string:username>')
    def user_page(username):
        if not office_map.in_map(username):
            abort(404)
        return render_template(
            'user_page.html',
            user=office_map.get(username),
        )

    @app.route('/tickets/')
    def show_tickets():
        return render_template(
            'tickets.html',
            tickets=tickets
        )

    @app.route('/debug/')
    def debug_mode():
        lion = bots.get('lion', None)
        debug_items = {
            'server': {
                'server ip': tcp_server.server.getIPAddress(),
                'connected': tcp_server.server.isConnected(),
                'client ip': tcp_server.client_ip
            },
        }
        if lion:
            debug_items['bot'] = {
                'last location': (lion.props['x_loc'], lion.props['y_loc']),
                'state': lion.props['state'],
                'going to': lion.props['dest'],
                'battery': lion.props['battery_volts'],
            }
        return render_template(
            'debug.html',
            debug_items=debug_items,
            debug_log=debug_log,
            vars=[office_map.offices]
        )

    @app.route('/cmd/<string:command>', methods=['GET', 'POST'])
    def send_cmd(command):
        tcp_server.send_encoded_message(command)
        return "sending command: '{}'".format(command)

    @app.route('/api/')
    def api_help():
        return render_template_string(
            '''
            <ul>
                <li><a href="/api/map.json">map.json</a></li>
                <li><a href="/api/botinfo">bot info</a></li>
            </ul>
            '''
        )

    @app.route('/api/<string:args>', methods=['GET'])
    def api_get(args):
        if args == 'map.json':
            return office_map.to_json()
        if args == 'botinfo':
            bot = bots.get(request.args.get('name'), None)  # type: Bot
            if bot:
                return bot.to_json()
            else:
                return "error"

    @app.route('/api/<string:args>', methods=['POST'])
    def api_post(args):
        if args == 'botinfo':
            bot = bots.get(request.args.get('name'), None)  # type: Bot
            if bot:
                bot.update_from_dict({
                    # send key, value pair only if value present
                    k: request.args.get(k, type=t) for k, t in
                    [('x_loc', int), ('y_loc', int), ('state', str),
                     ('battery_volts', float)]
                    if request.args.get(k)
                })
                return bot.to_json()
            else:
                return "error"
        elif args == 'changemap':
            n = request.args.get('n')
            if not n:
                return "error"

            # force update office_map
            office_map.update({person.username: person for person in
                               Person.from_file("map_{}.txt".format(n))})
            print("loaded new map with {} offices"
                  .format(len(office_map.get())))
            tcp_server.send_encoded_message(['UPDATEMAP'])
            return office_map.to_json()

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
            # 'user': user,
            'tcp_server': tcp_server,
        }

    return app


if __name__ == '__main__':
    flask_app = create_app()

    flask_app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
