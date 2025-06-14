import argparse
import os
from pathlib import Path

from bs4 import BeautifulSoup


def extract_complete_tweets(
    input_file: str, 
    output_file: str,
    max_tweets: int = 1000000
):
    """Extract complete tweet HTML with all data-testids intact"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all tweet articles
    all_tweets = soup.find_all('article', {'data-testid': 'tweet'})
    tweets = all_tweets[:max_tweets]
    print(f"Found {len(all_tweets)} tweets - retained {len(tweets)} tweets")
    
    # Extract all CSS
    styles = ""
    for style in soup.find_all('style'):
        if style.string:
            styles += style.string + "\n"
    
    # Create HTML with complete tweets
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Twitter Test HTML</title>
    <style>
    {styles}
    </style>
</head>
<body>
    <div id="test-container">
"""
    
    # Add each complete tweet
    for i, tweet in enumerate(tweets):
        html += f'\n<!-- Tweet {i+1} -->\n'
        html += str(tweet)
        html += '\n'
    
    html += """
    </div>
</body>
</html>"""
    
    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Created {output_file} with {len(tweets)} complete tweets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract tweet data into simpler HTML for testing purposes")
    parser.add_argument("input_file_name", help="Input file name; should be present in the original/ directory")
    parser.add_argument("--max_tweets", type=int, default=1000000, help="Maximum number of tweets to extract")
    args = parser.parse_args()

    # check that the file is present in present dir / original
    test_data_path = Path(__file__).parent / "data"
    input_file = test_data_path / "original" / args.input_file_name
    if not input_file.exists():
        print(f"File {input_file} not found in original/ directory")
        exit(1)
    output_file = test_data_path / "processed" / args.input_file_name

    extract_complete_tweets(input_file, output_file, args.max_tweets)
