import cmd
import asyncio
import threading
import getpass
from firehose_manager import FirehoseManager
from datetime import datetime

class KeywordPrompt(cmd.Cmd):
    intro = 'Welcome to the keyword firehose! Type help or ? to list commands.\n'
    prompt = 'keyword_firehose> '

    def __init__(self):
        super().__init__()
        self.firehose = FirehoseManager()
        self.firehose_task = None
        self.loop = asyncio.new_event_loop()
        self.bsky_login()

    def bsky_login(self):
        print('Login to bluesky')
        while True:
            try:
                handle = input('Enter your bluesky handle: ')
                app_password = getpass.getpass('Enter your app password: ')
                self.firehose.login(handle, app_password)
                del app_password
                print('Successfully logged in!')
                break
            except Exception as e:
                if hasattr(e, "response"):
                    print(f'Login failed: {e.response.content.message}')
                else:
                    print(f'Unexpected error {e}')
                    raise SystemExit(1)
                try:
                    retry = input("A login is required to display user handles. Proceed without login? (y/n): ")
                    if retry.lower() == 'y':
                        print('Proceeding without login.')
                        break
                except EOFError:
                    print('\nExiting')
                    raise SystemExit(0)

    def preloop(self):
        self.loop_thread = threading.Thread(
            target=lambda: self.loop.run_forever(),
            daemon=True
        )
        self.loop_thread.start()

    def do_add_keyword(self, line):
        """Add a keyword to the keyword set"""
        self.firehose.keywords.add(line)

    def do_start(self, arg):
        """Start the firehose"""
        if not self.firehose_task or self.firehose_task.done():
            self.firehose_task = asyncio.run_coroutine_threadsafe(
                self.firehose.start(),
                self.loop
            )
            print('Firehose started')
        else:
            print('Firehose is already running')

    def do_stop(self, arg):
        """Stop the firehose"""
        if self.firehose_task:
            async def stop_firehose():
                await self.firehose.stop()
                self.firehose_task.cancel()
                self.firehose_task = None

            future = asyncio.run_coroutine_threadsafe(stop_firehose(), self.loop)
            future.result()
            print('Firehose stopped')

    def do_add_keyword(self, line):
        """Add a keyword to the keyword set"""
        self.firehose.keywords.add(line)

    def do_remove_keyword(self, line):
        """Remove a keyword from the keyword set"""
        if line in self.firehose.keywords:
            self.firehose.keywords.remove(line)
            print(f'{line} removed!')
        else:
            print(f'{line} not in keywords!')

    def do_print_keywords(self, arg):
        """Display the keyword set"""
        print(self.firehose.keywords)

    def do_add_keyword(self, line):
        """Add a keyword to the keyword set"""
        self.firehose.keywords.add(line)

    def do_remove_keyword(self, line):
        """Remove a keyword from the keyword set"""
        if line in self.firehose.keywords:
            self.firehose.keywords.remove(line)
            print(f'{line} removed!')
        else:
            print(f'{line} not in keywords!')

    def do_print_keywords(self, arg):
        """Display the keyword set"""
        print(self.firehose.keywords)

    def do_quit(self, arg):
        """Exit the prompt"""
        self.do_stop(arg)
        self.loop.call_soon_threadsafe(self.loop.stop)
        return True
    
    def do_exit(self, arg):
        """Exit the prompt"""
        return self.do_quit(arg)
    
    def do_EOF(self, arg):
        """Ctrl-D stops the firehose if its running, and exit the program if its not"""
        if self.firehose_task and not self.firehose_task.done():
            self.do_stop(arg)
            return False
        else:
            return self.do_quit(arg)

    def do_or_match(self, arg):
        """Default on startup. Display posts if any keyword is in the post"""
        self.firehose.match_mode = 'OR'

    def do_and_match(self, arg):
        """Display posts if all keywords are in the post"""
        self.firehose.match_mode = 'AND'

    def do_match_mode(self, arg):
        """Display the current match mode"""
        print(self.firehose.match_mode)

    def do_stats(self, arg):
        """Display statistics about the most recent firehose run"""

        runtime = self.firehose.get_runtime()

        if not runtime:
            return
        
        posts_found = self.firehose.get_posts_found()

        print(f'===Statistics===')
        print(f'Total posts found: {posts_found}')
        if runtime.total_seconds() > 1:
            print(f'Ran for: {str(runtime).split('.')[0]}')
        else:
            print(f'Ran for: {runtime}')
