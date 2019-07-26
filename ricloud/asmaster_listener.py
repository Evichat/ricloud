import os
import re
import json
import time
import hashlib
import logging
import boto3
import ConfigParser
import io

from .api import Api, Task
from .ricloud import RiCloud
from .listener import Listener
from .handlers import RiCloudHandler, StreamError
from .database_handlers import DatabaseHandler
from .helpers import LogHelper
from . import utils


logger = logging.getLogger(__name__)

database_handler = DatabaseHandler()


class AsmasterListener(RiCloud):

    def __init__(self, timeout, api=None, listener=None, handlers=None):
        """Listener for receiving results from the asmaster mechanism."""
        logger.info(LogHelper.get_message('listener_worker_start'))

        self.timeout = timeout

        self.api = api or Api()

        handlers = handlers or [
            AsmasterSystemHandler,
            AsmasterFeedHandler,
            AsmasterMessageHandler,
            AsmasterDownloadFileHandler
        ]

        handlers_dict = dict(
            (handler.TYPE, handler(api=self.api)) for handler in handlers
        )

        super(AsmasterListener, self).__init__(
            api=self.api,
            listener=listener or Listener(handlers_dict),
        )

        self.listen()

    def listen(self):
        while True:
            try:
                self._check_stream_thread()

                RiCloudHandler.temporary_files.check_expiries()

                self.api.process_results()
            except KeyboardInterrupt:
                break
            except:  # noqa: E722 want the listener to survive.
                logger.error(LogHelper.get_message('listener_worker_error'), exc_info=True)


class AsmasterHandler(RiCloudHandler):
    TYPE = ''
    TABLE = None
    QUERY_TEMPLATE = ''

    @utils.profile('asmaster handler took', to_log=True)
    def on_complete_message(self, header, stream):
        task = AsmasterTask(header.get('task_id', 'system'), callback=self.generate_callback())
        task.headers = header
        task.result = stream.read()

        self.api.append_consumed_task(task)


class AsmasterSystemHandler(AsmasterHandler):
    TYPE = 'system'
    TABLE = 'system'
    QUERY_TEMPLATE = """
        INSERT INTO {table} (received, headers, body, message, code)
        VALUES (NOW(), %(headers)s, %(body)s, %(message)s, %(code)s)
    """

    def generate_callback(self):

        @utils.profile('system callback took', to_log=True)
        def callback(task):
            query = self.QUERY_TEMPLATE.format(table=self.TABLE)

            parsed_body = json.loads(task.result)

            message = parsed_body.get('message')
            code = parsed_body.get('code')

            args = {
                'headers': json.dumps(task.headers),
                'body': task.result,
                'message': message and message[:200] or None,
                'code': code and code[:200] or None,
            }

            database_handler.handle_query(query, args)

            if "error" in task.result:
                logger.error('System error message: %s', task.result)

        return callback


class AsmasterFeedHandler(AsmasterHandler):
    TYPE = 'fetch-data'
    TABLE = 'feed'
    QUERY_TEMPLATE = """
        INSERT INTO {table} (service, received, account_id, device_id, device_tag, headers, body)
        VALUES (%(service)s, NOW(), %(account_id)s, %(device_id)s, %(device_tag)s, %(headers)s, %(body)s)
    """

    def generate_callback(self):

        @utils.profile('feed callback took', to_log=True)
        def callback(task):
            query = self.QUERY_TEMPLATE.format(table=self.TABLE)

            args = {
                'service': task.headers['service'],
                'account_id': task.headers.get('account_id', None),
                'device_id': task.headers.get('device_id', None),
                'device_tag': task.headers.get('device_tag', None),
                'headers': json.dumps(task.headers),
                'body': json.dumps(task.result),
            }

            database_handler.handle_query(query, args)
            self.api.result_consumed(task.uuid)

        return callback


class AsmasterMessageHandler(AsmasterFeedHandler):
    TYPE = 'message'
    TABLE = 'message'


class AsmasterDownloadFileHandler(AsmasterHandler):
    print('AsmasterDownloadFileHandler')
    TYPE = 'download-file'
    TABLE = 'file'
    QUERY_TEMPLATE = """
        INSERT INTO {table}
            (service, received, account_id, device_id, device_tag, headers, location, file_id)
        VALUES (
            %(service)s, NOW(), %(account_id)s, %(device_id)s,
            %(device_tag)s, %(headers)s, %(location)s, %(file_id)s
        )
    """

    @utils.profile('file handler took', to_log=True)
    def on_complete_message(self, header, stream):
        print('on_complete_message')
        task = AsmasterTask(header.get('task_id', 'system'), callback=self.generate_callback())
        task.headers = header
        task.result = stream

        self.api.append_consumed_task(task)

        # Tell the `handle` function not to close the stream file.
        return True

    def generate_callback(self):
        print('generate_callback')
        @utils.profile('file callback took', to_log=True)
        def callback(task):
            print('callback')
            target_path = self.get_target_path(task.headers)
            print('target_path')
            print(target_path)

            file_path = utils.save_file_stream_to_target_path(task.result, target_path)
            print('file_path')
            print(file_path)

            # Close the temp file here as we did not let `handle` do so above.
            task.result.close()

            file_id = task.headers['file_id']
            print('file_id')
            print(file_id)

            if len(file_id) > 4096:
                raise StreamError("Invalid download file request, file_id is too long")

            query = self.QUERY_TEMPLATE.format(table=self.TABLE)

            args = {
                "service": task.headers['service'],
                "account_id": task.headers.get('account_id', None),
                "device_id": task.headers.get('device_id', None),
                "device_tag": task.headers.get('device_tag', None),
                "headers": json.dumps(task.headers),
                "location": file_path,
                "file_id": file_id,
            }

            database_handler.handle_query(query, args)
            self.upload_to_s3(file_path, file_id)
            self.api.result_consumed(task.uuid)

        return callback

    @staticmethod
    def upload_to_s3(file_path, file_id):
        print('upload_to_s3')
      
        # file_path = "/Users/nilu/workspace/ricloud/output/asrelay-itunes/397699/161961/25ff7d80c89599b67e5a00220d8753cc668427f6"
        # file_id = "25ff7d80c89599b67e5a00220d8753cc668427f6"

        outputName = re.findall(r"asrelay-itunes\/.*", file_path)[0]
        print(outputName)

        bucketName = 'evichat-production'
        s3 = boto3.client('s3')
        s3.upload_file(file_path,bucketName,outputName)
      
        return 'true'

    @staticmethod
    def get_target_path(headers):
        print('get_target_path')

        filename = AsmasterDownloadFileHandler.file_id_to_file_name(headers['file_id'])
        print('filename~')
        print(filename)

        path = os.path.join(
            headers['service'],
            str(headers.get('account_id', "None")),
            str(headers.get('device_id', "None")),
            filename
        )
        
        print('path')
        print(path)

        return path

    @staticmethod
    def file_id_to_file_name(file_id):
        print('file_id_to_file_name')
        """Sometimes file ids are not the file names on the device, but are instead generated
        by the API. These are not guaranteed to be valid file names so need hashing.
        """
        if len(file_id) == 40 and re.match("^[a-f0-9]+$", file_id):
            return file_id
        # prefix with "re_" to avoid name collision with real fileids
        return "re_{}".format(hashlib.sha1(file_id).hexdigest())


class AsmasterTask(Task):

    def __init__(self, uuid, callback=None):
        super(AsmasterTask, self).__init__(uuid, callback=callback)

        self._resolved = True  # Only create these tasks when we receive the task results, hence already resolved.
        self._headers = None

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

        start_time = self.timer
        self.timer = time.time() - start_time
