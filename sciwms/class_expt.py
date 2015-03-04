'''
Created on Mar 4, 2015

@author: ayan
'''

class SkittyDate(object):
    
    def __init__(self, day=0, month=0, year=0):
        self.day = day
        self.month = month
        self.year = year
        
    @staticmethod
    def is_date_valid(date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        return day <= 31 and month <= 12 and year <= 3999
        
    def display(self):
        return '{0}-{1}-{2} Skitty 1'.format(self.month, self.day, self.year)
    
    @classmethod
    def millenium(cls, month, day):
        mil = cls(month, day, 2000)
        return mil
    
class SkittyDate2(SkittyDate):
    
    def display(self):
        return '{0}-{1}-{2} Skitty 2'.format(self.month, self.day, self.year)
    
    
class MetapodDate(object):
    
    def __init__(self, month, day, year):
        self.month = month
        self.day = day
        self.year = year
        
    def display(self):
        return '{0}-{1}-{2}'.format(self.month, self.day, self.year)
    
    @staticmethod
    def millenium(month, day):
        return MetapodDate(month, day, 2000)
    
    
class MetapodDate2(MetapodDate):
    
    def display(self):
        return '{0}-{1}-{2} Metapod!'.format(self.month, self.day, self.year) 
    
    
if __name__ == '__main__':
    skitty1_date_20150303 = SkittyDate.millenium(3, 3)
    skitty2_date_20150303 = SkittyDate2.millenium(3, 3)
    print(isinstance(skitty1_date_20150303, SkittyDate))  # True
    print(isinstance(skitty2_date_20150303, SkittyDate2))  # True
    
    metapod1_date_20150303 = MetapodDate.millenium(3, 3)
    metapod2_date_20150303 = MetapodDate2.millenium(3, 3)
    print(isinstance(metapod1_date_20150303, MetapodDate))  # True
    print(isinstance(metapod2_date_20150303, MetapodDate2))  # False