import os
import sys
import pandas as pd
from progress import Progress
from scroller import Scroller
from tweet import Tweet

from datetime import datetime
from fake_headers import Headers
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

TWITTER_LOGIN_URL = "https://twitter.com/i/flow/login"


class Twitter_Scraper:
    def __init__(
        self,
        mail,
        username,
        password,
        headlessState,
        max_tweets=50,
        save_folder_path="./tweets/",
        scrape_username=None,
        scrape_hashtag=None,
        scrape_query=None,
        scrape_bookmarks=False,
        scrape_poster_details=False,
        scrape_latest=True,
        scrape_top=False,
        proxy=None,
    ):
        print("Initializing Twitter Scraper...")
        self.mail = mail
        self.username = username
        self.password = password
        self.headlessState = headlessState
        self.interrupted = False
        self.tweet_ids = set()
        self.data = []
        self.tweet_cards = []
        self.save_folder_path = save_folder_path
        self.scraper_details = {
            "type": None,
            "username": None,
            "hashtag": None,
            "bookmarks": False,
            "query": None,
            "tab": None,
            "poster_details": False,
        }
        self.max_tweets = max_tweets
        self.progress = Progress(0, max_tweets)
        self.router = self.go_to_home
        self.driver = self._get_driver(proxy)
        self.actions = ActionChains(self.driver)
        self.scroller = Scroller(self.driver)
        self._config_scraper(
            max_tweets,
            scrape_username,
            scrape_hashtag,
            scrape_bookmarks,
            scrape_query,
            scrape_latest,
            scrape_top,
            scrape_poster_details,
        )

    def _config_scraper(
        self,
        max_tweets=50,
        scrape_username=None,
        scrape_hashtag=None,
        scrape_bookmarks=False,
        scrape_query=None,
        scrape_list=None,
        scrape_latest=True,
        scrape_top=False,
        scrape_poster_details=False,
    ):
        self.tweet_ids = set()
        self.data = []
        self.tweet_cards = []
        self.max_tweets = max_tweets
        self.progress = Progress(0, max_tweets)
        self.scraper_details = {
            "type": None,
            "username": scrape_username,
            "hashtag": str(scrape_hashtag).replace("#", "")
            if scrape_hashtag is not None
            else None,
            "bookmarks": scrape_bookmarks,
            "query": scrape_query,
            "list": scrape_list,
            "tab": "Latest" if scrape_latest else "Top" if scrape_top else "Latest",
            "poster_details": scrape_poster_details,
        }
        self.router = self.go_to_home
        self.scroller = Scroller(self.driver)

        if scrape_username is not None:
            self.scraper_details["type"] = "Username"
            self.router = self.go_to_profile
        elif scrape_hashtag is not None:
            self.scraper_details["type"] = "Hashtag"
            self.router = self.go_to_hashtag
        elif scrape_bookmarks is not False:
            self.scraper_details["type"] = "Bookmarks"
            self.router = self.go_to_bookmarks
        elif scrape_query is not None:
            self.scraper_details["type"] = "Query"
            self.router = self.go_to_search
        elif scrape_list is not None:
            self.scraper_details["type"] = "List"
            self.router = self.go_to_list
        else:
            self.scraper_details["type"] = "Home"
            self.router = self.go_to_home
        pass

    def _get_driver(
        self,
        proxy=None,
    ):
        print("Setup WebDriver...")
        # header = Headers().generate()["User-Agent"] 

        # User agent of a andoird smartphone device
        header="Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.87 Mobile Safari/537.36"

        # browser_option = ChromeOptions()
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
            # print("Initializing ChromeDriver...")
            # driver = webdriver.Chrome(
            #     options=browser_option,
            # )

            print("Initializing FirefoxDriver...")
            driver = webdriver.Firefox(
                options=browser_option,
            )

            print("WebDriver Setup Complete")
            return driver
        except WebDriverException:
            try:
                # print("Downloading ChromeDriver...")
                # chromedriver_path = ChromeDriverManager().install()
                # chrome_service = ChromeService(executable_path=chromedriver_path)

                # print("Initializing ChromeDriver...")
                # driver = webdriver.Chrome(
                #     service=chrome_service,
                #     options=browser_option,
                # )

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
                    """This may be due to the following:

- Internet connection is unstable
- Username is incorrect
- Password is incorrect
"""
                )

            print()
            print("Login Successful")
            print()
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
                        """There was an error inputting the username.

It may be due to the following:
- Internet connection is unstable
- Username is incorrect
- Twitter is experiencing unusual activity"""
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
                        """There was an error inputting the password.

It may be due to the following:
- Internet connection is unstable
- Password is incorrect
- Twitter is experiencing unusual activity"""
                    )
                    self.driver.quit()
                    sys.exit(1)
                else:
                    print("Re-attempting to input password...")
                    sleep(2)

    def go_to_home(self):
        self.driver.get("https://twitter.com/home")
        sleep(3)
        pass

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
        self.tweet_cards = self.driver.find_elements(
            "xpath", '//article[@data-testid="tweet" and not(@disabled)]'
        )
        pass

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

    def scrape_tweets(
        self,
        max_tweets=50,
        no_tweets_limit=False,
        scrape_username=None,
        scrape_hashtag=None,
        scrape_bookmarks=False,
        scrape_query=None,
        scrape_list=None,
        scrape_latest=True,
        scrape_top=False,
        scrape_poster_details=False,
        router=None,
    ):
        self._config_scraper(
            max_tweets,
            scrape_username,
            scrape_hashtag,
            scrape_bookmarks,
            scrape_query,
            scrape_list,
            scrape_latest,
            scrape_top,
            scrape_poster_details,
        )

        if router is None:
            router = self.router

        router()

        if self.scraper_details["type"] == "Username":
            print(
                "Scraping Tweets from @{}...".format(self.scraper_details["username"])
            )
        elif self.scraper_details["type"] == "Hashtag":
            print(
                "Scraping {} Tweets from #{}...".format(
                    self.scraper_details["tab"], self.scraper_details["hashtag"]
                )
            )
        elif self.scraper_details["type"] == "Bookmarks":
            print(
                "Scraping Tweets from bookmarks...".format(self.scraper_details["username"]))
        elif self.scraper_details["type"] == "Query":
            print(
                "Scraping {} Tweets from {} search...".format(
                    self.scraper_details["tab"], self.scraper_details["query"]
                )
            )
        elif self.scraper_details["type"] == "Home":
            print("Scraping Tweets from Home...")

        # Accept cookies to make the banner disappear
        try:
            accept_cookies_btn = self.driver.find_element(
            "xpath", "//span[text()='Refuse non-essential cookies']/../../..")
            accept_cookies_btn.click()
        except NoSuchElementException:
            pass

        self.progress.print_progress(0, False, 0, no_tweets_limit)

        refresh_count = 0
        added_tweets = 0
        empty_count = 0
        retry_cnt = 0

        while self.scroller.scrolling:
            try:
                self.get_tweet_cards()
                added_tweets = 0

                for card in self.tweet_cards[-15:]:
                    try:
                        tweet_id = str(card)

                        if tweet_id not in self.tweet_ids:
                            self.tweet_ids.add(tweet_id)

                            if not self.scraper_details["poster_details"]:
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView();", card
                                )

                            import ipdb; ipdb.set_trace()
                            tweet = Tweet(
                                card=card,
                                driver=self.driver,
                                actions=self.actions,
                                scrape_poster_details=self.scraper_details[
                                    "poster_details"
                                ],
                            )

                            if tweet:
                                if not tweet.error and tweet.tweet is not None:
                                    if not tweet.is_ad:
                                        self.data.append(tweet.tweet)
                                        added_tweets += 1
                                        self.progress.print_progress(len(self.data), False, 0, no_tweets_limit)

                                        if len(self.data) >= self.max_tweets and not no_tweets_limit:
                                            self.scroller.scrolling = False
                                            break
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue
                    except NoSuchElementException:
                        continue

                if len(self.data) >= self.max_tweets and not no_tweets_limit:
                    break

                if added_tweets == 0:
                    # Check if there is a button "Retry" and click on it with a regular basis until a certain amount of tries
                    try:
                        while retry_cnt < 15:
                            retry_button = self.driver.find_element(
                            "xpath", "//span[text()='Retry']/../../..")
                            self.progress.print_progress(len(self.data), True, retry_cnt, no_tweets_limit)
                            sleep(600)
                            retry_button.click()
                            retry_cnt += 1
                            sleep(2)
                    # There is no Retry button so the counter is reseted
                    except NoSuchElementException:
                        retry_cnt = 0
                        self.progress.print_progress(len(self.data), False, 0, no_tweets_limit)

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

        if len(self.data) >= self.max_tweets or no_tweets_limit:
            print("Scraping Complete")
        else:
            print("Scraping Incomplete")

        if not no_tweets_limit:
            print("Tweets: {} out of {}\n".format(len(self.data), self.max_tweets))

        pass

    def scrape_tweet_conversation(
        self,
        tweet_url: str,
        max_tweets: int = 50,
    ):
        """
        given a tweet url get all the tweets within the conversation, i.e., 
        the tweet's replies and possibly sub-threads, especially when author
        has written sub-tweets.
        logic is to get all tweets or up to max_tweets before the "Discover more" 
        section: by observation it's found that the end of a thread is marked
        by the start of the "Discover more" section (if present at all).
        """
        try:
            # get the tweet
            self.driver.get(tweet_url)
            # wait for the tweet to load
            sleep(3)

            # Prepare the conversation
            conversation = []
            seen_tweet_ids = set()  # Track processed tweet IDs to avoid duplicates
            consecutive_empty_scrolls = 0
            max_empty_scrolls = 3
            discover_more_boundary = False
            
            # Main scrolling loop to collect tweets
            while not discover_more_boundary and len(conversation) < max_tweets and consecutive_empty_scrolls < max_empty_scrolls:
                # Look for "Show more" buttons and click them
                show_more_buttons = self.driver.find_elements(
                    "xpath", '//button[@data-testid="tweet-text-show-more-link"]'
                )
                
                for button in show_more_buttons:
                    try:
                        # Scroll button into view to ensure it's clickable
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        sleep(0.5)
                        
                        # Click the button to expand content
                        button.click()
                        sleep(1)  # Wait for content to expand
                    except Exception as e:
                        # Handle any clicking errors gracefully
                        continue 
                
                # Find the "Discover more" section position for boundary check
                try:
                    discover_more_element = self.driver.find_element(
                        "xpath", '//span[text()="Discover more"]'
                    )
                    discover_more_position = discover_more_element.location['y']
                except NoSuchElementException:
                    # If "Discover more" not found, include all tweets
                    discover_more_position = float('inf')
                
                # Get all current visible tweet cards
                current_tweet_cards = self.driver.find_elements(
                    "xpath", '//article[@data-testid="tweet" and not(@disabled)]'
                )
                
                # Track how many new tweets we find in this iteration
                new_tweets_found = 0
                
                # Process visible tweet cards
                for card in current_tweet_cards:
                    if len(conversation) >= max_tweets:
                        break
                    
                    try:
                        # Check if tweet is before "Discover more" boundary
                        tweet_position = card.location['y']
                        if tweet_position >= discover_more_position:
                            # Skip tweets that are after "Discover more"
                            discover_more_boundary = True
                            break
                        
                        # Extract tweet ID using the same logic as Tweet class
                        tweet_link = card.find_element(
                            "xpath", ".//a[contains(@href, '/status/')]"
                        ).get_attribute("href")
                        tweet_id = str(tweet_link.split("/")[-1])
                        
                        # Skip if we've already processed this tweet
                        if tweet_id in seen_tweet_ids:
                            continue
                        
                        seen_tweet_ids.add(tweet_id)
                        
                        # Create Tweet object and process
                        tweet = Tweet(
                            card=card,
                            driver=self.driver,
                            actions=self.actions,
                            scrape_poster_details=self.scraper_details["poster_details"],
                        )
                        
                        if tweet and not tweet.error and tweet.tweet is not None:
                            if not tweet.is_ad:
                                conversation.append(tweet.tweet)
                                new_tweets_found += 1
                                
                    except Exception as e:
                        # Skip tweets we can't process
                        continue
                
                # Update consecutive empty scroll counter
                if new_tweets_found == 0:
                    consecutive_empty_scrolls += 1
                else:
                    consecutive_empty_scrolls = 0
                
                # Scroll down to load more tweets (unless we've hit limits)
                if not discover_more_boundary and len(conversation) < max_tweets and consecutive_empty_scrolls < max_empty_scrolls:
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    sleep(2)
            
            return conversation
        
        except KeyboardInterrupt:
            print("\n")
            print("Keyboard Interrupt")
        
        except Exception as e:
            print("\n")
            print(f"Error scraping tweets: {e}")

    
    def _save_helper(self):
        now = datetime.now()

        if not os.path.exists(self.save_folder_path):
            os.makedirs(self.save_folder_path)
            print("Created Folder: {}".format(self.save_folder_path))

        data = {
            "Name": [tweet[0] for tweet in self.data],
            "Handle": [tweet[1] for tweet in self.data],
            "Timestamp": [tweet[2] for tweet in self.data],
            "Verified": [tweet[3] for tweet in self.data],
            "Content": [tweet[4] for tweet in self.data],
            "Comments": [tweet[5] for tweet in self.data],
            "Retweets": [tweet[6] for tweet in self.data],
            "Likes": [tweet[7] for tweet in self.data],
            "Analytics": [tweet[8] for tweet in self.data],
            "Tags": [tweet[9] for tweet in self.data],
            "Mentions": [tweet[10] for tweet in self.data],
            "Emojis": [tweet[11] for tweet in self.data],
            "Profile Image": [tweet[12] for tweet in self.data],
            "Tweet Link": [tweet[13] for tweet in self.data],
            "Tweet ID": [f"tweet_id:{tweet[14]}" for tweet in self.data],
        }

        if self.scraper_details["poster_details"]:
            data["Tweeter ID"] = [f"user_id:{tweet[15]}" for tweet in self.data]
            data["Following"] = [tweet[16] for tweet in self.data]
            data["Followers"] = [tweet[17] for tweet in self.data]

        df = pd.DataFrame(data)

        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        fn = f"{current_time}_tweets_1-{len(self.data)}"

        return df, fn

    def save_to_csv(self):
        print("Saving Tweets to CSV...")
        df, file_name = self._save_helper()
        file_path = os.path.join(self.save_folder_path, f"{file_name}.csv")
        pd.set_option("display.max_colwidth", None)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print("CSV Saved: {}".format(file_path))

    def save_to_jsonl(self):
        print("Saving Tweets to JSONL...")
        df, file_name = self._save_helper()
        file_path = os.path.join(self.save_folder_path, f"{file_name}.jsonl")
        df.to_json(file_path, orient="records", lines=True)
        print("JSONL Saved: {}".format(file_path))

    def get_tweets(self):
        return self.data
