'''
Created on Apr 12, 2016

@author: kakan
'''

class UrlCollector():
    __urls = []
    __instance = None
    
    @staticmethod
    def instance():
        if UrlCollector.__instance == None:
            UrlCollector.__instance = UrlCollector()
        return UrlCollector.__instance
    
    @property
    def list_url(self):
        return self.__urls
    
    def collect(self,url):
        if type(url) == list:
            self.__urls += url
        elif type(url) == tuple:
            self.__urls.append(url)
        else:
            raise TypeError("Url should be list or tuple.",type(url),"given.")
        #print(self.__urls)
        
        
