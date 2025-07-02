import os
import sys
import argparse
import getpass
from twitter_scraper import Twitter_Scraper

try:
    from dotenv import load_dotenv

    print("Loading .env file")
    load_dotenv()
    print("Loaded .env file\n")
except Exception as e:
    print(f"Error loading .env file: {e}")
    sys.exit(1)


def main():
    try:
        parser = argparse.ArgumentParser(
            add_help=True,
            usage="python scraper [option] ... [arg] ...",
            description="Twitter Scraper is a tool that allows you to scrape tweets from twitter without using Twitter's API.",
        )

        try:
            parser.add_argument(
                "mode",
                type=str,
                default="timeline",
                help="Scrape mode. [timeline/conversation/tweet]",
                choices=["timeline", "conversation", "tweet"],
            )

            parser.add_argument(
                "--mail",
                type=str,
                default=os.getenv("TWITTER_MAIL"),
                help="Your Twitter mail.",
            )

            parser.add_argument(
                "--user",
                type=str,
                default=os.getenv("TWITTER_USERNAME"),
                help="Your Twitter username.",
            )

            parser.add_argument(
                "--password",
                type=str,
                default=os.getenv("TWITTER_PASSWORD"),
                help="Your Twitter password.",
            )

            parser.add_argument(
                "--headlessState",
                type=str,
                default=os.getenv("HEADLESS"),
                help="Headless mode? [yes/no]"
            )
        except Exception as e:
            print(f"Error retrieving environment variables: {e}")
            sys.exit(1)

        parser.add_argument(
            "-t",
            "--tweets",
            type=int,
            default=50,
            help="Number of tweets to scrape (default: 50)",
        )

        parser.add_argument(
            "-u",
            "--username",
            type=str,
            default=None,
            help="Twitter username. Scrape tweets from a user's profile.",
        )

        parser.add_argument(
            "-ht",
            "--hashtag",
            type=str,
            default=None,
            help="Twitter hashtag. Scrape tweets from a hashtag.",
        )

        parser.add_argument(
            "--bookmarks",
            action='store_true',
            help="Twitter bookmarks. Scrape tweets from your bookmarks.",
        )

        parser.add_argument(
            "-ntl",
            "--no_tweets_limit",
            nargs='?',
            default=False,
            help="Set no limit to the number of tweets to scrape (will scrap until no more tweets are available).",
        )

        parser.add_argument(
            "-l",
            "--list",
            type=str,
            default=None,
            help="List ID. Scrape tweets from a list.",
        )

        parser.add_argument(
            "-q",
            "--query",
            type=str,
            default=None,
            help="Twitter query or search. Scrape tweets from a query or search.",
        )

        parser.add_argument(
            "-a",
            "--add",
            type=str,
            default="",
            help="Additional data to scrape and save in the .csv file.",
        )

        parser.add_argument(
            "--latest",
            action="store_true",
            help="Scrape latest tweets",
        )

        parser.add_argument(
            "--top",
            action="store_true",
            help="Scrape top tweets",
        )

        parser.add_argument(
            "--save_mode",
            choices=["csv", "jsonl"],
            help="Save mode: current choices are csv and jsonl",
            default="csv",
            type=str.lower
        )

        parser.add_argument(
            "--url",
            type=str,
            default=None,
            help="URL to specific tweet or conversation to scrape",
        )

        parser.add_argument(
            "--browser",
            type=str,
            default="firefox",
            help="Browser to use for scraping. [chrome/firefox]",
            choices=["chrome", "firefox"],
        )

        args = parser.parse_args()

        USER_MAIL = args.mail
        USER_UNAME = args.user
        USER_PASSWORD = args.password
        HEADLESS_MODE= args.headlessState

        if USER_UNAME is None:
            USER_UNAME = input("Twitter Username: ")

        if USER_PASSWORD is None:
            USER_PASSWORD = getpass.getpass("Enter Password: ")

        if HEADLESS_MODE is None:
            HEADLESS_MODE - str(input("Headless?[Yes/No]")).lower()

        print()

        tweet_type_args = []

        if args.username is not None:
            tweet_type_args.append(args.username)
        if args.hashtag is not None:
            tweet_type_args.append(args.hashtag)
        if args.list is not None:
            tweet_type_args.append(args.list)
        if args.query is not None:
            tweet_type_args.append(args.query)
        if args.bookmarks is not False:
            tweet_type_args.append(args.query)

        additional_data: list = args.add.split(",")

        if len(tweet_type_args) > 1:
            print("Please specify only one of --username, --hashtag, --bookmarks, or --query.")
            sys.exit(1)

        if args.latest and args.top:
            print("Please specify either --latest or --top. Not both.")
            sys.exit(1)

        if args.mode == "conversation" and args.url is None:
            print("Please specify a conversation URL to scrape.")
            sys.exit(1)

        if USER_UNAME is not None and USER_PASSWORD is not None:
            scraper = Twitter_Scraper(
                username=USER_UNAME,
                password=USER_PASSWORD,
                headlessState=HEADLESS_MODE,
                browser=args.browser,
            )
            scraper.login()
            if args.mode == "timeline":
                data = scraper.scrape_tweets(
                    max_tweets=args.tweets,
                    no_tweets_limit= args.no_tweets_limit if args.no_tweets_limit is not None else True,
                    mode=args.mode,
                    scrape_poster_details="pd" in additional_data,
                )
            elif args.mode == "conversation":
                data = scraper.scrape_tweets(
                    max_tweets=args.tweets,
                    no_tweets_limit= args.no_tweets_limit if args.no_tweets_limit is not None else True,
                    mode=args.mode,
                    scrape_poster_details="pd" in additional_data,
                    url=args.url
                )
            else:
                raise ValueError("Invalid mode:", args.mode)
            if args.save_mode == "csv":
                scraper.save_to_csv(data)
            elif args.save_mode == "jsonl":
                scraper.save_to_jsonl(data)
            else:
                raise ValueError("Invalid save mode:", args.save_mode)
            if not scraper.interrupted:
                scraper.close()
        else:
            print(
                "Missing Twitter username or password environment variables. Please check your .env file."
            )
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nScript Interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    sys.exit(1)


if __name__ == "__main__":
    main()
