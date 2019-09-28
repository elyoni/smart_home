from enum import Enum
import traceback


class TopicFields(Enum):
    PREFIX = 0
    DEVICE_TYPE = 1
    DEVICE_ID = 2
    ACTION = 3


class TopicParser(object):
    def __init__(self, topic):
        super().__init__()
        self._topic = topic.split("/")

    def get_prefix(self):
        """Return first topic."""
        try:
            return str(self._topic[TopicFields.PREFIX.value])
        except IndexError:
            print("error")
            traceback.format_exc()
            return None

    def get_device_type(self):
        try:
            return str(self._topic[TopicFields.DEVICE_TYPE.value])
        except IndexError:
            traceback.format_exc()
            print("error")
            return None

    def get_device_id(self):
        try:
            return str(self._topic[TopicFields.DEVICE_ID.value])
        except IndexError:
            print("error")
            traceback.format_exc()
            return None

    def get_action(self):
        try:
            return str(self._topic[TopicFields.ACTION.value])
        except IndexError:
            print("error")
            traceback.format_exc()
            return None

    def is_valid_topic(self):
        if self.get_prefix() != "device":
            print("Error Prefix topic doesn't start with 'device'")
            return False
        if self.get_action() != "connect" or\
                self.get_action() != "disconnect" or\
                self.get_action() != "set" or\
                self.get_action() != "get" or\
                self.get_action() != "update":
            print("Error Unknown action, only valid action are:")
            print("\t[connect, disconnect, set, get, update]")
            return False
        return True


if __name__ == '__main__':
    a = Topic("/device/lamp/1/set")
    print(a.get_prefix())
    print(a.get_device_type())
    print(a.get_device_id())
    print(a.get_action())
