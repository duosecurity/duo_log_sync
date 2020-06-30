import functools

from duologsync.producer.producer import Producer

class AuthlogProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Authentication logs
    """

    def __init__(self, config, last_offset_read, log_queue, inherited_self):
        super().__init__(config, last_offset_read, log_queue, inherited_self)

        self.log_type = 'auth'

    async def _call_log_api(self, mintime):
        """
        Make a call to the authentication log endpoint and return the result of
        that API call

        @param mintime  The oldest timestamp (in seconds) acceptable for a new
                        administrator log

        @return the result of a call to the authentication log API endpoint
        """

        # For the auth log call, mintime must be in milliseconds, not seconds
        mintime *= Producer.MILLISECONDS_PER_SECOND
        next_offset = self.last_offset_read.get('auth_last_fetched', None)

        # get_authentication_log is a high latency call which will block the
        # event loop. Thus it is run in an executor - a dedicated thread
        # pool - which allows for asyncio to do other work while this call is
        # being made
        authlog_api_result = await self.event_loop.run_in_executor(
            self.executor,
            functools.partial(
                self.admin.get_authentication_log,
                api_version=2,
                mintime=mintime,
                next_offset=next_offset,
                sort='ts:asc',
                limit='1000'
            )
        )

        return authlog_api_result

    @staticmethod
    def _get_logs(api_result):
        """
        Retrieve authentication logs from the API result of a call to the
        authentication log endpoint

        @param api_result   The result of an API call to the authentication
                            log endpoint

        @return authentication logs from the result of an API call to the
                authentication log endpoint
        """

        return api_result['authlogs']

    @staticmethod
    def _get_last_offset_read(api_result):
        """
        Return the next_offset given by the result of a call to the
        authentication log API endpoint

        @param api_result   The result of an API call to the authentication
                            log endpoint

        @return the next_offset given by the result of a call to the
                authentication log API endpoint
        """

        return api_result['metadata']['next_offset']
