import os

def get_lock(name="lock.lock"):
    while os.path.exists(name):
        pass
    else:
        f = open(name, 'w')
        f.write(" ")
        f.close()
    
def release_lock(name="lock.lock"):
    os.remove(name)
