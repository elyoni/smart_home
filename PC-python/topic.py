from enum import Enum
class TopicFields(Enum):
    PREFIX = 1
    DEVICE_TYPE = 2
    DEVICE_ID = 3
    ACTION = 4

class Topic(object):
    def __init__(self, topic):
        super().__init__()
        self._topic = topic.split("/")
    def get_prefix(self):
        try:
            return self._topic[TopicFields.PREFIX.value]
        except IndexError:
            return None

    def get_device_type(self):
        try:
            return self._topic[TopicFields.DEVICE_TYPE.value]
        except IndexError:
            return None

    def get_device_id(self):
        try:
            return self._topic[TopicFields.DEVICE_ID.value]
        except IndexError:
            return None

    def get_action(self):
        try:
            return self._topic[TopicFields.ACTION.value]
        except IndexError:
            return None

if __name__ == '__main__':
    a = Topic("/device/lamp/1/set")
    print(a.get_prefix())
    print(a.get_device_type())
    print(a.get_device_id())
    print(a.get_action())
