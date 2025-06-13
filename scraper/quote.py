from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from utils import resolve_short_url


class Quote:
    def __init__(self, quote_element: WebElement) -> None:
        self.quote_element = quote_element
        self.error = False
        self.quote = None
        self.poster_details = {}

        # Check if this is actually a quote by looking for "Quote" label
        try:
            quote_element.find_element("xpath", './/span[text()="Quote"]')
        except NoSuchElementException:
            self.error = True
            return

        # Extract user information
        try:
            self.user = quote_element.find_element(
                "xpath", './/div[@data-testid="User-Name"]//span[not(contains(text(), "@"))]'
            ).text
        except NoSuchElementException:
            self.error = True
            self.user = "skip"

        try:
            self.handle = quote_element.find_element(
                "xpath", './/div[@data-testid="User-Name"]//span[contains(text(), "@")]'
            ).text
        except NoSuchElementException:
            self.error = True
            self.handle = "skip"

        try:
            self.date_time = quote_element.find_element("xpath", ".//time").get_attribute(
                "datetime"
            )
        except NoSuchElementException:
            self.error = True
            self.date_time = "skip"

        if self.error:
            return

        # Check if user is verified
        try:
            quote_element.find_element(
                "xpath", './/*[local-name()="svg" and @data-testid="icon-verified"]'
            )
            self.poster_details["verified"] = True
        except NoSuchElementException:
            self.poster_details["verified"] = False

        # Extract content
        self.content = ""
        try:
            contents = quote_element.find_elements(
                "xpath",
                './/div[@data-testid="tweetText"]/span | .//div[@data-testid="tweetText"]/a',
            )
            for content in contents:
                self.content += content.text
        except NoSuchElementException:
            self.content = ""

        # Extract hashtags
        try:
            self.tags = quote_element.find_elements(
                "xpath",
                './/a[contains(@href, "src=hashtag_click")]',
            )
            self.tags = [tag.text for tag in self.tags]
        except NoSuchElementException:
            self.tags = []

        # Extract mentions
        try:
            self.mentions = quote_element.find_elements(
                "xpath",
                './/div[@data-testid="tweetText"]//a[contains(text(), "@")]',
            )
            self.mentions = [mention.text for mention in self.mentions]
        except NoSuchElementException:
            self.mentions = []

        # Extract emojis
        try:
            raw_emojis = quote_element.find_elements(
                "xpath",
                './/div[@data-testid="tweetText"]/img[contains(@src, "emoji")]',
            )
            self.emojis = [
                emoji.get_attribute("alt").encode("unicode-escape").decode("ASCII")
                for emoji in raw_emojis
            ]
        except NoSuchElementException:
            self.emojis = []

        # Extract profile image
        try:
            # Look for user avatar in the quote
            avatar_containers = quote_element.find_elements(
                "xpath", './/div[contains(@data-testid, "UserAvatar-Container-")]'
            )
            if avatar_containers:
                self.poster_details["profile_img"] = avatar_containers[0].find_element(
                    "xpath", ".//img"
                ).get_attribute("src")
            else:
                self.poster_details["profile_img"] = None
        except NoSuchElementException:
            self.poster_details["profile_img"] = None

        # Extract images from quoted tweet
        try:
            images = quote_element.find_elements(
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

        # Extract video data from quoted tweet
        try:
            video_players = quote_element.find_elements(
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
            media_cards = quote_element.find_elements(
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

        # Try to extract quoted tweet ID from any links
        try:
            status_links = quote_element.find_elements(
                "xpath", ".//a[contains(@href, '/status/')]"
            )
            if status_links:
                self.tweet_link = status_links[0].get_attribute("href")
                self.tweet_id = str(self.tweet_link.split("/")[-1])
            else:
                self.tweet_link = ""
                self.tweet_id = ""
        except NoSuchElementException:
            self.tweet_link = ""
            self.tweet_id = ""

        # Create the quote tuple (similar to Tweet pattern)
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
            "media_urls": self.media_urls,
            "resolved_media_urls": self.resolved_media_urls,
            "media_count": self.media_count,
            "poster_details": self.poster_details
        }