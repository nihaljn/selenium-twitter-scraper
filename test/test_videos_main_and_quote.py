import json
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from _utils import Difference

# imports for the package
import sys
path_to_scraper_package = Path(__file__).parent.parent / "scraper"
sys.path.insert(0, str(path_to_scraper_package))

from tweet import Tweet


class TestSingleTweet:

    @pytest.fixture
    def main_tweet(self):
        """Fixture to create a Tweet object for the main tweet"""
        path = Path(__file__).parent / "data/processed/videos_main_and_quote.json"
        with open(path, "r") as f:
            data = json.load(f)
        return data


    @pytest.fixture
    def driver(self):
        options = Options()
        options.add_argument("--headless")  # Run without GUI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        try:
            html_path = Path(__file__).parent / "data/processed/videos_main_and_quote.html"
            # Convert to absolute file URL
            file_url = f"file://{html_path.absolute()}"
            driver.get(file_url)
        except:
            pytest.fail("Could not load HTML file")

        yield driver

        driver.quit()

    
    def _get_tweet_cards(self, driver):
        """Helper function to get tweet cards from the page"""
        try:
            return driver.find_elements(
                "xpath", '//article[@data-testid="tweet" and not(@disabled)]'
            )
        except:
            pytest.fail("Could not find tweet cards")

    
    def test_tweets_count(self, main_tweet, driver):
        """Test for the correct number of tweets in the page"""
        tweet_cards = self._get_tweet_cards(driver)
        assert len(tweet_cards) == 1, (
            f"Expected 1 tweet, but found {len(tweet_cards)}."
        )

    
    def test_main_tweet_props(self, main_tweet, driver):
        """Test if the first tweet (main tweet with a quote) has the right 
        properties including those for the quoted tweet"""
        tweet_card = self._get_tweet_cards(driver)[0] # get the first tweet
        assert tweet_card is not None, "Could not find the first tweet card"
        tweet = Tweet(tweet_card).tweet
        assert tweet is not None, "Could not create Tweet object"
        differences = []
        
        # main tweet
        for k in main_tweet:
            if k == "quoted_tweet":
                # skip quoted tweet for this test
                continue
            expected = main_tweet[k]
            actual = tweet.get(k)
            if expected != actual:
                differences.append(Difference(k, expected, actual))
        for k in tweet:
            if k not in main_tweet:
                differences.append(Difference(k, None, tweet[k]))
        
        assert len(differences) == 0, (
            f"Found {len(differences)} differing keys:\n" +
            "\n".join(str(d) for d in differences)
        )
