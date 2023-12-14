import sqlite3
import os

__currentdir = os.path.dirname(os.path.realpath(__file__))
SQLITE_DATABASE_PATH = os.path.join(__currentdir, "loramac.db")

TABLE_DEVICE_QUERY = """
CREATE TABLE IF NOT EXISTS DEVICE (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DevEUI VARCHAR(16) NOT NULL UNIQUE,
    AppEUI VARCHAR(16) NOT NULL,
    AppKey VARCHAR(32) NOT NULL,
    DevAddr VARCHAR(8),
    NwkSKey VARCHAR(32),
    AppSKey VARCHAR(32),
    FCnt INTEGER DEFAULT 0,
    FPort INTEGER DEFAULT 2,
    DevNonce INTEGER DEFAULT 0,
    isJoined BOOLEAN DEFAULT 0,
    channelGroup INTEGER DEFAULT 0,
    Created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now', 'utc'))
);
"""

SELECT_DEVICES_QUERY = "SELECT * FROM DEVICE "
SELECT_DEVICE_QUERY  = "SELECT * FROM DEVICE WHERE DevEUI = ? "
INSERT_DEVICE_QUERY  = "INSERT INTO DEVICE(DevEUI, AppEUI, AppKey) VALUES(?, ?, ?) "
UPDATE_DEVICE_QUERY  = "UPDATE DEVICE SET "
DELETE_DEVICE_QUERY  = "DELETE FROM DEVICE WHERE DevEUI = ? "
SELECT_DEVICE_QUERY_BY_DEVADDR  = "SELECT * FROM DEVICE WHERE DevAddr = ? "

DEFAULT_APPEUI       = "0000000000000000"

class COLOR:
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

class Database():

    def __init__(self, database_name : str = SQLITE_DATABASE_PATH):
        self.__name = database_name
        self.__connection : sqlite3.Connection = None
        self.__cursor : sqlite3.Cursor = None

    def open(self):
        self.__connection = sqlite3.connect(self.__name)
        self.__cursor = self.__connection.cursor()

    def close(self):
        if self.__connection != None:
            self.__connection.close()
            self.__connection = None
            self.__cursor = None

    def __connected__(self):
        if self.__connection == None :
            print(COLOR.FAIL+"No connection"+COLOR.END)
            return False
        return True

    def create_table(self) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            self.__cursor.execute(TABLE_DEVICE_QUERY)
            self.__connection.commit()
            return True
        except:
            print("failed")
            return False



    ######################## Table DEVICE CRUD methods #############################
    
    def get_device(self, DevEUI:str=None) -> dict:
        try:
            if self.__connected__() is not True:
                return None
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return None
            self.__cursor.execute(SELECT_DEVICE_QUERY, (DevEUI,))
            item = self.__cursor.fetchone()
            device = {}
            columns = [description[0] for description in self.__cursor.description]
            for i in range(len(columns)):
                device[columns[i]] = item[i]
            return device
        except:
            return None

    def get_device_by_devaddr(self, DevAddr:str=None) -> dict:
        try:
            if self.__connected__() is not True:
                return None
            if DevAddr == None:
                print(COLOR.FAIL+"DevAddr can't be none"+COLOR.END)
                return None
            self.__cursor.execute(SELECT_DEVICE_QUERY_BY_DEVADDR, (DevAddr,))
            items = self.__cursor.fetchone()
            device = {}
            columns = [description[0] for description in self.__cursor.description]
            for i in range(len(columns)):
                device[columns[i]] = items[i]
            return device
        except:
            return None
    

    def insert_device(self, DevEUI:str=None, AppEUI:str=DEFAULT_APPEUI, AppKey:str=None) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None or AppKey == None:
                print(COLOR.FAIL+"DevEUI or AppEUI can't be none"+COLOR.END)
                return False
            self.__cursor.execute(INSERT_DEVICE_QUERY, (DevEUI, AppEUI, AppKey,))
            self.__cursor.connection.commit()
            return True
        except:
            return False
    
    def update_dev_nonce(self, DevEUI:str=None, DevNonce:int=1) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return False
            if DevNonce <= 0 or DevNonce >= 65536:
                print(COLOR.FAIL+"DevNonce must be between 1 and 65535"+COLOR.END)
                return False
            query = UPDATE_DEVICE_QUERY + "DevNonce = ? " \
                                        + "WHERE DevEUI = ?"
            self.__cursor.execute(query, (DevNonce, DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False

    def update_f_cnt(self, DevEUI:str=None, FCnt:int=1) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return False
            if FCnt <= 0 or FCnt >= 65536:
                print(COLOR.FAIL+"FCnt must be between 1 and 65535"+COLOR.END)
                return False
            query = UPDATE_DEVICE_QUERY + "FCnt = ? " \
                                        + "WHERE DevEUI = ?"
            self.__cursor.execute(query, (FCnt, DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False

    def update_session_keys(self, DevEUI:str=None, DevAddr:str=None, NwkSKey:str=None, AppSKey:str=None) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None or DevAddr == None or NwkSKey == None or AppSKey == None:
                print(COLOR.FAIL+"DevEUI or DevAddr or NwkSKey or AppSKey can't be none"+COLOR.END)
                return False
            query = UPDATE_DEVICE_QUERY + "DevAddr = ?, " \
                                        + "NwkSKey = ?, " \
                                        + "AppSKey = ? " \
                                        + "WHERE DevEUI = ?"
            self.__cursor.execute(query, (DevAddr, NwkSKey, AppSKey, DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False
    

    def update_is_joined(self, DevEUI:str=None, isJoined:bool=False) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return False
            query = UPDATE_DEVICE_QUERY + "isJoined = ? " \
                                        + "WHERE DevEUI = ?"
            self.__cursor.execute(query, (isJoined, DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False
    def update_channel_group(self, DevEUI:str=None, channelGoup:int=0) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return False
            if channelGoup < 0 or channelGoup > 7:
                print(COLOR.FAIL+"DevNonce must be between 0 and 7"+COLOR.END)
                return False
            query = UPDATE_DEVICE_QUERY + "channelGoup = ? " \
                                        + "WHERE DevEUI = ?"
            self.__cursor.execute(query, (channelGoup, DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False
    def delete_device(self, DevEUI:str=None) -> bool:
        try:
            if self.__connected__() is not True:
                return False
            if DevEUI == None:
                print(COLOR.FAIL+"DevEUI can't be none"+COLOR.END)
                return False
            self.__cursor.execute(DELETE_DEVICE_QUERY, (DevEUI,))
            self.__connection.commit()
            return True
        except:
            return False


