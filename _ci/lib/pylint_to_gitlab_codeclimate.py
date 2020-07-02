#!/usr/bin/env python3
# adapted from https://gist.github.com/caryan/87bdadba4b6579ffed8a87d546364d72
import hashlib
import six
import sys

from pylint.interfaces import IReporter
from pylint.reporters import JSONReporter
from pylint.lint import Run


# small portions taken from https://github.com/mercos/codeclimate-pylint
# no copyright or license was asserted as of February 2020
class GitlabCodeClimateReporter(JSONReporter):
    __implements__ = IReporter
    name = "gitlabcodeclimate"

    def handle_message(self, msg):
        codeclimate_dict = dict()

        message_lines = self._parse_message(msg.msg).splitlines()
        codeclimate_dict["description"] = message_lines[0]

        location = dict()
        location["path"] = msg.path

        # gitlab only uses the "lines.begin" version of location
        location["lines"] = {"begin": msg.line}
        codeclimate_dict["location"] = location

        # gitlab needs a fingerprint
        # hash the issue, filename and line number
        codeclimate_dict["fingerprint"] = hashlib.sha256(
            (msg.symbol + msg.path + six.text_type(msg.line)).encode()
        ).hexdigest()

        self.messages.append(codeclimate_dict)

    def _parse_message(self, message):
        while "  " in message:
            message = message.replace("  ", " ")
        message = message.replace('"', "`")
        message = message.replace("\\", "")
        return message


if __name__ == "__main__":
    Run(sys.argv[1:], reporter=GitlabCodeClimateReporter(), do_exit=False)
