from atproto import AsyncFirehoseSubscribeReposClient, parse_subscribe_repos_message, models, CAR, firehose_models, AtUri, Client
from datetime import datetime
from matcher import Matcher
import asyncio

_INTERESTED_RECORDS = {
        models.ids.AppBskyFeedPost: models.AppBskyFeedPost,
}

class FirehoseManager:
    def __init__(self):
        self.firehose_client = None
        self.bsky_client = Client()
        self.logged_in = False
        self.keywords = set()
        self.match_mode = 'OR'
        self.stats = {
            'posts_found': 0,
            'start_time': None,
            'end_time': None,
        }

    def login(self, handle, password):
        self.bsky_client.login(handle, password)
        self.logged_in = True

    async def start(self):
        self.stats['start_time'] = datetime.now()
        self.stats['posts_found'] = 0
        self.stats['end_time'] = None
        self.firehose_client = AsyncFirehoseSubscribeReposClient()
        await self.firehose_client.start(self.message_handler)

    async def stop(self):
        if self.firehose_client:
            self.stats['end_time'] = datetime.now()
            try:
                await asyncio.shield(self.firehose_client.stop())
            except Exception as e:
                print(f'Error stopping firehose: {e}')
            finally:
                self.firehose_client = None

    def get_runtime(self):
        if not self.stats['start_time']:
            return None
        end_time = self.stats['end_time'] or datetime.now()
        return end_time - self.stats['start_time']

    def get_posts_found(self):
        return self.stats['posts_found']

    def get_posts(self, commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> list:
        posts = list()

        for op in commit.ops:
            uri = AtUri.from_str(f'at://{commit.repo}/{op.path}')
            car = CAR.from_bytes(commit.blocks)

            if op.action == 'create':
                if not op.cid:
                    continue
                create_info = {'uri': str(uri), 'cid': str(op.cid), 'author': commit.repo}

                record_raw_data = car.blocks.get(op.cid)
                if not record_raw_data:
                    continue

                record = models.get_or_create(record_raw_data, strict=False)
                record_type = _INTERESTED_RECORDS.get(uri.collection)
                if record_type and models.is_record_type(record, record_type):
                    posts.append({'record': record, **create_info})
        return posts

    async def message_handler(self, message: firehose_models.MessageFrame) -> None:
        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return
        if not commit.blocks:
            return

        posts = self.get_posts(commit)
        for post in posts:
            author_did = post['author']
            if self.logged_in:
                try:
                    profile = self.bsky_client.app.bsky.actor.get_profile({'actor': author_did})
                    author_handle = profile.handle
                except Exception as e:
                    author_handle = author_did
            else:
                author_handle = author_did
            
            record = post['record']
            display_post = Matcher.matches_keywords(
                record.text,
                self.keywords,
                self.match_mode)

            if display_post:
                self.stats['posts_found'] += 1
                inlined_text = record.text.replace('\n', ' ')
                print(f'[{author_handle}]: {inlined_text}')
