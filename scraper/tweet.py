from time import sleep

from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

from quote import Quote
from utils import resolve_short_url


class Tweet:
    def __init__(
        self,
        card: WebDriver,
        driver: WebDriver,
        actions: ActionChains,
        scrape_poster_details=False,
    ) -> None:
        self.card = card
        self.error = False
        self.tweet = None
        self.poster_details = {}

        try:
            self.user = card.find_element(
                "xpath", './/div[@data-testid="User-Name"]//span'
            ).text
        except NoSuchElementException:
            self.error = True
            self.user = "skip"

        try:
            self.handle = card.find_element(
                "xpath", './/span[contains(text(), "@")]'
            ).text
        except NoSuchElementException:
            self.error = True
            self.handle = "skip"

        try:
            self.date_time = card.find_element("xpath", ".//time").get_attribute(
                "datetime"
            )

            if self.date_time is not None:
                self.is_ad = False
        except NoSuchElementException:
            self.is_ad = True
            self.error = True
            self.date_time = "skip"

        if self.error:
            return

        try:
            card.find_element(
                "xpath", './/*[local-name()="svg" and @data-testid="icon-verified"]'
            )

            self.poster_details["verified"] = True
        except NoSuchElementException:
            self.poster_details["verified"] = False

        self.content = ""
        contents = card.find_elements(
            "xpath",
            '(.//div[@data-testid="tweetText"])[1]/span | (.//div[@data-testid="tweetText"])[1]/a',
        )

        for index, content in enumerate(contents):
            self.content += content.text

        try:
            self.reply_cnt = card.find_element(
                "xpath", './/button[@data-testid="reply"]//span'
            ).text

            if self.reply_cnt == "":
                self.reply_cnt = "0"
        except NoSuchElementException:
            self.reply_cnt = "0"

        try:
            self.retweet_cnt = card.find_element(
                "xpath", './/button[@data-testid="retweet"]//span'
            ).text

            if self.retweet_cnt == "":
                self.retweet_cnt = "0"
        except NoSuchElementException:
            self.retweet_cnt = "0"

        try:
            self.like_cnt = card.find_element(
                "xpath", './/button[@data-testid="like"]//span'
            ).text

            if self.like_cnt == "":
                self.like_cnt = "0"
        except NoSuchElementException:
            self.like_cnt = "0"

        try:
            self.analytics_cnt = card.find_element(
                "xpath", './/a[contains(@href, "/analytics")]//span'
            ).text

            if self.analytics_cnt == "":
                self.analytics_cnt = "0"
        except NoSuchElementException:
            self.analytics_cnt = "0"

        try:
            self.tags = card.find_elements(
                "xpath",
                './/a[contains(@href, "src=hashtag_click")]',
            )

            self.tags = [tag.text for tag in self.tags]
        except NoSuchElementException:
            self.tags = []

        try:
            self.mentions = card.find_elements(
                "xpath",
                '(.//div[@data-testid="tweetText"])[1]//a[contains(text(), "@")]',
            )

            self.mentions = [mention.text for mention in self.mentions]
        except NoSuchElementException:
            self.mentions = []

        try:
            raw_emojis = card.find_elements(
                "xpath",
                '(.//div[@data-testid="tweetText"])[1]/img[contains(@src, "emoji")]',
            )

            self.emojis = [
                emoji.get_attribute("alt").encode("unicode-escape").decode("ASCII")
                for emoji in raw_emojis
            ]
        except NoSuchElementException:
            self.emojis = []

        try:
            self.poster_details["profile_img"] = card.find_element(
                "xpath", './/div[@data-testid="Tweet-User-Avatar"]//img'
            ).get_attribute("src")
        except NoSuchElementException:
            self.poster_details["profile_img"] = None

        try:
            self.tweet_link = self.card.find_element(
                "xpath",
                ".//a[contains(@href, '/status/')]",
            ).get_attribute("href")
            self.tweet_id = str(self.tweet_link.split("/")[-1])
        except NoSuchElementException:
            self.tweet_link = ""
            self.tweet_id = ""

        try:
            images = self.card.find_elements(
                "xpath", './/div[@data-testid="tweetPhoto"]//img'
            )
            image_urls = []
            for img in images:
                try:
                    img_src = img.get_attribute('src')
                    if img_src:
                        image_urls.append(img_src)
                except:
                    continue
            self.image_urls = image_urls
            self.image_count = len(image_urls)
        except NoSuchElementException:
            self.image_urls = []
            self.image_count = 0

        # Extract video data
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

        # Extract media card URLs (t.co links)
        try:
            media_cards = self.card.find_elements(
                "xpath", './/div[@data-testid="card.wrapper"]'
            )
            media_urls = []
            resolved_urls = []
            
            for card in media_cards:
                try:
                    # Look for links in the media card
                    links = card.find_elements("xpath", './/a[@href]')
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "t.co/" in href:
                            media_urls.append(href)
                            # Resolve the short URL
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

        # Check for quoted tweet
        try:
            quote_sections = self.card.find_elements(
                "xpath", './/div[contains(@aria-labelledby, "id__")]'
            )
            
            self.quoted_tweet = None
            for section in quote_sections:
                try:
                    # Check if this section contains "Quote" label
                    section.find_element("xpath", './/span[text()="Quote"]')
                    # Found a quote section, create Quote object
                    quote = Quote(section)
                    if not quote.error:
                        self.quoted_tweet = quote
                    break
                except NoSuchElementException:
                    continue
                    
            if self.quoted_tweet is None:
                self.has_quote = False
            else:
                self.has_quote = True
                
        except NoSuchElementException:
            self.quoted_tweet = None
            self.has_quote = False

        if scrape_poster_details:

            el_name = card.find_element(
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
                    actions.move_to_element(el_name).perform()

                    hover_card = driver.find_element(
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
                        self.error
                        return
                    hover_attempt += 1
                    sleep(0.5)
                    continue
                except StaleElementReferenceException:
                    self.error = True
                    return

            if ext_hover_card and ext_following and ext_followers:
                actions.reset_actions()

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
            "video_urls": self.video_urls,
            "video_thumbnails": self.video_thumbnails,
            "video_durations": self.video_durations,
            "media_urls": self.media_urls,
            "resolved_media_urls": self.resolved_media_urls,
            "media_count": self.media_count,
            "poster_details": self.poster_details
        }
