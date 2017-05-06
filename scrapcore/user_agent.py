# -*- coding: utf-8 -*-
import random

user_agents_mobile = [
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_2_1 like Mac OS X) AppleWebKit/602.4.6 (KHTML, like Gecko) Version/10.0 Mobile/14D27 Safari/602.1',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0 Mobile/14C92 Safari/602.1',
    'Mozilla/5.0 (Linux, Android 7.0, SAMSUNG SM-G930F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/5.0 Chrome/51.0.2704.106 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SM-G920F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 7.0, SM-G930F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 7.0, SAMSUNG SM-G935F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/5.0 Chrome/51.0.2704.106 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G900F Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_1_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0 Mobile/14B100 Safari/602.1',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E277 Safari/602.1',
    'Mozilla/5.0 (Linux, Android 7.0, SM-G935F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_2_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) GSA/24.1.151204851 Mobile/14D27 Safari/602.1',
    'Mozilla/5.0 (Linux, Android 6.0.1, SM-G900F Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G920F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/5.0 Chrome/51.0.2704.106 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0, ALE-L21 Build/HuaweiALE-L21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G920F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SM-G925F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A456 Safari/602.1',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) GSA/24.1.151204851 Mobile/14E304 Safari/602.1',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-A510F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SM-G920F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Crosswalk/20.50.533.12 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 7.0, SM-G935F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Crosswalk/20.50.533.12 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SM-A510F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G800F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone, CPU iPhone OS 9_3_5 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13G36 Safari/601.1',
    'Mozilla/5.0 (Linux, Android 7.0, SM-G930F Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Crosswalk/20.50.533.12 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G925F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/5.0 Chrome/51.0.2704.106 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux, Android 6.0, HUAWEI VNS-L31 Build/HUAWEIVNS-L31) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.132 Mobile Safari/537.36',
    'Mozilla/5.0 (Android 6.0.1, Mobile, rv:52.0) Gecko/52.0 Firefox/52.0',
    'Mozilla/5.0 (Linux, Android 6.0.1, SAMSUNG SM-G903F Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
]

user_agents_computer = [
    'Mozilla/5.0 (Windows NT 6.1, WOW64, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 10.0, WOW64, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 6.1, WOW64, Trident/7.0, rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0, Win64, x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1, WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0, WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0, Win64, x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
    'Mozilla/5.0 (Windows NT 6.1, Win64, x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (X11, Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1, Trident/7.0, rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.3, WOW64, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Macintosh, Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30',
    'Mozilla/5.0 (Windows NT 6.1, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 6.1, WOW64, rv:45.0) Gecko/20100101 Firefox/45.0',
    # 'Mozilla/5.0 (Windows NT 10.0, WOW64, Trident/7.0, rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.3, WOW64, Trident/7.0, rv:11.0) like Gecko',
    'Mozilla/5.0 (Macintosh, Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',
    'Mozilla/5.0 (Windows NT 10.0, Win64, x64, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3, WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 6.1, Win64, x64, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Macintosh, Intel Mac OS X 10_11_6) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30',
    'Mozilla/5.0 (Windows NT 6.3, Win64, x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1, WOW64, rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Windows NT 6.1, WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0, WOW64, rv:51.0) Gecko/20100101 Firefox/51.0',
    'Mozilla/5.0 (Windows NT 6.0, rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 6.1, Win64, x64, Trident/7.0, rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 5.1, rv:52.0) Gecko/20100101 Firefox/52.0',
]


def random_user_agent(mobile=False):
    if mobile is True:
        return random.choice(user_agents_mobile)
    else:
        return random.choice(user_agents_computer)
