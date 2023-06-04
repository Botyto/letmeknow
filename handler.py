import logging
import tornado.web
import sqlalchemy.orm

import db

logger = logging.getLogger(__name__)


class BaseRequestHandler(tornado.web.RequestHandler):
    _session: sqlalchemy.orm.Session|None = None

    @property
    def session(self):
        if self._session is None:
            self._session = db.sessionmaker()
        return self._session
    
    def on_finish(self):
        if self._session is not None:
            try:
                self._session.commit()
            except sqlalchemy.exc.PendingRollbackError as e:
                logger.exception(e)
            self._session.close()
            self._session = None
