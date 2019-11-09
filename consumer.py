import atexit
from bson import objectid
import logging
import json
from pykafka import KafkaClient
from pymongo import MongoClient
from scrapify import Scraper

logging.basicConfig(filename='consumer.log', level=logging.ERROR,  format = '%(asctime)s %(name)s %(levelname)s %(message)s')
logging.getLogger("pykafka").setLevel(logging.WARNING)
logging.getLogger("kazoo").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger()

#Defaults 
MONGO_URI = 'localhost:27017'
KAFKA_URI = "0.0.0.0:9092"
ZOOKEEPER_URI = '0.0.0.0:2181'
CONSUMER_GROUP = "docker"
DEFAULT_DB = 'Kafka'
DEFAULT_COLL = 'Source'

#mongo connections
CON = MongoClient(MONGO_URI)
coll = CON[DEFAULT_DB][DEFAULT_COLL]
#kafka connection
client = KafkaClient(hosts=KAFKA_URI)
topic = client.topics['Mongo.Kafka.Source']

scraper = Scraper()
commands = {}
commands['OnlyEmails'] = scraper.get_emails_from_url
commands['Emails'] = scraper.get_emails_and_social_networks_from_url
commands['SocialNetworks'] = scraper.get_emails_and_social_networks_from_url
commands['OnlySocialNetworks'] = scraper.get_social_networks_from_url
commands['Data'] = scraper.get_data_from_url_for_list_of_tags #also Tag value need to be passed here

def process(message):
    '''
    will process the message and update doc in collection
    '''
    try:
        data_from_kafka = json.loads(message.value.decode()).get('payload')
    except (Exception, BaseException) as e:
        logger.error(e.__class__.__name__)
        data_from_kafka = None
    logger.debug(message.value.decode())
    if data_from_kafka:
        doc = json.loads(data_from_kafka)
        _id = objectid.ObjectId(doc['_id']['$oid'])
        web = doc.get('Website')
        command = doc.get('Command')
        if web and command:
            data = {}
            try:
                if command == 'OnlyEmails':
                    result = commands['OnlyEmails'](web)
                    data['Emails'] = result
                elif command == "Data":
                    tags = doc.get('Tags')
                    if tags:
                        data = commands['Data'](web, tags)                   
                else:
                    data = commands[command](web)
            except (Exception, BaseException) as error:
                error_name = error.__class__.__name__
                data['Error'] = error_name
        logger.debug(doc)
        data['Processed'] = True
        db_origin = doc.get("Database")
        coll_origin = doc.get("Collection")
        #change in different database and collection
        if db_origin and coll_origin:
            response = CON[db_origin][coll_origin].update_one({'_id':_id},{"$set":data})
            if response.matched_count:
                coll.delete_one({'_id':_id})
            logger.debug('Removing data after update in original collection')
        logging.debug(data)
        coll.update_one({'_id':_id},{"$set":data})    
        
#consumer = topic.get_balanced_consumer(consumer_group=CONSUMER_GROUP, auto_commit_enable=False, zookeeper_connect=ZOOKEEPER_URI)
consumer = topic.get_balanced_consumer(consumer_group=CONSUMER_GROUP, auto_commit_enable=False, rebalance_backoff_ms=100, zookeeper_connect=ZOOKEEPER_URI)
#for cleanup
@atexit.register
def cleanup():
    consumer.stop()
    
try:  
    for message in consumer:
        if message is not None:
            process(message)
except KeyboardInterrupt:
    cleanup()
