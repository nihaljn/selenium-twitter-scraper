from selenium.webdriver.remote.webelement import WebElement

from .card import Card


class Quote(Card):
    def __init__(self, quote_card: WebElement) -> None:
        super().__init__(quote_card)
        self.error = False
        self.quote = None
        self.poster_details = {}
        self._scrape()
        # Build final tweet dictionary
        self._build_tweet_dict()


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
            "videos": self.videos,
            "poster_details": self.poster_details
        }        
