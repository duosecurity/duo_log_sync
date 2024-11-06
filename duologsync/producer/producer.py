"""
Definition of the Producer class
"""

import functools
import logging
from datetime import datetime
from socket import gaierror

import six

from duologsync.config import Config
from duologsync.program import Program, ProgramShutdownError
from duologsync.util import get_log_offset, restless_sleep, run_in_executor


class Producer:
    """
    Read data from a specific log endpoint via an API call at a polling
    duration that is user specified. The data is published to a queue which
    is only used for data of the same log type, and offset information is
    recorded to allow checkpointing and recovery from a crash.
    """

    def __init__(self, api_call, log_queue, log_type, account_id=None, url_path=None):
        self.api_call = api_call
        self.log_queue = log_queue
        self.log_type = log_type
        self.account_id = account_id
        self.log_offset = get_log_offset(
            self.log_type,
            Config.get_checkpointing_enabled(),
            Config.get_checkpoint_dir(),
            self.account_id,
        )
        self.url_path = url_path

    async def produce(self):
        """
        The main function of this class and subclasses. Runs a loop, sleeping
        for the polling duration then making an API call, consuming the logs
        from that API call and saving the offset of the latest log read.
        """

        # Exit when DuoLogSync is shutting down (due to error or Ctrl-C)
        while Program.is_running():
            shutdown_reason = None
            Program.log(
                f"{self.log_type} producer: fetching next logs after "
                f"{Config.get_api_timeout()} seconds",
                logging.INFO,
            )

            try:
                # Sleep for api_timeout amount of time, but check for program
                # shutdown every second
                await restless_sleep(Config.get_api_timeout())
                Program.log(
                    f"{self.log_type} producer: fetching logs from offset {self.log_offset or self.mintime}",
                    logging.INFO,
                )
                api_result = await self.call_log_api()

                if api_result:
                    formatted_logs = self.get_logs(api_result)
                    await self.add_logs_to_queue(formatted_logs)
                else:
                    Program.log(
                        f"{self.log_type} producer: no new logs available", logging.INFO
                    )

            # Incorrect api_hostname or proxy_server was provided
            # duo_client throws the same error if either the api_hostname or proxy_server is incorrect
            except (gaierror, OSError) as error:
                shutdown_reason = f"{self.log_type} producer: [{error}]"
                Program.log(
                    "DuoLogSync: check that the duoclient host and/or proxy_server provided in the config "
                    "file are correct"
                )

            # duo_client throws a RuntimeError if the ikey or skey is invalid
            except RuntimeError as runtime_error:
                shutdown_reason = self.handle_runtime_error_gracefully(runtime_error)

            # Shutdown hath been noticed and thus shutdown shall begin
            except ProgramShutdownError:
                break

            if shutdown_reason:
                Program.initiate_shutdown(shutdown_reason)

        # Unblock consumer but putting anything in the shared queue
        await self.log_queue.put([])
        Program.log(f"{self.log_type} producer: shutting down", logging.INFO)

    def handle_runtime_error_gracefully(self, runtime_error: RuntimeError):
        """
        Handle a runtime error gracefully by checking if the error is eligible for a retry.
        If it is, log the error and return None to indicate that the producer should retry.
        If it is not, log the error and return a string to indicate that the producer should shut down.
        """
        if self.eligible_for_retry(runtime_error):
            error_data = getattr(runtime_error, "data", None)
            error_code = error_data['code'] if error_data else None
            Program.log(
                f"{self.log_type} producer: retrying due to error: {runtime_error} error_code: {error_code}",
                logging.WARNING,
            )

            return None

        return f"{self.log_type} producer: [{runtime_error}]"

    @staticmethod
    def eligible_for_retry(runtime_error: RuntimeError):
        """
        Check if the runtime error is eligible for a retry based on the status code.
        See the Config.GRACEFUL_RETRY_STATUS_CODES for the list of status codes that is eligible for a retry.
        """
        http_error_code = getattr(runtime_error, "status", None)

        if http_error_code:
            for http_status_code in Config.GRACEFUL_RETRY_STATUS_CODES:
                if http_error_code == http_status_code:
                    return True

        return False

    async def add_logs_to_queue(self, logs):
        """
        If logs is not none, add them to this Writer's queue

        @param logs The logs to be added to the asyncio queue
        """

        # Important for recovery in the event of a crash
        self.log_offset = Producer.get_log_offset(
            logs, current_log_offset=self.log_offset, log_type=self.log_type
        )

        # Authlogs v2, Trust Monitor, Telephony, and Activity endpoint returns dict response
        if isinstance(logs, dict):
            if logs.get("authlogs", None) is not None:
                logs = logs["authlogs"]
            elif logs.get("events", None) is not None:
                logs = logs["events"]
            elif logs.get("items", None) is not None:
                logs = logs["items"]

        if len(logs):
            Program.log(
                f"{self.log_type} producer: adding {len(logs)} logs to the queue",
                logging.INFO,
            )

            await self.log_queue.put(logs)

            Program.log(
                f"{self.log_type} producer: successfully added logs to the queue",
                logging.INFO,
            )
        else:
            Program.log(
                f"{self.log_type} producer: no new logs to add to the queue",
                logging.INFO,
            )

    async def call_log_api(self):
        """
        Make a call to a log-specific API and return the API result. The default
        implementation given here will not suffice for every type of log API and
        so should be overridden by a child class when necessary.

        @return the result of the API call
        """

        if Config.account_is_msp():
            # Make an API call to retrieve authlog logs for MSP accounts
            parameters = {
                "mintime": six.ensure_str(str(self.log_offset)),
                "account_id": six.ensure_str(self.account_id),
            }

            api_result = await run_in_executor(
                functools.partial(
                    self.api_call, method="GET", path=self.url_path, params=parameters
                )
            )
        else:
            api_result = await run_in_executor(
                functools.partial(self.api_call, mintime=self.log_offset)
            )

        return api_result

    @staticmethod
    def get_logs(api_result):
        """
        Perform an action to retrieve logs from a log-specific api_result. The
        default implementation given here will not suffice for every type of
        log API and so should be overridden by a child class when necessary.

        @param api_result   The result of an API call

        @return the logs contained within api_result
        """

        # No need to rewrite this function if api_result is a container of logs
        return api_result

    @staticmethod
    def get_log_offset(log, current_log_offset=None, log_type=None):
        """
        Get offset information given an individual log.

        @param log  Individual log from which to get offset information

        @return the offset of the log
        """

        # In case of authlogs, dict is returned as response. So we check for that and record
        # information from metadata field. This is applicable for producer log offset
        # Elif loops are considered when offset is calculated for checkpointing. Here logs will be
        # of type dict. Authlog will have txid field in addition to timestamp field which can be
        # used for identification. Direct timestamp field cannot be used since it loses precision.
        # Hence calculating timestamp from isotimestamp field.
        if isinstance(log, dict):
            if log_type is not None and log_type == Config.AUTH:
                if (
                    log.get("authlogs")
                    and log.get("metadata", {}).get("next_offset") is not None
                ):
                    return log.get("metadata", {}).get("next_offset")

            if log_type is not None and log_type in [Config.ACTIVITY, Config.TELEPHONY]:
                # Telephony and Activity require a comma separated string of `timestamp,id` for
                # the next_offset parameter to the Admin API. Here we parse the
                # next_offset from an individual log. Called from the consumer logic.

                # Check if we're processing a response or an individual log
                if log.get("items") is None:
                    next_timestamp_to_poll_from = (
                        datetime.strptime(
                            log.get("ts", ""),
                            "%Y-%m-%dT%H:%M:%S.%f+00:00",
                        ).timestamp()
                        * 1000
                    )
                    id_field = "activity_id"
                    if log_type == Config.TELEPHONY:
                        id_field = "telephony_id"
                    log_id = log.get(id_field)
                    next_timestamp = int(next_timestamp_to_poll_from) + 1
                    return f"{next_timestamp},{log_id}"
                else:
                    if (log.get("metadata", {}) or {}).get("next_offset", None) is not None:
                        next_offset = log.get("metadata", {}).get("next_offset", None)
                        return next_offset

            if log_type is not None and log_type == Config.TRUST_MONITOR:
                # For the Trust Monitor API, once DLS paginates through and
                # transports all events within the supplied mintime and maxtime window,
                # we need to keep track of the last event's timestamp and
                # supply that as the new mintime so that we can continue to poll

                # Check if we're processing a response or an individual log
                if log.get("events") is None:
                    next_timestamp_to_poll_from = log.get("surfaced_timestamp", 0)
                    return int(next_timestamp_to_poll_from) + 1
                else:
                    if log.get("metadata", {}).get("next_offset") is not None:
                        return int(log.get("metadata", {}).get("next_offset", 0))
                    else:
                        events = log.get("events", {})
                        if events:
                            last_event = events[len(events) - 1]
                            next_timestamp_to_poll_from = last_event.get(
                                "surfaced"
                            ) or last_event.get("surfaced_timestamp")
                            return int(next_timestamp_to_poll_from) + 1

            if log.get("isotimestamp") and log.get("txid"):
                value = int(
                    (
                        datetime.strptime(
                            six.ensure_str(log.get("isotimestamp", "")),
                            "%Y-%m-%dT%H:%M:%S.%f+00:00",
                        )
                        - datetime(1970, 1, 1)
                    ).total_seconds()
                    * 1000
                )

                return [six.ensure_str(str(value)), log.get("txid")]

            if log.get("timestamp"):
                return log.get("timestamp", 0) + 1

            return current_log_offset
        else:
            timestamp = log[-1]["timestamp"]
            return timestamp + 1
