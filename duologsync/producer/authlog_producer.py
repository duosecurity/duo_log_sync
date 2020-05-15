import asyncio
import functools
import logging
from datetime import datetime, timedelta

from duologsync.duo_log_sync_base import LogSyncBase


class AuthlogProducer(LogSyncBase):

    async def auth_producer(self):
        """
        This class reads data from authlog endpoint at polling duration
        specified by the user. Next offset is recorded from fetched records
        which is used for making next request and achieve pagination. Offset
        information is also recorded to allowing checkpointing and recovery
        from crash.
        """
        mintime = datetime.utcnow() - timedelta(days=self.config.get('logs').
                                                get('polling').get(
            'daysinpast'))
        mintime = int(mintime.timestamp()) * 1000
        polling_duration = self.config.get('logs').get('polling').get('duration') * 60
        while True:
            await asyncio.sleep(polling_duration)
            logging.info("Getting data from auth endpoint after {} seconds...".format(polling_duration))
            next_offset = self.last_offset_read.get('auth_last_fetched', None)
            if not next_offset:
                authlogs = await self.loop.run_in_executor(self._executor,
                                                       functools.partial(self.admin_api.get_authentication_log, api_version=2, mintime=mintime, sort='ts:asc', limit='1000'))
            else:
                authlogs = await self.loop.run_in_executor(self._executor,
                                                       functools.partial(self.admin_api.get_authentication_log, api_version=2, mintime=mintime, next_offset=next_offset, sort='ts:asc', limit='1000'))
            if len(authlogs['authlogs']) == 0:
                continue

            logging.info("Adding {} auth logs to queue...".format(len(authlogs['authlogs'])))
            await self.authlog_queue.put(authlogs['authlogs'])
            logging.info("Added {} auth logs to queue...".format(len(authlogs['authlogs'])))
            self.last_offset_read['auth_last_fetched'] = authlogs['metadata']['next_offset']
