import logging
# import MySQLdb
import psycopg2
import requests

from . import conf


logger = logging.getLogger(__name__)


class DatabaseHandler(object):

    def __init__(self, db_name=conf.LISTENER_DB_NAME):
        logger.debug('Setting up DatabaseHandler for database `%s`.', db_name)
        self.db_name = db_name

    _db_con = None

    @property
    def db_con(self):
        if not self._db_con:
            logger.debug('Establishing new database connection to database `%s`.', self.db_name)
            import psycopg2

            # print ('db_con')
            # print (conf.LISTENER_DB_HOST)
            # print (conf.LISTENER_DB_PORT)
            # print (conf.LISTENER_DB_USER)
            # print (conf.LISTENER_DB_PASSWORD)
            # print (self.db_name)

            self._db_con = psycopg2.connect(
                host=conf.LISTENER_DB_HOST,
                port=int(conf.LISTENER_DB_PORT),
                user=conf.LISTENER_DB_USER,
                password=conf.LISTENER_DB_PASSWORD,
                dbname=self.db_name
            )
        return self._db_con

    def handle_query(self, query, args=None, retry=2):
        try:
            print ("query:" + query)
            print (args)
            cursor = self.db_con.cursor()
            cursor.execute(query, args)
            # print ("valar dohairis")
            self.db_con.commit()
        except (AttributeError, psycopg2.OperationalError):
            if not retry:
                logger.error('Query failed, no retries remaining.', exc_info=True)
                raise

            logger.warn('Query failed, attempting to refresh connection (%d retries remaining)', retry)
            self._db_con = None
            self.handle_query(query, args=args, retry=retry - 1)
        else:
            print ("initiating callback") 
            # r = requests.post('http://localhost:3000/test')
            # print (r.status_code)

