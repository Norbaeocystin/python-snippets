import atexit
from bson import objectid
import logging
import json
from pykafka import KafkaClient
from pymongo import MongoClient
from scrapify import Scraper

logging.basicConfig(filename='consumer.log', level=logging.DEBUG,  format = '%(asctime)s %(name)s %(levelname)s %(message)s')
logging.getLogger("pykafka").setLevel(logging.WARNING)
logging.getLogger("kazoo").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger()

#Defaults 
MONGO_URI = 'localhost:27017'
KAFKA_URI = "0.0.0.0:9092"
ZOOKEEPER_URI = '0.0.0.0:2181'
CONSUMER_GROUP = "Docker"
DEFAULT_DB = 'Kafka'
DEFAULT_COLL = 'Source'

#mongo connections
CON = MongoClient(MONGO_URI)
coll = CON[DEFAULT_DB][DEFAULT_COLL]
#kafka connection
client = KafkaClient(hosts=KAFKA_URI)
topic = client.topics['Mongo.Kafka.Source']

scraper = Scraper(timeout=10)
commands = {}
commands['OnlyEmails'] = scraper.get_emails_from_url
commands['Emails'] = scraper.get_emails_and_social_networks_from_url
commands['SocialNetworks'] = scraper.get_emails_and_social_networks_from_url
commands['OnlySocialNetworks'] = scraper.get_social_networks_from_url
commands['Data'] = scraper.get_data_from_url_for_list_of_tags #also Tag value need to be passed here

def convert_message(message):
    logger.debug(message.value.decode())
    try:
        data_from_kafka = json.loads(message.value.decode()).get('payload')
    except (Exception, BaseException) as e:
        logger.error(e.__class__.__name__)
        return None
    return data_from_kafka

def get_id(doc):
    _id = doc['_id']
     #some _id are ObjectId some are not
    if isinstance(_id, dict) and _id.get('$oid'):
        _id = objectid.ObjectId(_id['$oid'])
    return _id

def insert_and_remove_doc(CON, data, db_origin, coll_origin, _id, coll):
    logging.debug(data)
    if db_origin and coll_origin:
        response = CON[db_origin][coll_origin].update_one({'_id':_id},{"$set":data})
        if response.matched_count:
            coll.delete_one({'_id':_id})
            logger.debug('Removing data after update in original collection')
    else:
        coll.update_one({'_id':_id},{"$set":data})    

def process(message):
    '''
    will process the message and update doc in collection
    '''
    data_from_kafka = convert_message(message)
    if data_from_kafka:
        doc = json.loads(data_from_kafka)
        _id = get_id(doc)
        web = doc.get('Website')
        command = doc.get('Command')
        data = {}
        if web and command:
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
        insert_and_remove_doc(CON = CON, data = data, db_origin = db_origin, coll_origin = coll_origin, _id = _id, coll = coll)
        
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
    exit()
