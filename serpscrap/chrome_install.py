import os
import platform
import sys
import tarfile
import urllib.request
import zipfile
import tempfile
import subprocess
from scrapcore.logger import Logger

logger = Logger()
logger.setup_logger()
logger = logger.get_logger()


class ChromeInstall():

    home_dir = os.path.expanduser('chromedriver/')
    binary_win = 'chromedriver.exe'
    binary_linux64 = 'chromedriver'
    binary_linux32 = 'chromedriver'
    binary_mac64 = 'chromedriver'

    def get_os(self):
        return platform.system()

    def detect_chromedriver(self):
        logger.info('detecting chromedriver')
        this_os = self.get_os().lower()
        if 'windows' in this_os:
            if os.path.isfile(self.home_dir + self.binary_win):
                os.chmod(self.home_dir + self.binary_win, 755)
                return self.home_dir + self.binary_win
        elif 'linux' in this_os:
            if sys.maxsize > 2 ** 32:
                if os.path.isfile(self.home_dir + self.binary_linux64):
                    os.chmod(self.home_dir + self.binary_linux64, 755)
                    return self.home_dir + self.binary_linux64
            else:
                if os.path.isfile(self.home_dir + self.binary_linux32):
                    os.chmod(self.home_dir + self.binary_linux32, 755)
                    return self.home_dir + self.binary_linux32
        elif 'darwin' in this_os:
            if os.path.isfile(self.home_dir + self.binary_mac64):
                os.chmod(self.home_dir + self.binary_mac64, 755)
                return self.home_dir + self.binary_mac64
        else:
            raise Exception('''
            Platform not supported.
            install chromedriver by your own and update the path in your config
            ''')

    def download(self):
        logger.info('downloading chromedriver')
        this_os = self.get_os().lower()
        base_url = 'http://chromedriver.storage.googleapis.com/2.41/'

        if 'windows' in this_os:
            file_name = 'chromedriver_win32.zip'
            archive = 'zip'
        elif 'linux' in this_os:
            subprocess.call('./install_chrome.sh')
            archive = 'zip'
            if sys.maxsize > 2 ** 32:
                file_name = 'chromedriver_linux64.zip'
            else:
                file_name = 'chromedriver_linux64.zip'
        elif 'darwin' in this_os:
                file_name = 'chromedriver_mac64.zip'
                archive = 'zip'
        else:
            raise Exception('''
            Platform not supported.
            install chromedriver by your own and update the path in your config
            ''')
        # Download the file from `url` and save it under `file_name`:
        tmp_dir = tempfile.gettempdir() + '/'
        try:
            urllib.request.urlretrieve(base_url + file_name, tmp_dir + file_name)
            self.unpack(tmp_dir + file_name, archive)
        except:
            raise Exception('Download and unpack of chromedriver failed. Check if %(tmp_dir)s exists and has write permissions' % {'tmp_dir' : tmp_dir})

    def unpack(self, file_path, archive):
        logger.info('unpacking chromedriver')
        if os.path.isdir(self.home_dir) is False:
            os.mkdir(self.home_dir)
        if 'tar.bz2' in archive:
            tar = tarfile.open(file_path, 'r:bz2')
            tar.extractall(self.home_dir)
            tar.close()
        if 'zip' in archive:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.home_dir)
