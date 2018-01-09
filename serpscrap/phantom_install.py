import os
import platform
import sys
import tarfile
import urllib.request
import zipfile
import tempfile
from scrapcore.logger import Logger

logger = Logger()
logger.setup_logger()
logger = logger.get_logger()


class PhantomInstall():

    home_dir = os.path.expanduser('phantomjs/')
    binary_win = 'phantomjs-2.1.1-windows/bin/phantomjs.exe'
    binary_linux64 = 'phantomjs-2.1.1-linux-x86_64/bin/phantomjs'
    binary_linux32 = 'phantomjs-2.1.1-linux-i686/bin/phantomjs'

    def get_os(self):
        return platform.system()

    def detect_phantomjs(self):
        logger.info('detecting phantomjs')
        this_os = self.get_os().lower()
        if 'windows' in this_os:
            if os.path.isfile(self.home_dir + self.binary_win):
                return self.home_dir + self.binary_win
        elif 'linux' in this_os:
            if sys.maxsize > 2 ** 32:
                if os.path.isfile(self.home_dir + self.binary_linux64):
                    return self.home_dir + self.binary_linux64
            else:
                if os.path.isfile(self.home_dir + self.binary_linux32):
                    return self.home_dir + self.binary_linux32
        else:
            raise Exception('''
            Platform not supported.
            install phantomjs manualy and update the path in your config
            ''')

    def download(self):
        logger.info('downloading phantomjs')
        this_os = self.get_os().lower()
        base_url = 'https://bitbucket.org/ariya/phantomjs/downloads/'

        if 'windows' in this_os:
            file_name = 'phantomjs-2.1.1-windows.zip'
            archive = 'zip'
        elif 'linux' in this_os:
            archive = 'tar.bz2'
            if sys.maxsize > 2 ** 32:
                file_name = 'phantomjs-2.1.1-linux-x86_64.tar.bz2'
            else:
                file_name = 'phantomjs-2.1.1-linux-i686.tar.bz2'
        else:
            raise Exception('''
            Platform not supported.
            install phantomjs manualy and update the path in your config
            ''')
        # Download the file from `url` and save it under `file_name`:
        tmp_dir = tempfile.gettempdir() + '/'
        try:
            urllib.request.urlretrieve(base_url + file_name, tmp_dir + file_name)
            self.unpack(tmp_dir + file_name, archive)
        except:
            raise Exception('Download and unpack of phantomjs failed. Check if %(tmp_dir)s exists and has write permissions' % {'tmp_dir' : tmp_dir})

    def unpack(self, file_path, archive):
        logger.info('unpacking phantomjs')
        if os.path.isdir(self.home_dir) is False:
            os.mkdir(self.home_dir)
        if 'tar.bz2' in archive:
            tar = tarfile.open(file_path, 'r:bz2')
            tar.extractall(self.home_dir)
            tar.close()
        if 'zip' in archive:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.home_dir)
