# Keyword Firehose
This is a small CLI application that allows you to filter the bluesky firehose 

## Usage
1. Run with ./venv/bin/python3 main.py
2. Enter valid Bluesky credentials when prompted
3. Add or remove keywords with add_keyword {arg} or remove_keyword {arg}
4. Start or stop the firehose with start or stop

You can also switch between displaying posts with any keyword in them (default),
or displaying posts with all keywords in them by using or_match and and_match

EOF will stop the firehose if its running, and exit the program if its not
