import datetime
import json
import os

import requests
from flask import Flask, render_template, request, url_for, \
    render_template_string, abort
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, current_user

from .deliverai_utils import Person, Ticket, Bot, Map, TicketRegister
from .server import DeliverAIServer


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
    MAP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maps')

    def get_map_file(map_no):
        return os.path.join(MAP_DIR, 'map{}.json'.format(map_no))

    def load_json_map(mapfile):
        # check map exists
        if not os.path.isfile(mapfile):
            return False
        # force update office_map
        office_map.update({
            person.username: person for person in
            Person.from_json_file(mapfile)
        })
        return True

    people = Person.from_json_file(get_map_file(1))
    people_map = {person.username: person for person in people}
    # user = people_map.pop("ash.ketchum", None)
    print("reading office map")
    office_map = Map(people_map)
    maps = {
        'n': 1,
        'available': sorted([
            int(f[len('map'):f.index('.')]) for f in
            os.listdir(MAP_DIR) if
            os.path.isfile(os.path.join(MAP_DIR, f)) and 'map' in f]),
    }

    def get_current_user_as_person():
        if current_user.is_authenticated:
            return office_map.get(current_user.username)
        else:
            return None

    # robots
    bots = Bot.from_file("bots.txt")

    tickets = TicketRegister()

    tcp_server = DeliverAIServer()

    in_log = []
    out_log = tcp_server.log

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
            map=office_map,
            maps=maps,
        )

    @app.route('/send/')
    def send():
        try:
            user = get_current_user_as_person()
        except KeyError:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="You're not on this map!",
                line2="Please contact an administrator "
                      "to register your office.",
                button_text="Home page",
                button_href=url_for('index'),
            )
        if not user:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="Nothing here!",
                line2="Please sign in or register to start sending.",
                button_text="Log in",
                button_href=url_for('user.login'),
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
                button_href=url_for('send'),
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
        try:
            user = get_current_user_as_person()
        except KeyError:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="You're not on this map!",
                line2="Please contact an administrator "
                      "to register your office.",
                button_text="Home page",
                button_href=url_for('index'),
            )
        if not user:
            return error_page(
                error='',
                icon="fas fa-paper-plane",
                line1="Nothing here!",
                line2="Please sign in or register to view your deliveries.",
                button_text="Log in",
                button_href=url_for('user.login'),
            )
        return render_template(
            'receive.html',
            pending_tickets=tickets.get_received(user),
            user=office_map.get(user.username),
            bot=bots.get('lion'),
            # offices=offices,
        )

    @app.route('/history/')
    def history():
        try:
            user = get_current_user_as_person()
        except KeyError:
            return error_page(
                error='',
                icon="fas fa-ticket-alt",
                line1="You're not on this map!",
                line2="Please contact an administrator "
                      "to register your office.",
                button_text="Home page",
                button_href=url_for('index'),
            )
        if not user:
            return error_page(
                error='',
                icon="fas fa-ticket-alt",
                line1="Nothing here!",
                line2="Please sign in or register to view your tickets.",
                button_text="Log in",
                button_href=url_for('user.login'),
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
            bot=bots.get('lion'),
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
            out_log=out_log,
            in_log=in_log,
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
        in_log.append(f'[{request.method:4}] {request.url}')
        if args == 'map.json':
            return office_map.to_json()
        elif args == 'current_user':
            p = get_current_user_as_person()  # type: Person
            return p.username if p else ""
        elif args == 'confirm':
            user = request.args.get('user', None)
            try:
                person = people_map[user]
            except KeyError:
                return "[]"
            pending = tickets.get_all_pending(person)
            return json.dumps([t.to_json() for t in pending])
        elif args == 'botinfo':
            bot = bots.get(request.args.get('name'), None)  # type: Bot
            if bot:
                return bot.to_json()
            else:
                return "error"
        elif args == 'tcp_server':
            return json.dumps({
                'connected': tcp_server.server.isConnected(),
                'serverIP': tcp_server.server.getIPAddress(),
                'clientIP': tcp_server.client_ip,
            })
        elif args == 'user_pin':
            user = request.args.get('user')
            try:
                person = office_map.get(user)
                code = request.args.get('code')
                return json.dumps(code == '{}0{}0'.format(person.x, person.y))
            except KeyError:
                return "false"
        elif args == 'current_map':
            return maps['n']
        elif args == 'log_get':
            pass
        elif args == 'log_post':
            pass
        else:
            return "Invalid api call (GET)."

    @app.route('/api/<string:args>', methods=['POST'])
    def api_post(args):
        in_log.append(
            f'[{request.method:4}] {request.url} - {dict(request.form)}')
        if args == 'botinfo':
            bot = bots.get(request.args.get('name'), None)  # type: Bot
            if bot:
                bot.update_from_dict({
                    # send key, value pair only if value present
                    k: request.args.get(k, type=t) for k, t in
                    [
                        ('x_loc', int),
                        ('y_loc', int),
                        ('bearing', int),
                        ('state', str),
                        ('battery_volts', float),
                    ]
                    if request.args.get(k)
                })
                # send new robot bearing to the Pi
                tcp_server.send_encoded_message(
                    ['BEARING', request.args.get('bearing')]
                )
                return bot.to_json()
            else:
                return "error"
        elif args == 'confirm':
            user = request.form.get('user', None)
            ticket = request.form.get('ticket', None)
            accepted = request.form.get('accepted', None)
            print(f"confirming with ${user} ${ticket} ${accepted}")
            if not user or not ticket:
                return "[]"
            try:
                pending = tickets.get_all_pending(people_map[user])
            except KeyError:
                return "[]"
            t = [t for t in pending if t.id == ticket]
            print(f"matched t = {t}")

            if len(t) != 1:
                return "[]"
            t[0].pending = False
            t[0].accepted = accepted == "true"
            return json.dumps(t[0].to_json())
        elif args == 'changemap':
            n = request.form.get('n')
            maps['n'] = int(n)
            if not n:
                return "error"
            # check map exists
            m = get_map_file(n)
            if not load_json_map(m):
                return "error"
            print("loaded new map with {} offices"
                  .format(len(office_map.get())))
            tcp_server.send_encoded_message(['UPDATEMAP'])
            return office_map.to_json()
        elif args == 'newmap':
            n = len(maps['available']) + 1
            with open(get_map_file(n), "w+") as f:
                f.write(json.dumps({'offices': [{}]}))
            maps['n'] = n
            maps['available'].append(n)
            tcp_server.send_encoded_message(['UPDATEMAP'])
            office_map.update({})
            return office_map.to_json()
        elif args == 'savemap':
            try:
                with open(get_map_file(maps['n']), "w+") as f:
                    f.write(office_map.to_json())
                return "Map saved successfully!"
            except Exception as e:
                return "Save failed! {}".format(e)
        elif args == 'delete_map':
            try:
                n = maps['n']
                os.remove(get_map_file(n))
                maps['available'].remove(n)

                maps['n'] = 1
                m = get_map_file(maps['n'])
                if not load_json_map(m):
                    return "error"
                return "Map deleted!"
            except Exception as e:
                return "Delete failed! {}".format(e)
        elif args == 'add_office':
            params = {
                # send key, value pair only if value present
                k: request.form.get(k, type=t) for k, t in
                [
                    ('x', int),
                    ('y', int),
                    ('username', str),
                ]
                if request.form.get(k)
            }
            try:
                s = params['username'].split('.')
                if len(s) != 2:
                    raise ValueError
                name = " ".join(s).title()
            except ValueError:
                return "Error - incorrect username. " \
                       "Please use the 'first.last' format"
            print(f' --- name = {name}')
            new_person = Person(
                params['username'],
                name,
                (params['x'], params['y'],)
            )
            try:
                office_map.add_office(new_person)
                tcp_server.send_encoded_message(['UPDATEMAP'])
            except KeyError:
                return "Error - user or office already present on the map."
            except ValueError:
                return "Cannot add office at (0, 0)!"
            return ''
        elif args == 'remove_office':
            username = request.form.get('username')
            office_map.remove_office(username)
            return f'Office removed: {username}'
        else:
            return "Invalid api call (POST)"

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
