import urllib2, urllib, json, os, MySQLdb, ConfigParser

ZABBIX_SENDER = "/usr/bin/zabbix_sender"
ZABBIX_SERVER = "localhost"
ZABBIX_PORT = "10051"

config = ConfigParser.ConfigParser()
config.read("weather_setting.txt")

mysql_host = config.get("mysql","host")
mysql_port = config.get("mysql","port")
mysql_user = config.get("mysql","user")
mysql_pass = config.get("mysql","pass")
mysql_db = config.get("mysql","db")

db = MySQLdb.connect(host=mysql_host,port=int(mysql_port),user=mysql_user,passwd=mysql_pass,db=mysql_db)
cursor = db.cursor()
cursor.execute("SELECT hosts.host, hosts.name FROM hosts, hosts_groups, groups WHERE hosts.hostid=hosts_groups.hostid AND hosts.status=0 AND hosts_groups.groupid=groups.groupid AND groups.name='Weather stations'")
data = cursor.fetchall()

for row in data :
    HOST = row[0]
    CITY_WEATHER = row[1]	
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = "SELECT item.condition FROM weather.forecast WHERE woeid=" +row[0] +" AND u='c'"
    yql_url = baseurl + urllib.urlencode({'q':yql_query}) + "&format=json" 
	
    print row[1] #City Name 
    result = urllib2.urlopen(yql_url).read()
    data = json.loads(result)
    if data['query']['results'] != None:
        CURRENT_CONDITION = data['query']['results']['channel']['item']['condition']
        print CURRENT_CONDITION
        for CURRENT_KEY, CURRENT_VAL in CURRENT_CONDITION.items() :
            cmd = ZABBIX_SENDER + " -z " + ZABBIX_SERVER + " -p " + ZABBIX_PORT + " -s " + HOST + " -k " + CURRENT_KEY + " -o \"" + CURRENT_VAL + "\""
            os.system(cmd)		
            if CURRENT_KEY == "text":											
                sql = "SELECT hosts.host, hosts.name, hosts.hostid, items.itemid, items.name, items.key_ FROM items LEFT JOIN hosts ON items.hostid=hosts.hostid WHERE items.name='" + CITY_WEATHER + "'"
                cursor.execute(sql)
                result = cursor.fetchall()
                for record in result :
                    #print "Updating Modems Weather: " + record[0]
                    MODEM_HOST = record[0]
                    MODEM_KEY = "weather.condition" 				
                    cmd = ZABBIX_SENDER + " -z " + ZABBIX_SERVER + " -p " + ZABBIX_PORT + " -s \"" + MODEM_HOST + "\" -k " + MODEM_KEY + " -o \"" + CURRENT_VAL + "\""
                    print cmd
                    os.system(cmd)    
                '''sql = "SELECT hosts.host, hosts.name, hosts.hostid, items.itemid, items.name, items.key_ FROM items LEFT JOIN hosts ON items.hostid=hosts.hostid WHERE items.key_='" + HOST + "'"
                cursor.execute(sql)
                result = cursor.fetchall()
                for record in result :
                    print "Updating Modems Weather: " + record[0]
                    MODEM_HOST = record[0]
                    MODEM_KEY = HOST 				
                    cmd = ZABBIX_SENDER + " -z " + ZABBIX_SERVER + " -p " + ZABBIX_PORT + " -s \"" + MODEM_HOST + "\" -k " + MODEM_KEY + " -o \"" + CURRENT_VAL + "\""
                    print cmd
                    os.system(cmd)'''      
cursor.close()
db.close()