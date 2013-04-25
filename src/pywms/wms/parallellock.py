'''
COPYRIGHT 2010 Alexander Crosby

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

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
