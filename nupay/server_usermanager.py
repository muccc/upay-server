import ConfigParser
import io
import logging
import bcrypt

ROLE_TOKEN_MANAGER = "token_manager"
ROLE_CHARGING_STATION = "charging_station"
ROLE_VENDING_MACHINE = "vending_machine"

class User(object):
    def __init__(self, config, name):
        self._username = name
        self._role = config.get(name, 'role')
        self._password_hash = config.get(name, 'password_hash')
        self._active = config.getboolean(name, 'active')
        self._bad_passwords = config.getint(name, 'bad_passwords')

    @property
    def username(self):
        return self._username

    @property
    def active(self):
        return self._active

    @property
    def password_hash(self):
        return self._password_hash

    @property
    def role(self):
        return self._role

    @property
    def bad_passwords(self):
        return self._bad_passwords

    @property
    def timeout(self):
        if self.bad_passwords > 0:
            return 5
        return 0


class ServerUserManager(object):
    def __init__(self, users_config):
        self._logger = logging.getLogger(__name__)
        self._users_config = users_config

        self._users = {}
        for name in users_config.sections():
            self._users[name] = User(users_config, name)

    @property
    def users(self):
        return self._users

    def check_password(self, user, password):
        if bcrypt.hashpw(password, user.password_hash) == user.password_hash:
            user._bad_passwords = 0
            self._logger.info("Password OK")
            return True

        self._logger.info("Password WRONG")
        user._bad_passwords += 1
        return False

