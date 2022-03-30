from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from json import dumps, loads
import pandas as pd
from time import time
import sys
import os
import logging

# Initialize log
log = logging.getLogger(__name__)


# TODO documentation
# TODO verify inputs (ie. is a list)
class MessageHandler:
    """
    Handles communication with Kafka in terms of both producing and consuming messages.

    Attributes
    ----------
    group id : str, optional
        kafka consumer group id used to keep track of consumed message offset (default is None)
    auto_offset_reser : str, optional
        kafka auto offset reset, which can be set to latest or earliest (default is earliest)
    enable_auto_commit : boolen, optional
        ???
    """
    # TODO add serializer usage (JSON)
    def __init__(self,
                 group_id=None,
                 auto_offset_reset='earliest',
                 enable_auto_commit=False,
                 topics_consumed_list=[],
                 topics_produced_list=[],
                 poll_timeout_ms=100,
                 fetch_max_wait_ms=200):

        # attributes set on object instansiation, either by default or supplied values.
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.topics_consumed_list = topics_consumed_list
        self.topics_produced_list = topics_produced_list
        self.poll_timeout_ms = poll_timeout_ms
        self.fetch_max_wait_ms = fetch_max_wait_ms

        # attributes set based on others
        self.topic_list = list(set(self.topics_produced_list + self.topics_consumed_list))
        self.topics_consumed_only = list(set(self.topics_consumed_list) - set(self.topics_produced_list))
        self.topics_produced_only = list(set(self.topics_produced_list) - set(self.topics_consumed_list))
        self.topics_consumed_and_produced = list(set(self.topics_consumed_list).intersection(self.topics_produced_list))

        # attributes init by methods on creation
        self.bootstrap_servers = None
        self.consumer = None
        self.producer = None

        # methods called to init kafka settings
        # TODO add kafka brooker setting from var instead of env-var
        self.set_kafka_brooker_from_env()
        self.init_consumer()
        self.verify_topic_existence()
        if topics_consumed_list:
            self.subscribe_topics()
        if topics_produced_list:
            self.init_producer()
        self.init_topic_partitions()

    # Method: set kafka brooker from ENV or default to value
    def set_kafka_brooker_from_env(self):
        log.debug("Setting kafka boostrap servers from environment variable.")
        try:
            self.bootstrap_servers = os.environ.get('KAFKA_HOST', "my-cluster-kafka-bootstrap.kafka")
            log.info(f"Kakfa bootsrap servers was set to: {self.bootstrap_servers}")
        except Exception as e:
            log.exception(f"Setting kafka boostrap servers from environment variable failed with message: '{e}'.")
            sys.exit(1)

    # Method: Initializes Kafka comsumer.
    def init_consumer(self):
        log.debug("Kafka consumer connection initializing.")
        try:
            self.consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers,
                                          group_id=self.group_id,
                                          value_deserializer=lambda x: loads(x.decode('utf-8')),
                                          auto_offset_reset=self.auto_offset_reset,
                                          enable_auto_commit=self.enable_auto_commit,
                                          fetch_max_wait_ms=self.fetch_max_wait_ms)
            log.info("Kafka consumer connection established.")
        except Exception as e:
            log.exception(f"Kafka Consumer connection failed with message: '{e}'.")
            sys.exit(1)

    # Method: Initializes Kafka producer.
    def init_producer(self):
        log.debug("Kafka producer connection initializing.")
        try:
            self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers,
                                          value_serializer=lambda x: dumps(x).encode('utf-8'),
                                          key_serializer=lambda x: dumps(x).encode('utf-8'))
            log.info("Kafka producer connection established.")
        except Exception as e:
            log.exception(f"Kafka producer connection failed with message: '{e}'.")
            sys.exit(1)

    # Method: Dummy Poll, which is needed to force assignment of partitions after subsribtion to topics. (only needed when using seek method)
    def init_topic_partitions(self):
        log.debug("Initiliasing topic partitions assignemnt.")
        # TODO check if using a dummy poll is the correct way, maybe also consumer loop could work?
        try:
            # dummy poll only one message
            data = self.consumer.poll(timeout_ms=self.poll_timeout_ms, max_records=1)

            # if data returned in dummy poll, then seek partion back one offset to keep correct postion for later message processing
            if data:
                for topic_partition in data:
                    self.consumer.seek(partition=topic_partition, offset=self.consumer.position(topic_partition)-1)

            log.debug("Initial poll done. TopicPartitions are now assigned.")
        except Exception as e:
            log.exception(f"Initial poll failed with message '{e}'.")
            sys.exit(1)

    # Method: Verify if topics exists.
    def verify_topic_existence(self):
        log.debug("Verifying if topics {self.topic_list} exist via Kakfa brooker.")
        unavbl_topics = []
        for topic in self.topic_list:
            try:
                if topic not in self.consumer.topics():
                    unavbl_topics.append(topic)
            except Exception as e:
                log.exception(f"Verifying if topic: '{topic}' exists failed with message: '{e}'.")
                sys.exit(1)

        if unavbl_topics:
            log.error(f"The Topic(s): {unavbl_topics} does not exist.")
            sys.exit(1)
        else:
            log.debug("All topics exist.")

    # Method: Subscribes consumer to topics
    def subscribe_topics(self):
        log.debug("Subscribing to consumed kafka topics.")
        try:
            self.consumer.subscribe(self.topics_consumed_list)
            log.info(f"Kafka consumer subscribed to topics: '{self.topics_consumed_list}'.")
        except Exception as e:
            log.info(f"Kafka consumer subscribtion to topics: '{self.topics_consumed_list}' " +
                     f"failed with message: '{e}'.")
            sys.exit(1)

    # Method: Create a dictionary with partitions availiable for each topic.
    def create_topic_partitions_dict(self):
        log.debug("Creating topic partitions dictionary")
        if type(self.topic_list) != list:
            log.error(f"Supplied topics must have the type 'list' but is {type(self.topic_list)}")
            sys.exit(1)

        topic_partitions_dict = {}
        try:
            for topic in self.topic_list:
                topic_partitions_dict[topic] = [TopicPartition(topic, p)
                                                for p in self.consumer.partitions_for_topic(topic)]
            log.debug("Created topic partitions dictionary")
        except Exception as e:
            log.exception(f"Making dictionary of lists for topic partitions for topic: '{topic}' " +
                          f"failed with message: '{e}'.")
            sys.exit(1)

        return topic_partitions_dict

    # Method: Create a dictionary with topic partition --> begin offsets
    def create_topic_partitions_begin_offsets_dict(self):
        log.debug("Creating dictionary with: topic partitions -> begin offsets.")
        begin_offset_topic_partitions_dict = {}

        try:
            for topic in self.topic_list:
                begin_offset_topic_partitions_dict[topic] = self.consumer.beginning_offsets([TopicPartition(topic, p) for p in self.consumer.partitions_for_topic(topic)])
            log.debug("Created dictionary.")
        except Exception as e:
            log.exception(f"Getting latest offset for partitions for topic: '{topic}' failed with message '{e}'.")
            sys.exit(1)

        return begin_offset_topic_partitions_dict

    # Method: Create a dictionary with topic partition --> end offsets
    def create_topic_partitions_end_offsets_dict(self):
        log.debug("Creating dictionary with: topic partitions -> end offsets.")
        end_offset_topic_partitions_dict = {}

        try:
            for topic in self.topic_list:
                end_offset_topic_partitions_dict[topic] = self.consumer.end_offsets([TopicPartition(topic, p) for p in self.consumer.partitions_for_topic(topic)])
            log.debug("Created dictionary.")
        except Exception as e:
            log.exception(f"Getting end offset for partitions for topic: '{topic}' failed with message: '{e}'.")
            sys.exit(1)

        return end_offset_topic_partitions_dict

    # TODO doc Method:
    def create_topic_latest_dicts(self):
        topic_latest_message_timestamp_dict = {}
        topic_latest_message_value_dict = {}
        for topic in self.topics_consumed_list:
            topic_latest_message_timestamp_dict[topic] = 0
            topic_latest_message_value_dict[topic] = None
        return topic_latest_message_timestamp_dict, topic_latest_message_value_dict

    # Method: list empty topics
    def list_empty_topics(self, topic_list):
        topic_partitions_dict = self.create_topic_partitions_dict()
        begin_offset_topic_partitions_dict = self.create_topic_partitions_begin_offsets_dict()
        end_offset_topic_partitions_dict = self.create_topic_partitions_end_offsets_dict()

        empty_topics = topic_list.copy()

        for topic in topic_list:
            # loop all partitions for topic
            for topic_partition in topic_partitions_dict[topic]:
                if end_offset_topic_partitions_dict[topic][topic_partition] > begin_offset_topic_partitions_dict[topic][topic_partition]:
                    empty_topics.remove(topic)

        return empty_topics

    # Method: list empty consumed only topics
    def list_empty_consumed_only_topics(self):
        return self.list_empty_topics(self.topics_consumed_only)

    # Method: list empty produced only topics
    def list_empty_produced_only_topics(self):
        return self.list_empty_topics(self.topics_produced_only)

    # Method: list empty consuemd and produced topics
    def list_empty_consumed_and_produced_topics(self):
        return self.list_empty_topics(self.topics_consumed_and_produced)

    # Method: Seek partitions to latest availiable message
    def seek_topic_partitions_latest(self):

        topic_partitions_dict = self.create_topic_partitions_dict()
        end_offset_topic_partitions_dict = self.create_topic_partitions_end_offsets_dict()

        try:
            # loop topics and seek all partitions to latest availiable message
            for topic in self.topics_consumed_list:
                # loop all partitions for topic
                for topic_partition in topic_partitions_dict[topic]:
                    # if they have messages, per partition
                    if end_offset_topic_partitions_dict[topic][topic_partition] > 0:
                        # seek to highest offset-1
                        partition = topic_partitions_dict[topic][topic_partition.partition]
                        offset = end_offset_topic_partitions_dict[topic][topic_partition]-1
                        self.consumer.seek(partition, offset)
        except Exception as e:
            log.exception(f"Seeking consumer: '{partition}' to offset: {offset} failed with message '{e}'.")
            sys.exit(1)

    # Method: Get latest message value per topic and return it in dictionary - using poll
    def get_latest_topic_messages_to_dict_poll_based(self):
        # TODO modify this to include timeout for max time spend on polls?

        # dictionaries for holding latest timestamp and value for each consumed topic
        topic_latest_message_timestamp_dict, topic_latest_message_value_dict = self.create_topic_latest_dicts()

        # Seek all partitions for consumed topics to latest availiable message
        self.seek_topic_partitions_latest()

        # poll data
        is_polling = True
        while is_polling:

            data_object = self.consumer.poll(timeout_ms=self.poll_timeout_ms, max_records=None)

            if data_object:
                # loop all messages returned by poll per partition
                for topic_partition in data_object:
                    # loop all messages for partition
                    for msg in range(0, len(data_object[topic_partition])):
                        # if timestamp than last read msg for topic, then update values in dict
                        topic = data_object[topic_partition][msg].topic
                        if data_object[topic_partition][msg].timestamp > topic_latest_message_timestamp_dict[topic]:
                            topic_latest_message_timestamp_dict[topic] = data_object[topic_partition][msg].timestamp
                            topic_latest_message_value_dict[topic] = data_object[topic_partition][msg].value

            if self.topic_positions_reached_last_offsets(topic_list=self.topics_consumed_list):
                is_polling = False

        return topic_latest_message_value_dict

    # Method: Get latest message value per topic and return it in dictionary - using consumer loop
    def get_latest_topic_messages_to_dict_loop_based(self):
        # Latest message is determined on timestamp. Will loop all partitions.
        # TODO put everything in a try catch?
        # TODO modify this to include timeout logic?

        # dictionaries for holding latest timestamp and value for each consumed topic
        topic_latest_message_timestamp_dict, topic_latest_message_value_dict = self.create_topic_latest_dicts()

        # Seek all partitions for consumed topics to latest availiable message
        self.seek_topic_partitions_latest()

        for message in self.consumer:

            # if timestamp of read message is newer that last read message from topic, update dict
            if message.timestamp > topic_latest_message_timestamp_dict[message.topic]:
                topic_latest_message_timestamp_dict[message.topic] = message.timestamp
                topic_latest_message_value_dict[message.topic] = message.value

            # If all partitions have been consumed till latest offset, break out of conusmer loop
            if self.topic_positions_reached_last_offsets(topic_list=self.topics_consumed_list):
                break

        return topic_latest_message_value_dict

    # Method: get latest msg from topic an return it
    def get_latest_msg_from_topic(self, topic_name):
        topic_latest_message_value_dict = self.get_latest_topic_messages_to_dict_poll_based()

        if topic_latest_message_value_dict[topic_name] is None:
            log.exception("Message is not avialiable from topic: '{topic_name}'")
            sys.exit(1)
        else:
            message = topic_latest_message_value_dict[topic_name]

        return message

    # Method: get latest message value from topic and return it
    def get_latest_msg_val_from_topic(self, topic_name, msg_val_name, default_msg_val=None, precision=3):
        # TODO doc
        topic_latest_message_value_dict = self.get_latest_topic_messages_to_dict_poll_based()

        if topic_latest_message_value_dict[topic_name][msg_val_name] is None:
            log.warning(f"Value: {msg_val_name} is not avialiable from topic: " +
                        f"'{topic_name}'. Setting to default value: '{default_msg_val}'.")
            message_value = default_msg_val
        else:
            message_value = topic_latest_message_value_dict[topic_name][msg_val_name]

        if type(message_value) == float:
            message_value = round(message_value, precision)

        return message_value

    # Method: Produce message to topic
    def produce_message(self, topic_name, msg_value, msg_key="NA"):
        # TODO doc
        # TODO verify if topic name is in producer list? (if not then what?)
        # TODO add callback, since it will not fail on ie. missing brooker

        try:
            self.producer.send(topic_name, value=msg_value, key=msg_key)
            return True
        except Exception as e:
            log.exception(f"Sending message to Kafka failed with message: '{e}'.")
            sys.exit(1)

    # Method: latest kafka to Pandas
    # TODO: add such that it updates latest msg to attribute, then make function which extract from it and recalls it?
    # TODO: build in timeout to avopid endless polling or init last offset before polling such that it does not change durring poll
    # TODO: document
    # TODO: lav try/catch (1 eller flere)
    def get_kafka_messages_to_pandas_dataframe(self,
                                               msg_key_filter: str = None,
                                               get_latest_msg_by_key: bool = False,
                                               get_latest_produced_msg_only: bool = True
                                               ) -> pd.DataFrame:
        """
        Construct DataFrame from messages avaliable on consumed topics.

        Creates Pandas DataFrame object from Kafka messages on consumed topics.
        The dataframe will have the follwing columns (reflecting consumer record fields for messages):
        topic, partion, offset, timestamp, key and value.
        Each row in the dataframe will contain the values from each field in message.

        The consumed topics is assigned on object initialisation.
        Filtering on messages keys and offset can be set via parameters.

        Parameters
        ----------
        msg_key_filter : str, optional
            If provided the consumed messages will be filtered by field "key" on messages.
            (default is None, which means no filtering is done).
        get_latest_msg_by_key : bool, optional
            If set true, only the
            (default is False, which mean)
            Note: The parameter will be ignored if msg_key_filter is set to None.
        get_latest_produced_msg_only: bool, optional
            will either follow offset og consume alle records

        Returns
        -------
        DataFrame

        Examples
        --------
        1. defualt return all
        2. filter by key
        3. latest vs. all

        >>> code
        result
        """

        time_begin = time()

        # seek consumer to begging, if all record should be fetch and not only latest produced messages only (the ones not consumed)
        if not get_latest_produced_msg_only:
            self.consumer.seek_to_beginning()

        # init list for holding consumer records
        record_list = []

        # poll data, until last offset has been reached for all topic partitions
        is_polling = True
        while is_polling:

            # poll data from consumer and store in dictionary (topic partition --> list of consumer records for partition)
            topic_partition_record_dict = self.consumer.poll(timeout_ms=self.poll_timeout_ms, max_records=None)

            # process data, if any returned from the poll
            if topic_partition_record_dict:

                # append consumer records from poll to list of consumer records
                record_list = record_list + [record for consumer_record_list in topic_partition_record_dict.values()
                                             for record in consumer_record_list]

            # stop polling when last offset has been reached for all topic partitions, meaning all data polled
            if self.topic_positions_reached_last_offsets(topic_list=self.topics_consumed_list):
                is_polling = False

        log.debug(f"Polling data took {round(time()-time_begin,3)} secounds")

        # construct dictionary for storing values for consumer records
        # TODO: check om denne oprette korrekt type wise?
        # TODO: flyt serializer til init af consumer?
        record_dict = [{'topic': record_list[record].topic,
                        'partition':  record_list[record].partition,
                        'offset': record_list[record].offset,
                        'timestamp':  record_list[record].timestamp,
                        'key': loads(record_list[record].key.decode()),
                        'value': record_list[record].value}
                       for record in range(len(record_list))]

        # make dataframe structure
        time_pandas_frame = time()
        dataframe = pd.DataFrame.from_dict(record_dict)
        log.debug(f"Making pandas dataframe took {round(time()-time_pandas_frame,3)} secounds")

        # filter if choosen
        time_filter = time()
        if msg_key_filter is not None:
            dataframe = self.filter_kafka_data_frame_by_msg_key(dataframe=dataframe, msg_key_filter=msg_key_filter, filter_on_latest_msg_by_key=get_latest_msg_by_key)
        log.debug(f"Filtering pandas dataframe took {round(time()-time_filter,3)} secounds")
        log.debug(f"Extracting Kafka data to pandas dataframe took {time()-time_begin}")

        return dataframe

    # todo lav try/catch
    def filter_kafka_data_frame_by_msg_key(self, dataframe, msg_key_filter, filter_on_latest_msg_by_key=False):
        if not dataframe.empty:
            # filter by key
            dataframe = dataframe[dataframe.key == msg_key_filter]
            if filter_on_latest_msg_by_key:
                # filter by latest offset
                dataframe = dataframe[dataframe.offset == dataframe[dataframe.key == msg_key_filter]["offset"].max()]

        return dataframe

    def extract_value_from_kafka_dataframe(self, dataframe, msg_key_filter):
        dataframe = self.filter_kafka_data_frame_by_msg_key(dataframe=dataframe, msg_key_filter=msg_key_filter, filter_on_latest_msg_by_key=True)
        if not dataframe.empty:
            value = dataframe['value'].values[0]
        else:
            value = None

        return value

    # todo try catch and dok
    def topic_positions_reached_last_offsets(self, topic_list):

        try:
            # init dictionary with Topic -> TopicPartitions
            topic_partitions_dict = self.create_topic_partitions_dict()

            # create list of topic partitions which have not reached last offset
            topic_partitions_not_reached_last_offset = [topic for topic in topic_list
                                                        for topic_partition in topic_partitions_dict[topic]
                                                        if self.consumer.position(topic_partition) < self.consumer.end_offsets([topic_partition])[topic_partition]]

            # If all partitions have been consumed till latest offset, break out of polling loop
            if len(topic_partitions_not_reached_last_offset) == 0:
                return True
            else:
                return False
        except Exception as e:
            log.exception(f"Checking for last offset for topics: '{topic_list}' failed with message '{e}'.")
            sys.exit(1)
