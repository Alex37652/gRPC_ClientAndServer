# Практика gRPC

## Мессенджер с одним чатом

В рамках проекта реализованы сервер и клиент мессенджера с одним общим чатом. У сервера есть два RPC-метода: послать сообщение в чат (SendMessage) и подключиться к чату и получать бесконечный поток сообщений из чата (ReadMessages).
Клиент при включении открывает поток и скапливать в своём буфере пришедшие сообщения. Также через клиент отправляются сообщения в чат с помощью http интерфейса.

Ниже представлена диаграмма коммуникации с одним серверов, двумя клиентами и двумя пользователями:
```mermaid
flowchart RL
   subgraph Tests
      U1{User 1}
      U2{User 2}
   end

   subgraph Clients with HTTP interface
      C1(fa:fa-comments Client 1)
      C2(fa:fa-comments Client 2)
   end

   subgraph GRPC server
      S(fa:fa-server Server)
   end


   C1 -- SendMessage --> S
   S -. stream ReadMessages .-> C1

   U1 -- POST /sendMessage --> C1
   C1 -- forward messages in /getAndFlushMessages --> U1

   C2 -- SendMessage --> S
   S -. stream ReadMessages .-> C2

   U2 -- POST /sendMessage --> C2
   C2 -- forward messages in /getAndFlushMessages --> U2
```

### Коммуникация между компонентами

На диаграмме ниже представлена последовательность вызовов и ответов между компонентами. Чтобы не переусложнять диаграмму, на ней представлен только один клиент, паттерн коммуникации при двух и более не отличается.

```mermaid
sequenceDiagram
    autonumber
    title Messenger

    participant U as Tests/User
    participant C as Client
    participant S as Server

    C -->>+ S: [grpc stream] open grpc stream ReadMessages

    C ->> C: Created buffer to collect received messages

    U ->>+ C: [http] POST /sendMessage {author, text}

    C ->>+ S: [grpc call] SendMessage {author, text}

    S ->>- C: [grpc response] SendMessage response with {sendTime}

    C ->>- U: [http response] body with {sendTime}

    S ->> C: [message in grpc stream] new message {author, text, sendTime}

    U ->>+ C: [http] POST /sendMessage {author, text}

    C ->>+ S: [grpc call] SendMessage {author, text}

    S ->>- C: [grpc response] SendMessage response with {sendTime}

    C ->>- U: [http response] body with {sendTime}

    S ->> C: [message in grpc stream] new message {author, text, sendTime}

    U ->>+ C: [http] POST /getAndFlushMessages

    C ->> C: Flushed buffer to send to the user, created new one

    C ->>- U: [http response] body with all messages

    S -->- C: client died and closed stream

```

### Интерфейс взаимодействия пользователя с клиентом

Пользователи отправляют на сервер+клиент запросы клиенту, который представляет собой HTTP сервер, поддерживающий два вида запросов:

```
POST /sendMessage
Отправляет одно сообщение в общий чат.
Body:
{
    "author": "Ivan Ivanov",
    "text": "Hey guys"
}

Response:
{
    "sendTime": "..."
}

POST /getAndFlushMessages
Возвращает буферизированные сообщения, удаляя их из буфера.
Response:
[{
    "author": "Ivan Ivanov",
    "text": "Hey guys",
    "sendTime": "..."
},{
    "author": "Petr Petrov",
    "text": "Hey Ivan",
    "sendTime": "..."
}]
```

Примеры с curl:
```
$ curl -X POST localhost:8080/sendMessage -d '{"author": "alice", "text": "hey"}'
{"sendTime":"2021-09-12T10:25:22.454093428Z"}


$ curl -X POST localhost:8080/getAndFlushMessages
[{"author":"alice","text":"hey","sendTime":"2021-09-12T10:25:22.454093428Z"},{"author":"alice","text":"hey guys","sendTime":"2021-09-12T10:25:41.296997047Z"}]
```

