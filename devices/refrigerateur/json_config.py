import json

class JsonConfig:
    '''A storage area on filesystem. Based on json format
    '''
    def __init__(self, filename = "config.json"):
        self.filename = filename
        self.dict = {}
        
    def read(self, key = None):
        '''Read the file if key, return value otherwise, return all dict
        '''
        try:
            with open(self.filename, 'r') as configfile:
                self.dict = json.loads(configfile.read())
        except:
            self.dict = {}
        if key:
            return self.dict.get(key)
        else:
            return self.dict
    def get(self, key):
        return self.dict.get(key)
    
    def set(self, key, value):
        ''' Add key:value to the dict
        '''
        self.dict[key]=value
    
    def save(self):
        '''Save config to file
        '''
        try:
            with open(self.filename, 'w') as configfile:
                configfile.write(json.dumps(self.dict))
        except:
            print("Error saving fault.")
            return False
        else:
            return True