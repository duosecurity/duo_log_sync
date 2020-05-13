import asyncio
import functools
import logging

from datetime import datetime, timedelta
from duologsync.duo_log_sync_base import LogSyncBase


class AdminactionProducer(LogSyncBase):
    """
    This class reads data from admin endpoint at polling duration
    specified by the user. Next offset is recorded from fetched records
    which is used for making next request and achieve pagination. Offset
    information is also recorded to allowing checkpointing and recovery
    from crash.
    """
    async def adminaction_producer(self):
        mintime = datetime.utcnow() - timedelta(
            days=self.config.get('logs').
                get('polling').get('daysinpast'))
        mintime = int(mintime.timestamp())
        polling_duration = self.config.get('logs').get('polling').get(
            'duration') * 60
        while True:
            await asyncio.sleep(polling_duration)
            mintime = self.last_offset_read.get('adminaction_last_fetched',
                                                mintime)
            adminaction_logs = await self.loop.run_in_executor(self._executor,
                                                  functools.partial(self.admin_api.get_administrator_log, mintime=mintime))
            if not adminaction_logs:
                continue
            logging.info("Adding {} adminaction logs to queue...".format(len(adminaction_logs)))
            await self.adminlog_queue.put(adminaction_logs)
            logging.info("Added {} adminaction logs to queue...".format(len(adminaction_logs)))
            self.last_offset_read['adminaction_last_fetched'] = adminaction_logs[-1]['timestamp'] + 1
