import logging
import io
import token
import os

class NoTokensAvailableError(Exception):
    pass

def read_tokens_from_file(purse_path, max_tokens = 200, max_size = 100 * 1024):
    logger = logging.getLogger(__name__)
    try:
        if os.path.getsize(purse_path) > max_size:
            raise NoTokensAvailableError("Purse at %s is to big"%(purse_path))
    except OSError as e:
        logger.warning("OSError while reading a purse", exc_info=True)
        return []

    tokens = []
    with io.open(purse_path, 'rb') as purse:
        for line in purse:
            t = token.Token(line)
            if t not in tokens:
                tokens.append(t)
            else:
                logger.info("Found duplicated token: %s"%t.token)

            if len(tokens) >= max_tokens:
                break

    return tokens
       
class USBTokenReader(object):
    def __init__(self, mounts_path = '/proc/mounts'):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Created USBTokenReader")
        self._mounts_path = mounts_path
        self._read_paths = []

    def _read_mount_points(self):
        d = {}
        with io.open(self._mounts_path, 'r') as mounts:
            for l in mounts:
                if l[0] == '/':
                    l = l.split()
                    d[l[0]] = l[1].replace("\\040"," ")
        return d

    def read_tokens(self, max_tokens = 200, max_size = 100 * 1024):
        self._read_paths = []
        read_paths = []
        
        mount_points = self._read_mount_points()
        for mount_point in mount_points.values():
            try:
                purse_path = mount_point + '/purse'
                if not os.path.isfile(purse_path):
                    continue
                
                tokens = read_tokens_from_file(purse_path, max_tokens, max_size)
                if len(tokens) > 0:
                    self._read_paths = [mount_point]
                    return tokens
       
            except IOError as e:
                self.logger.warning("IOError while reading a purse", exc_info=True)
            except token.BadTokenFormatError:
                raise NoTokensAvailableError("Badly formatted token found in file %s"%purse_path)
        raise NoTokensAvailableError("No purse with valid tokens found")


    @property
    def medium_valid(self): 
        mount_points = self._read_mount_points()
        if len(self._read_paths) == 0:
            return False

        for path in self._read_paths:
            if path not in mount_points.values():
                return False
        return True

