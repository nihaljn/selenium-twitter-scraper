from time import sleep

from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from card import Card
from quote import Quote
from utils import resolve_short_url


class Tweet(Card):
    def __init__(
        self,
        card: WebElement,
        driver: WebDriver | None = None,
        actions: ActionChains | None = None,
        scrape_poster_details: bool = False,
    ) -> None:
        """
        actions and driver needed only if scrape_poster_details is True
        """
        super().__init__(card)
        self.driver = driver
        self.actions = actions
        self.scrape_poster_details = scrape_poster_details
        self.error = False
        self.tweet = None
        self.poster_details = {}
        self._scrape()
        # Build final tweet dictionary
        self._build_tweet_dict()
        

    def _scrape_quoted_tweet(self):
        try:
            # Find the div that contains the "Quote" span
            quote_card = self.card.find_element(
                "xpath", './/span[text()="Quote"]/parent::div/parent::div'
            )

            # The quote card is this div
            quote = Quote(quote_card)
            if not quote.error:
                self.quoted_tweet = quote
                self.has_quote = True
            else:
                self.quoted_tweet = None
                self.has_quote = False

        except NoSuchElementException:
            self.quoted_tweet = None
            self.has_quote = False

    def _scrape_images(self):
        try:
            images = self.card.find_elements(
                "xpath", './/div[@data-testid="tweetPhoto"]//img'
            )
            image_urls = []
            for img in images:
                try:
                    img_src = img.get_attribute('src')
                    if img_src:
                        # exclude those in quote
                        if self.has_quote and img_src in self.quoted_tweet.image_urls:
                            continue
                        image_urls.append(img_src)
                except:
                    continue
            self.image_urls = image_urls
            self.image_count = len(image_urls)
        except NoSuchElementException:
            self.image_urls = []
            self.image_count = 0

    def _scrape_videos(self):
        try:
            video_players = self.card.find_elements(
                "xpath", './/div[@data-testid="videoPlayer"]'
            )
            video_urls = []
            video_thumbnails = []
            video_durations = []
            
            for video_player in video_players:
                try:
                    # Get video blob URL
                    video_sources = video_player.find_elements("xpath", './/video//source')
                    for source in video_sources:
                        video_url = source.get_attribute("src")
                        if video_url and video_url.startswith("blob:"):
                            video_urls.append(video_url)
                    
                    # Get video thumbnail/poster
                    video_element = video_player.find_element("xpath", './/video')
                    poster = video_element.get_attribute("poster")
                    if poster:
                        video_thumbnails.append(poster)
                    
                    # Get video duration
                    try:
                        duration_element = video_player.find_element(
                            "xpath", './/span[contains(text(), ":")]'
                        )
                        duration = duration_element.text.strip()
                        if ":" in duration and len(duration) <= 10:
                            video_durations.append(duration)
                    except NoSuchElementException:
                        video_durations.append("unknown")
                        
                except NoSuchElementException:
                    continue
                    
            self.video_urls = video_urls
            self.video_count = len(video_urls)
            self.video_thumbnails = video_thumbnails
            self.video_durations = video_durations
        except NoSuchElementException:
            self.video_urls = []
            self.video_count = 0
            self.video_thumbnails = []
            self.video_durations = []

    def _scrape_media_cards(self):
        try:
            media_cards = self.card.find_elements(
                "xpath", './/div[@data-testid="card.wrapper"]'
            )
            media_urls = []
            resolved_urls = []
            
            for card in media_cards:
                try:
                    links = card.find_elements("xpath", './/a[@href]')
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "t.co/" in href:
                            media_urls.append(href)
                            resolved_url = resolve_short_url(href)
                            resolved_urls.append(resolved_url)
                except:
                    continue
                    
            self.media_urls = media_urls
            self.resolved_media_urls = resolved_urls
            self.media_count = len(media_urls)
        except NoSuchElementException:
            self.media_urls = []
            self.resolved_media_urls = []
            self.media_count = 0

    def _scrape_poster_details(self):
        if not self.scrape_poster_details or not self.driver or not self.actions:
            return

        el_name = self.card.find_element(
            "xpath", './/div[@data-testid="User-Name"]//span'
        )

        ext_hover_card = False
        ext_user_id = False
        ext_following = False
        ext_followers = False
        hover_attempt = 0

        while (
            not ext_hover_card
            or not ext_user_id
            or not ext_following
            or not ext_followers
        ):
            try:
                self.actions.move_to_element(el_name).perform()

                hover_card = self.driver.find_element(
                    "xpath", '//div[@data-testid="hoverCardParent"]'
                )

                ext_hover_card = True

                while not ext_user_id:
                    try:
                        raw_user_id = hover_card.find_element(
                            "xpath",
                            '(.//div[contains(@data-testid, "-follow")]) | (.//div[contains(@data-testid, "-unfollow")])',
                        ).get_attribute("data-testid")

                        if raw_user_id == "":
                            self.poster_details["user_id"] = None
                        else:
                            self.poster_details["user_id"] = str(raw_user_id.split("-")[0])

                        ext_user_id = True
                    except NoSuchElementException:
                        continue
                    except StaleElementReferenceException:
                        self.error = True
                        return

                while not ext_following:
                    try:
                        following_cnt = hover_card.find_element(
                            "xpath", './/a[contains(@href, "/following")]//span'
                        ).text

                        if following_cnt == "":
                            following_cnt = None
                        self.poster_details["following_cnt"] = following_cnt

                        ext_following = True
                    except NoSuchElementException:
                        continue
                    except StaleElementReferenceException:
                        self.error = True
                        return

                while not ext_followers:
                    try:
                        followers_cnt = hover_card.find_element(
                            "xpath",
                            './/a[contains(@href, "/verified_followers")]//span',
                        ).text

                        if followers_cnt == "":
                            followers_cnt = None
                        self.poster_details["follower_cnt"] = followers_cnt

                        ext_followers = True
                    except NoSuchElementException:
                        continue
                    except StaleElementReferenceException:
                        self.error = True
                        return
            except NoSuchElementException:
                if hover_attempt == 3:
                    self.error = True
                    return
                hover_attempt += 1
                sleep(0.5)
                continue
            except StaleElementReferenceException:
                self.error = True
                return

        if ext_hover_card and ext_following and ext_followers:
            self.actions.reset_actions()

    def _build_tweet_dict(self):
        self.tweet = {
            "user": self.user,
            "handle": self.handle,
            "date_time": self.date_time,
            "content": self.content,
            "reply_cnt": self.reply_cnt,
            "retweet_cnt": self.retweet_cnt,
            "like_cnt": self.like_cnt,
            "analytics_cnt": self.analytics_cnt,
            "tags": self.tags,
            "mentions": self.mentions,
            "emojis": self.emojis,
            "tweet_link": self.tweet_link,
            "tweet_id": self.tweet_id,
            "quoted_tweet": self.quoted_tweet.quote if self.quoted_tweet else None,
            "image_urls": self.image_urls,
            "image_count": self.image_count,
            "video_urls": self.video_urls,
            "video_count": self.video_count,
            "video_thumbnails": self.video_thumbnails,
            "video_durations": self.video_durations,
            "media_urls": self.media_urls,
            "resolved_media_urls": self.resolved_media_urls,
            "media_count": self.media_count,
            "poster_details": self.poster_details
        }

    def _scrape(self):
        super()._scrape()
        self._scrape_quoted_tweet()
        
        # Media content
        self._scrape_images()
        self._scrape_videos()
        self._scrape_media_cards()
        
        # Detailed poster information (if requested)
        self._scrape_poster_details()
