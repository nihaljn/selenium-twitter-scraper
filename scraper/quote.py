from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from card import Card


class Quote(Card):
    def __init__(self, quote_card: WebElement) -> None:
        super().__init__(quote_card)
        self.error = False
        self.quote = None
        self.poster_details = {}
        self._scrape()
        # Build final tweet dictionary
        self._build_tweet_dict()

    def _scrape_images(self):

        # Extract images from quoted tweet
        try:
            images = self.card.find_elements(
                "xpath", './/div[@data-testid="tweetPhoto"]//img'
            )
            image_urls = []
            for img in images:
                try:
                    img_src = img.get_attribute('src')
                    if img_src:
                        # Convert to higher quality
                        if 'name=small' in img_src:
                            img_src = img_src.replace('name=small', 'name=large')
                        image_urls.append(img_src)
                except:
                    continue
            self.image_urls = image_urls
            self.image_count = len(image_urls)
        except NoSuchElementException:
            self.image_urls = []
            self.image_count = 0

    def _scrape_videos(self):

        # Extract video data from quoted tweet
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

    def _build_tweet_dict(self):

        # Create the quote tuple (similar to Tweet pattern)
        # import ipdb; ipdb.set_trace()
        self.quote = {
            "user": self.user,
            "handle": self.handle,
            "date_time": self.date_time,
            "content": self.content,
            "tags": self.tags,
            "mentions": self.mentions,
            "emojis": self.emojis,
            "tweet_link": self.tweet_link,
            "tweet_id": self.tweet_id,
            "image_urls": self.image_urls,
            "video_urls": self.video_urls,
            "video_thumbnails": self.video_thumbnails,
            "video_durations": self.video_durations,
            "poster_details": self.poster_details
        }

    def _scrape(self):
        super()._scrape()
        
        # Media content
        self._scrape_images()
        self._scrape_videos()
