import joblib
import os

######################################################################
# Cache management
######################################################################

def getCaheDir():
    if (os.environ.has_key('JAZZ_HARMONY_CACHE_DIR')):
        return os.environ['JAZZ_HARMONY_CACHE_DIR']
    else:
        return None

memory = joblib.Memory(cachedir=getCaheDir(), verbose=0)

def clearCache():
    memory.clear()
