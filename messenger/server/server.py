import grpc
import threading
import queue

from messenger.proto import messenger_pb2
from messenger.proto import messenger_pb2_grpc
from concurrent import futures
from google.protobuf.timestamp_pb2 import Timestamp

class Server(messenger_pb2_grpc.MessengerServerServicer):
    def __init__(self):
        self._messenges_for_clients: list[queue.SimpleQueue] = []
        self._lock = threading.Lock()

    def SendMessage(self, request, context):
        with self._lock:
            timestamp = Timestamp()
            timestamp.GetCurrentTime()
            for clients in self._messenges_for_clients:
                clients.put(messenger_pb2.ReadResponse(author=request.author, text=request.text, sendTime=timestamp))
            return messenger_pb2.SendResponse(sendTime = timestamp)    
        
    
    def ReadMessages(self, request, context):
        clients_number = 0
        with self._lock:
            clients_number = len(self._messenges_for_clients)
            self._messenges_for_clients.append(queue.SimpleQueue())
        while True:
            yield self._messenges_for_clients[clients_number].get()
        
    
if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messenger_pb2_grpc.add_MessengerServerServicer_to_server(Server(), server)
    server.add_insecure_port('0.0.0.0:51075')
    server.start()
    server.wait_for_termination(timeout=None)