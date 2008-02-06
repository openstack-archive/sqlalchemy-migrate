class KeyedInstance(object):
    """A class whose instances have a unique identifier of some sort
    No two instances with the same unique ID should exist - if we try to create
    a second instance, the first should be returned. 
    """
    # _instances[class][instance]
    _instances=dict()
    def __new__(cls,*p,**k):
        instances = cls._instances
        clskey = str(cls)
        if clskey not in instances:
            instances[clskey] = dict()
        instances = instances[clskey]

        key = cls._key(*p,**k)
        if key not in instances:
            instances[key] = super(KeyedInstance,cls).__new__(cls,*p,**k)
        self = instances[key]
        return self

    @classmethod
    def _key(cls,*p,**k):
        """Given a unique identifier, return a dictionary key
        This should be overridden by child classes, to specify which parameters 
        should determine an object's uniqueness
        """
        raise NotImplementedError()

    @classmethod
    def clear(cls,cls2=None):
        # Allow cls.clear() as well as niqueInstance.clear(cls)
        if cls2 is not None:
            cls=cls2
        if str(cls) in cls._instances:
            del cls._instances[str(cls)]
        
