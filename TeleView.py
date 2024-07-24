import threading
import requests
import urllib
import concurrent.futures
import time
from threading import active_count

n_threads = 400

class TelegramSubscriberApp:
    def __init__(self):
        self.links = []
        self.logs = []
        self.last_subscriber_count = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)
        self.get_links()
        self.start_process()

    def get_links(self):
        link = input("ENTER YOUR TG CHANNEL LINK: ")
        self.links.append(link)

    def update_logs(self, log_message):
        if log_message != self.last_subscriber_count:
            self.logs.append(log_message)
            print(log_message)
            self.last_subscriber_count = log_message

    def start_process(self):
        link_values = self.links
        for link in link_values:
            if not link:
                print("Link field must be filled!")
                return

        self.process_thread = threading.Thread(target=self.process, args=(link_values, True))
        self.process_thread.start()
        self.process_thread.join()

    def subscribe2(self, proxy, links):
        for i in links:
            channel = i.split('/')[3]
            self.subscribe_channel(channel, proxy)

    def subscribe_channel(self, channel, proxy):
        s = requests.Session()
        proxies = {'http': proxy, 'https': proxy}
        try:
            a = s.get(f"https://t.me/{channel}", timeout=10, proxies=proxies)
            cookie = a.headers.get('set-cookie', '').split(';')[0]
            if not cookie:
                return False
        except requests.RequestException as e:
            return False
        
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie,
            "Host": "t.me",
            "Origin": "https://t.me",
            "Referer": f"https://t.me/{channel}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        data = {
            "channel": channel
        }

        try:
            r = s.post(f'https://t.me/+{channel}', headers=headers, data=data, proxies=proxies)
            if r.status_code == 200:
                subscriber_count = r.json().get('subscribers_count', 'Unknown')
                self.update_logs(f"\033[92mSuccessfully subscribed to channel:\033[0m {channel} (Subscribers: {subscriber_count})")
            else:
                self.update_logs(f"\033[91mFailed to subscribe to channel:\033[0m {channel}")
        except (requests.RequestException, ValueError) as e:
            self.update_logs(f"\033[91mError subscribing to channel:\033[0m {channel} - {str(e)}")
            return False

    def scrap(self):
        try:
            https = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=https&timeout=0",
                                 proxies=urllib.request.getproxies(), timeout=5).text
            http = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=0",
                                proxies=urllib.request.getproxies(), timeout=5).text
            socks = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5&timeout=0",
                                 proxies=urllib.request.getproxies(), timeout=5).text
        except requests.RequestException as e:
            print(e)
            return False
        with open("proxies.txt", "w") as f:
            f.write(https + "\n" + http)
        with open("socks.txt", "w") as f:
            f.write(socks)
        return True

    def checker(self, proxy, links):
        self.subscribe2(proxy, links)

    def start(self, links):
        s = self.scrap()
        if not s:
            return
        futures = []
        with open('proxies.txt', 'r') as list:
            proxies = list.readlines()
        futures += [self.executor.submit(self.checker, p.strip(), links) for p in proxies if p.strip()]

        with open('socks.txt', 'r') as list:
            proxies = list.readlines()
        futures += [self.executor.submit(self.checker, f"socks5://{p.strip()}", links) for p in proxies if p.strip()]

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

    def process(self, links, run_forever: bool = False):
        if run_forever:
            while True:
                self.start(links)
                time.sleep(10)  # Adjust sleep time as necessary
        else:
            self.start(links)

def main():
    app = TelegramSubscriberApp()

if __name__ == "__main__":
    main()
