from base import Base
from pathed import Pathed
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import create_session
from pkg_resources import resource_stream
import os

def readurls():
    filename='test_db.cfg'
    fullpath = os.path.join(os.curdir,filename)
    ret=[]
    tmpfile=Pathed.tmp()
    try:
        fd=open(fullpath)
    except IOError:
        print "You must specify the databases to use for testing!"
        tmplfile = "%s.tmpl"%filename
        print "Copy %s.tmpl to %s and edit your database URLs."%(tmplfile,filename)
        raise
    #fd = resource_stream('__main__',filename)
    for line in fd:
        if line.startswith('#'):
            continue
        line=line.replace('__tmp__',tmpfile).strip()
        ret.append(line)
    fd.close()
    return ret

def is_supported(url,supported,not_supported):
    db = url.split(':',1)[0]
    if supported is not None:
        if isinstance(supported,basestring):
            supported = (supported,)
        ret = db in supported
    elif not_supported is not None:
        if isinstance(not_supported,basestring):
            not_supported = (not_supported,)
        ret = not (db in not_supported)
    else:
        ret = True
    return ret

#we make the engines global, which should make the tests run a bit faster
urls = readurls()
engines=dict([(url,create_engine(url, echo=True)) for url in urls])


def usedb(supported=None,not_supported=None):
    """Decorates tests to be run with a database connection
    These tests are run once for each available database

    @param supported: run tests for ONLY these databases
    @param not_supported: run tests for all databases EXCEPT these

    If both supported and not_supported are empty, all dbs are assumed 
    to be supported
    """
    if supported is not None and not_supported is not None:
        msg = "Can't specify both supported and not_supported in fixture.db()"
        assert False, msg

    my_urls = [url for url in urls if is_supported(url,supported,not_supported)]
    def dec(func):
        def entangle(self):
            for url in my_urls:
                self._setup(url)
                yield func, self
                self._teardown()
        entangle.__name__ = func.__name__
        return entangle
    return dec


class DB(Base):
    # Constants: connection level
    NONE=0  # No connection; just set self.url
    CONNECT=1   # Connect; no transaction
    TXN=2   # Everything in a transaction

    level=TXN

    def shortDescription(self,*p,**k):
        """List database connection info with description of the test"""
        ret = super(DB,self).shortDescription(*p,**k) or str(self)
        engine = self._engineInfo()
        if engine is not None:
            ret = "(%s) %s"%(engine,ret)
        return ret

    def _engineInfo(self,url=None):
        if url is None: 
            url=self.url
        return url

    def _setup(self, url):
        self._connect(url)

    def _teardown(self):
        self._disconnect()
    
    def _connect(self,url):
        self.url = url
        self.engine = engines[url]
        self.meta = MetaData(bind=self.engine)
        if self.level < self.CONNECT: 
            return
        #self.conn = self.engine.connect()
        self.session = create_session(bind=self.engine)
        if self.level < self.TXN: 
            return
        self.txn = self.session.begin()

        #self.txn.add(self.engine)

    def _disconnect(self):
        if hasattr(self,'txn'):
            self.txn.rollback()
        if hasattr(self,'session'):
            self.session.close()
        #if hasattr(self,'conn'):
        #    self.conn.close()

    def _supported(self,url):
        db = url.split(':',1)[0]
        func = getattr(self,self._TestCase__testMethodName)
        if hasattr(func,'supported'):
            return db in func.supported
        if hasattr(func,'not_supported'):
            return not (db in func.not_supported)
        # Neither list assigned; assume all are supported
        return True
    def _not_supported(self,url):
        return not self._supported(url)

    def refresh_table(self,name=None):
        """Reload the table from the database
        Assumes we're working with only a single table, self.table, and
        metadata self.meta

        Working w/ multiple tables is not possible, as tables can only be
        reloaded with meta.clear()
        """
        if name is None:
            name = self.table.name
        self.meta.clear()
        self.table = Table(name,self.meta,autoload=True)
