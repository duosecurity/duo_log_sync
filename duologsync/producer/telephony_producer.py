from duologsync.duo_log_sync_base import LogSyncBase
import asyncio
import functools
import logging
from datetime import datetime, timedelta

class TelephonyProducer(LogSyncBase):

    async def telephony_producer(self):
        """
        This class reads data from telephony endpoint at polling duration
        specified by the user. Next offset is recorded from fetched records
        which is used for making next request and achieve pagination. Offset
        information is also recorded to allowing checkpointing and recovery
        from crash.
        """
        mintime = datetime.utcnow() - timedelta(days=self.config.get('logs').
                                                get('polling').get('daysinpast'))
        mintime = int(mintime.timestamp())
        polling_duration = max(self.config.get('logs').get('polling').get(
            'duration') * 60, 120)

        while True:
            await asyncio.sleep(polling_duration)
            mintime = self.last_offset_read.get('telephony_last_fetched', mintime)
            telephony_logs = await self.loop.run_in_executor(self._executor,
                                                             functools.partial(self.admin_api.get_telephony_log, mintime=mintime))
            if not telephony_logs:
                continue
            logging.info("Adding {} telephony logs to queue...".format(len(telephony_logs)))
            await self.telephonylog_queue.put(telephony_logs)
            logging.info("Added {} telephony logs to queue...".format(len(telephony_logs)))
            self.last_offset_read['telephony_last_fetched'] = telephony_logs[-1]['timestamp'] + 1
