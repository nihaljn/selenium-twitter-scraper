import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement


class Card:
    def __init__(self, card: WebElement):
        self.card = card

    def _scrape_user(self):
        try:
            self.user = self.card.find_element(
                "xpath", './/div[@data-testid="User-Name"]//span'
            ).text
        except NoSuchElementException:
            self.error = True
            self.user = "skip"

    def _scrape_handle(self):
        try:
            self.handle = self.card.find_element(
                "xpath", './/span[contains(text(), "@")]'
            ).text
        except NoSuchElementException:
            self.error = True
            self.handle = "skip"

    def _scrape_datetime(self):
        try:
            self.date_time = self.card.find_element("xpath", ".//time").get_attribute(
                "datetime"
            )
            if self.date_time is not None:
                self.is_ad = False
        except NoSuchElementException:
            self.is_ad = True
            self.error = True
            self.date_time = "skip"

    def _scrape_verification(self):
        try:
            self.card.find_element(
                "xpath", './/*[local-name()="svg" and @data-testid="icon-verified"]'
            )
            self.poster_details["verified"] = True
        except NoSuchElementException:
            self.poster_details["verified"] = False

    def _scrape_content(self):
        self.content = ""
        try:
            tweet_text_div = self.card.find_element("xpath", './/div[@data-testid="tweetText"]')

            elements = tweet_text_div.find_elements("xpath", './span | ./img[@alt] | ./div')

            for element in elements:
                if element.tag_name == "img":
                    # emoji likely
                    self.content += element.get_attribute("alt")
                elif element.tag_name == "div":
                    # Handle different div cases
                    try:
                        # Case 1: Div containing a link
                        link = element.find_element("xpath", './/a')
                        self.content += link.text
                    except NoSuchElementException:
                        # Case 2: Add other div cases here as needed
                        # For now, raise exception for unknown div types
                        raise NotImplementedError(f"Unknown div type in tweet content: {element.get_attribute('outerHTML')[:100]}...")
                else:
                    # Handle spans
                    self.content += element.text

        except NoSuchElementException:
            self.content = ""

    def _scrape_engagement_counts(self):
        # Reply count
        try:
            self.reply_cnt = self.card.find_element(
                "xpath", './/button[@data-testid="reply"]//span'
            ).text
            if self.reply_cnt == "":
                self.reply_cnt = "0"
        except NoSuchElementException:
            self.reply_cnt = "0"

        # Retweet count
        try:
            self.retweet_cnt = self.card.find_element(
                "xpath", './/button[@data-testid="retweet"]//span'
            ).text
            if self.retweet_cnt == "":
                self.retweet_cnt = "0"
        except NoSuchElementException:
            self.retweet_cnt = "0"

        # Like count
        try:
            self.like_cnt = self.card.find_element(
                "xpath", './/button[@data-testid="like"]//span'
            ).text
            if self.like_cnt == "":
                self.like_cnt = "0"
        except NoSuchElementException:
            self.like_cnt = "0"

        # Analytics count
        try:
            self.analytics_cnt = self.card.find_element(
                "xpath", './/a[contains(@href, "/analytics")]//span'
            ).text
            if self.analytics_cnt == "":
                self.analytics_cnt = "0"
        except NoSuchElementException:
            self.analytics_cnt = "0"

    def _scrape_tags_mentions_emojis(self):
        # Tags
        try:
            self.tags = self.card.find_elements(
                "xpath", './/a[contains(@href, "src=hashtag_click")]',
            )
            self.tags = [tag.text for tag in self.tags]
        except NoSuchElementException:
            self.tags = []

        # Mentions
        try:
            self.mentions = self.card.find_elements(
                "xpath", '(.//div[@data-testid="tweetText"])[1]//a[contains(text(), "@")]',
            )
            self.mentions = [mention.text for mention in self.mentions]
        except NoSuchElementException:
            self.mentions = []

        # Emojis
        try:
            raw_emojis = self.card.find_elements(
                "xpath", '(.//div[@data-testid="tweetText"])[1]/img[contains(@src, "emoji")]',
            )
            self.emojis = [
                emoji.get_attribute("alt").encode("unicode-escape").decode("ASCII")
                for emoji in raw_emojis
            ]
        except NoSuchElementException:
            self.emojis = []

    def _scrape_profile_image(self):
        try:
            self.poster_details["profile_img"] = self.card.find_element(
                "xpath", './/div[@data-testid="Tweet-User-Avatar"]//img'
            ).get_attribute("src")
        except NoSuchElementException:
            self.poster_details["profile_img"] = None

    def _scrape_tweet_link(self):
      try:
          tweet_link = self.card.find_element(
              "xpath", ".//a[contains(@href, '/status/')]",
          ).get_attribute("href")

          pattern = r".*/status/(\d+)"
          match = re.search(pattern, tweet_link)
        
          if match:
              self.tweet_link = match.group(0)
              self.tweet_id = match.group(1)  # Extract the captured group (the number)
          else:
              self.tweet_link = ""
              self.tweet_id = ""
      except NoSuchElementException:
          self.tweet_link = ""
          self.tweet_id = ""

    def _extract_video_info(self, video_player: WebElement) -> dict:
        video = {
            "video_id": "unknown",
            "source": "unknown",
            "duration": "unknown",
            "thumbnail": "unknown",
        }
        try:
            # Get video blob URL
            video_source = video_player.find_element("xpath", './/video//source')
            video_url = video_source.get_attribute("src")
            video_id = video_url.split("/")[-1]
            
            # Get video thumbnail/poster
            video_element = video_player.find_element("xpath", './/video')
            thumbnail = video_element.get_attribute("poster")
            
            # Get video duration
            try:
                duration_element = video_player.find_element(
                    "xpath", './/span[contains(text(), ":")]'
                )
                duration = duration_element.text.strip()
            except:
                duration = "unknown"

            # Store
            video["video_id"] = video_id
            video["source"] = video_url
            video["duration"] = duration
            video["thumbnail"] = thumbnail
        except NoSuchElementException as e:
            print("Warning (skipping) - ", e)
            pass
        return video


    def _scrape_videos(self):
        # Extract video data from quoted tweet
        try:
            video_players = self.card.find_elements(
                "xpath", './/div[@data-testid="videoPlayer"]'
            )
            videos = []
            for video_player in video_players:
                try:
                    video = self._extract_video_info(video_player)
                    videos.append(video)
                except NoSuchElementException:
                    continue
            self.videos = videos
        except NoSuchElementException:
            self.videos = []


    def _scrape_images(self):

        # Extract images from quoted tweet
        try:
            images = self.card.find_elements(
                "xpath", './/div[@data-testid="tweetPhoto"]//img'
            )
            image_urls = []
            video_thumbnails = set(
                v["thumbnail"] for v in self.videos 
                if v.get("thumbnail") not in [None, "unknown"]
            )
            for img in images:
                try:
                    img_src = img.get_attribute('src')
                    if img_src:
                        if 'name=small' in img_src:
                            # Convert to higher quality
                            img_src = img_src.replace('name=small', 'name=large')
                        if img_src not in video_thumbnails:
                            image_urls.append(img_src)
                except:
                    continue
            self.image_urls = image_urls
        except NoSuchElementException:
            self.image_urls = []


    def _scrape(self, scrape_media: bool = True):
        # Basic tweet information
        self._scrape_user()
        self._scrape_handle()
        self._scrape_datetime()

        if self.error:
            return

        # Content and metadata
        self._scrape_verification()
        self._scrape_content()
        self._scrape_engagement_counts()
        self._scrape_tags_mentions_emojis()
        self._scrape_profile_image()
        self._scrape_tweet_link()

        # Media content
        if scrape_media:
            self._scrape_videos()
            self._scrape_images()
