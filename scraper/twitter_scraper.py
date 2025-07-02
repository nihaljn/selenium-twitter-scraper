import os
import sys
import pandas as pd
from .progress import Progress
from .scroller import Scroller
from .tweet import Tweet

from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from functools import partial

TWITTER_LOGIN_URL = "https://twitter.com/i/flow/login"


class Twitter_Scraper:
    def __init__(
        self,
        username,
        password,
        headlessState,
        save_folder_path="./tweets/",
        proxy=None,
        browser: str = "firefox"
    ):
        print("Initializing Twitter Scraper...")
        self.username = username
        self.password = password
        self.headlessState = headlessState
        self.interrupted = False
        self.save_folder_path = save_folder_path
        self.driver = self._get_driver(proxy, browser)
        self.actions = ActionChains(self.driver)
        self.logged_in = False

    def _route(self, mode, url: str | None):
        # configure current scraping session
        if mode == "username":
            router = self.go_to_profile
        elif mode == "hashtag":
            router = self.go_to_hashtag
        elif mode == "bookmarks":
            router = self.go_to_bookmarks
        elif mode == "query":
            router = self.go_to_search
        elif mode == "list":
            router = self.go_to_list
        elif mode == "timeline":
            router = self.go_to_timeline
        elif mode == "conversation":
            assert url is not None, "URL is required for conversation mode"
            router = partial(self.go_to_url, url=url)
        else:
            print(ValueError("Invalid mode"))
            sys.exit(1)
        router()

    def _get_driver(
        self,
        proxy=None,
        browser: str = "firefox"
    ):
        print("Setup WebDriver...")
        # header = Headers().generate()["User-Agent"] 

        # User agent of a andoird smartphone device
        header="Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.87 Mobile Safari/537.36"

        if browser == "chrome":
            browser_option = ChromeOptions()
        elif browser == "firefox":
            browser_option = FirefoxOptions()
        
        browser_option.add_argument("--no-sandbox")
        browser_option.add_argument("--disable-dev-shm-usage")
        browser_option.add_argument("--ignore-certificate-errors")
        browser_option.add_argument("--disable-gpu")
        browser_option.add_argument("--log-level=3")
        browser_option.add_argument("--disable-notifications")
        browser_option.add_argument("--disable-popup-blocking")
        browser_option.add_argument("--user-agent={}".format(header))
        if proxy is not None:
            browser_option.add_argument("--proxy-server=%s" % proxy)

        # Option to hide browser or not
        # If not yes then skips the headless
        if self.headlessState == 'yes':
            # For Hiding Browser
            browser_option.add_argument("--headless")

        try:
            if browser == "chrome":
                print("Initializing ChromeDriver...")
                driver = webdriver.Chrome(
                    options=browser_option,
                )

            elif browser == "firefox":
                print("Initializing FirefoxDriver...")
                driver = webdriver.Firefox(
                    options=browser_option,
                )

            print("WebDriver Setup Complete")
            return driver
        
        except WebDriverException:
            try:
                if browser == "chrome":
                    print("Downloading ChromeDriver...")
                    chromedriver_path = ChromeDriverManager().install()
                    chrome_service = ChromeService(executable_path=chromedriver_path)

                    print("Initializing ChromeDriver...")
                    driver = webdriver.Chrome(
                        service=chrome_service,
                        options=browser_option,
                    )

                elif browser == "firefox":
                    print("Downloading FirefoxDriver...")
                    firefoxdriver_path = GeckoDriverManager().install()
                    firefox_service = FirefoxService(executable_path=firefoxdriver_path)

                    print("Initializing FirefoxDriver...")
                    driver = webdriver.Firefox(
                        service=firefox_service,
                        options=browser_option,
                    )

                print("WebDriver Setup Complete")
                return driver
            except Exception as e:
                print(f"Error setting up WebDriver: {e}")
                sys.exit(1)
        pass

    def login(self):
        print()
        print("Logging in to Twitter...")

        try:
            self.driver.maximize_window()
            self.driver.execute_script("document.body.style.zoom='150%'") #set zoom to 150%
            self.driver.get(TWITTER_LOGIN_URL)
            sleep(3)

            self._input_username()
            self._input_unusual_activity()
            self._input_password()

            cookies = self.driver.get_cookies()

            auth_token = None

            for cookie in cookies:
                if cookie["name"] == "auth_token":
                    auth_token = cookie["value"]
                    break

            if auth_token is None:
                raise ValueError(
                    "This may be due to the following:\n"
                    "- Internet connection is unstable\n"
                    "- Username is incorrect\n"
                    "- Password is incorrect"
                )
            print()
            print("Login Successful")
            print()
            self.logged_in = True
        except Exception as e:
            print()
            print(f"Login Failed: {e}")
            sys.exit(1)

        pass

    def _input_username(self):
        input_attempt = 0

        while True:
            try:
                username = self.driver.find_element(
                    "xpath", "//input[@autocomplete='username']"
                )

                username.send_keys(self.username)
                username.send_keys(Keys.RETURN)
                sleep(3)
                break
            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    print()
                    print(
                        "There was an error inputting the username.\n\n"
                        "It may be due to the following:\n"
                        "- Internet connection is unstable\n"
                        "- Username is incorrect\n"
                        "- Twitter is experiencing unusual activity"
                    )
                    self.driver.quit()
                    sys.exit(1)
                else:
                    print("Re-attempting to input username...")
                    sleep(2)

    def _input_unusual_activity(self):
        input_attempt = 0

        while True:
            try:
                unusual_activity = self.driver.find_element(
                    "xpath", "//input[@data-testid='ocfEnterTextTextInput']"
                )
                unusual_activity.send_keys(self.username)
                unusual_activity.send_keys(Keys.RETURN)
                sleep(3)
                break
            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    break

    def _input_password(self):
        input_attempt = 0

        while True:
            try:
                password = self.driver.find_element(
                    "xpath", "//input[@autocomplete='current-password']"
                )

                password.send_keys(self.password)
                password.send_keys(Keys.RETURN)
                sleep(3)
                break
            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    print()
                    print(
                        "There was an error inputting the password.\n\n"
                        "It may be due to the following:\n"
                        "- Internet connection is unstable\n"
                        "- Password is incorrect\n"
                        "- Twitter is experiencing unusual activity"
                    )
                    self.driver.quit()
                    sys.exit(1)
                else:
                    print("Re-attempting to input password...")
                    sleep(2)

    def go_to_timeline(self):
        self.driver.get("https://twitter.com/home")
        sleep(3)

    def go_to_url(self, url=None):
        self.driver.get(url)
        sleep(3)

    def go_to_profile(self):
        if (
            self.scraper_details["username"] is None
            or self.scraper_details["username"] == ""
        ):
            print("Username is not set.")
            sys.exit(1)
        else:
            self.driver.get(f"https://twitter.com/{self.scraper_details['username']}")
            sleep(3)
        pass

    def go_to_hashtag(self):
        if (
            self.scraper_details["hashtag"] is None
            or self.scraper_details["hashtag"] == ""
        ):
            print("Hashtag is not set.")
            sys.exit(1)
        else:
            url = f"https://twitter.com/hashtag/{self.scraper_details['hashtag']}?src=hashtag_click"
            if self.scraper_details["tab"] == "Latest":
                url += "&f=live"

            self.driver.get(url)
            sleep(3)
        pass

    def go_to_bookmarks(self):
        if (
            self.scraper_details["bookmarks"] is False
            or self.scraper_details["bookmarks"] == ""
        ):
            print("Bookmarks is not set.")
            sys.exit(1)
        else:
            url = f"https://twitter..com/i/bookmarks"

            self.driver.get(url)
            sleep(3)
        pass

    def go_to_search(self):
        if self.scraper_details["query"] is None or self.scraper_details["query"] == "":
            print("Query is not set.")
            sys.exit(1)
        else:
            url = f"https://twitter.com/search?q={self.scraper_details['query']}&src=typed_query"
            if self.scraper_details["tab"] == "Latest":
                url += "&f=live"

            self.driver.get(url)
            sleep(3)
        pass

    def go_to_list(self):
        if self.scraper_details["list"] is None or self.scraper_details["list"] == "":
            print("List is not set.")
            sys.exit(1)
        else:
            url = f"https://x.com/i/lists/{self.scraper_details['list']}"
            self.driver.get(url)
            sleep(3)
        pass

    def get_tweet_cards(self):
        tweet_cards = self.driver.find_elements(
            "xpath", '//article[@data-testid="tweet" and not(@disabled)]'
        )
        return tweet_cards

    def remove_hidden_cards(self):
        try:
            hidden_cards = self.driver.find_elements(
                "xpath", '//article[@data-testid="tweet" and @disabled]'
            )

            for card in hidden_cards[1:-2]:
                self.driver.execute_script(
                    "arguments[0].parentNode.parentNode.parentNode.remove();", card
                )
        except Exception as e:
            return
        pass

    def _click_all_show_more_buttons(self):
        # Look for "Show more" buttons and click them
        show_more_buttons = self.driver.find_elements(
            "xpath", '//button[@data-testid="tweet-text-show-more-link"]'
        )
        for button in show_more_buttons:
            try:
                # Scroll button into view to ensure it's clickable
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", 
                    button
                )
                sleep(0.5)
                # Click the button to expand content
                button.click()
                sleep(1)  # Wait for content to expand
            except Exception as e:
                # Handle any clicking errors gracefully
                continue 
        
    def scrape_tweets(
        self,
        max_tweets: int = 50,
        mode: str = "timeline",
        no_tweets_limit: bool = False,
        scrape_poster_details: bool = False,
        url: str = None
    ):
        # set the router and route accordingly
        self._route(mode, url=url)
        progress = Progress(0, max_tweets)
        scroller = Scroller(self.driver)

        if mode == "timeline":
            print("Scraping Tweets from Home...")
        elif mode == "conversation":
            print(f"Scraping Tweets from conversation: {url} ...")
        else:
            raise NotImplementedError(f"Mode {mode} is not implemented.")

        # Accept cookies to make the banner disappear
        try:
            accept_cookies_btn = self.driver.find_element(
            "xpath", "//span[text()='Refuse non-essential cookies']/../../..")
            accept_cookies_btn.click()
        except NoSuchElementException:
            pass

        progress.print_progress(0, False, 0, no_tweets_limit)

        refresh_count = 0
        added_tweets = 0
        empty_count = 0
        retry_cnt = 0
        data = []
        tweet_ids = set()
        discover_more_boundary = False

        while scroller.scrolling:
            try:
                
                # Find the "Discover more" section position for boundary check
                try:
                    discover_more_element = self.driver.find_element(
                        "xpath", '//span[text()="Discover more"]'
                    )
                    discover_more_position = discover_more_element.location['y']
                except NoSuchElementException:
                    # If "Discover more" not found, include all tweets
                    discover_more_position = float('inf')

                self._click_all_show_more_buttons()
                tweet_cards = self.get_tweet_cards()
                added_tweets = 0

                for card in tweet_cards[-15:]:
                    try:
                        tweet_position = card.location['y']
                        if tweet_position >= discover_more_position:
                            # Skip tweets that are after "Discover more"
                            discover_more_boundary = True
                            break

                        tweet_id = str(card)

                        if tweet_id not in tweet_ids:
                            tweet_ids.add(tweet_id)

                            if not scrape_poster_details:
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView();", card
                                )

                            # import ipdb; ipdb.set_trace()
                            tweet = Tweet(
                                card=card,
                                driver=self.driver,
                                actions=self.actions,
                                scrape_poster_details=scrape_poster_details
                            )

                            if tweet:
                                if not tweet.error and tweet.tweet is not None:
                                    if not tweet.is_ad:
                                        data.append(tweet.tweet)
                                        added_tweets += 1
                                        progress.print_progress(len(data), False, 0, no_tweets_limit)

                                        if len(data) >= max_tweets and not no_tweets_limit:
                                            scroller.scrolling = False
                                            break
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                        
                    except NoSuchElementException:
                        continue

                if discover_more_boundary or (len(data) >= max_tweets and not no_tweets_limit):
                    break

                if added_tweets == 0:
                    # Check if there is a button "Retry" and click on it with a regular basis until a certain amount of tries
                    try:
                        while retry_cnt < 15:
                            retry_button = self.driver.find_element(
                            "xpath", "//span[text()='Retry']/../../..")
                            progress.print_progress(len(data), True, retry_cnt, no_tweets_limit)
                            sleep(600)
                            retry_button.click()
                            retry_cnt += 1
                            sleep(2)
                    # There is no Retry button so the counter is reseted
                    except NoSuchElementException:
                        retry_cnt = 0
                        progress.print_progress(len(data), False, 0, no_tweets_limit)

                    if empty_count >= 5:
                        if refresh_count >= 3:
                            print()
                            print("No more tweets to scrape")
                            break
                        refresh_count += 1
                    empty_count += 1
                    sleep(1)
                else:
                    empty_count = 0
                    refresh_count = 0
            except StaleElementReferenceException:
                sleep(2)
                continue
            except KeyboardInterrupt:
                print("\n")
                print("Keyboard Interrupt")
                self.interrupted = True
                break
            except Exception as e:
                print("\n")
                print(f"Error scraping tweets: {e}")
                break

        print("")

        if len(data) >= max_tweets or no_tweets_limit or mode == "conversation":
            print("Scraping Complete")
        else:
            print("Scraping Incomplete")

        if not no_tweets_limit:
            print("Tweets: {} out of {}\n".format(len(data), max_tweets))

        return data
    
    def _save_helper(self, data):
        now = datetime.now()

        if not os.path.exists(self.save_folder_path):
            os.makedirs(self.save_folder_path)
            print("Created Folder: {}".format(self.save_folder_path))

        df = pd.DataFrame(data)

        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        fn = f"{current_time}_tweets_1-{len(data)}"

        return df, fn

    def save_to_csv(self, data):
        print("Saving Tweets to CSV...")
        df, file_name = self._save_helper(data)
        file_path = os.path.join(self.save_folder_path, f"{file_name}.csv")
        pd.set_option("display.max_colwidth", None)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print("CSV Saved: {}".format(file_path))

    def save_to_jsonl(self, data):
        print("Saving Tweets to JSONL...")
        df, file_name = self._save_helper(data)
        file_path = os.path.join(self.save_folder_path, f"{file_name}.jsonl")
        df.to_json(file_path, orient="records", lines=True)
        print("JSONL Saved: {}".format(file_path))

    def close(self):
        if self.driver is not None:
            self.driver.quit()
            print("Closed session.")
            self.logged_in = False
        else:
            print("Driver is already closed.")

    def is_logged_in(self):
        return self.logged_in
