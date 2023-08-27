# Chat_App
This is a Chat Web App which utilizes Websockets for real time message transfer, this chat app works on basis of rooms therefore more than 2 people can participate in a chat and messages will be shared amongst them.

This web app is majorly implemented using python and its frameworks only. HTML,Bootstrap and a little Javascript is also used for various operations here.

## Technologies Used
- Django
- Celery
- Redis
- Daphne
- Postgres
- Django Channels

## How does this work

This chat app works in the same manner as some of chat apps like discord, whatsapp and more, but the working of this is different from them and is defined according to me.

1. First basic working of chat app is simple, a html file sends a ws:// request to our ChatConsumer which is itself a instance asyncwebsocket library and capable of creating rooms and sending messages to all people inside a channel.

The above step is the major step for a simple chat app, but no messages will be persistent after every refresh of the page the previous message will be gone, to prevent this and make the system more reliable I had to design this.

The challenges of a chat app is they are supposed to be async and therefore need to have extremely fast queries for real time updates.
plus the challenge of making the chats persistent was another challenge on top of being fast. I kept all of the things in mind while designing this and the final product of this chat app is quite nice.

1. While people are chatting there has to be a way to store these messages somewhere, using normal django queries or normal database won't be a good idea because these are synchorus and slow ways of dealing with this, therefore I went with redis, That's Right I am taking a caching database where all chats are stored with headers like user_id, username, message, chat_room and all these things are pushed into a list implemented in redis also this pushing action is done asynchorusly using `aioredis` library therefore it doesn't block main event loop. Therefore first requirement of system being fast is almost done.
2. We have messages in redis now, but redis is a memory storage based database, data is not persistent there it can be wiped as soon as power is cut off, we need something to store all these messages in a persistent database and therefore comes our persistent storage database `POSTGRESQL`, The way messags are stored here is as soon as all the users in a specific room disconnects that room, a worker is ran, this worker process is run using python library `celery`, and these workers are based on entirely different machine so they can utililze the sources there, On disconnect only one worker process is ran this is called the master process, this master process then loops through **all the new entries** in redis db and creates more child processes to individually save these on persistent storage that is postgresql. The approach I defined where master processes create even more child processes for their work is called **The Fanout Approach.**

You must be wondering why "all the new entires" is in bold, the reason is redis db will contain all the messages in that chat room but most of these messages could already be saved in our persistent db, so to prevent them from being saved again a initial value is also taken when the first user connects to a specific room this initial value is just the length of all the previous message so our system will be able to identify the new messages. 

Also, the caching we just performed here, where data is cached first and then asynchorusly made persistent is called **write-back caching.**, [Read more about it here](https://github.com/karanpratapsingh/system-design#write-back-cache)

3. So Now we have a perfect system where user can write messages, these new messages are immediately stored on a fast db like redis and then asynchorusly made persistent on a db like postgres, But what about reading, We are able to save all the messages but even now if a person refresh the page he won't see the old messages or new joinees will also not see the old message.
This is because we have configured everything for writing yet, Now we have to configure a system for reading as well.

4. So let's start, We know that redis is fast and we have to use it to quickly load all the previous messages and send it to the new joinee or a person who just refreshed his page(mind it all the messages are stored in javascript on the frontend),this behaves as a log file on memory, only this log file is shown to the user which behaves as previous messages refreshing this log file will erase all of its data, Therefore on every refresh as soon as a websocket connection is established the backend quickly loops through all the entries of that redis db and send its contents in a ordered manner(ordered by timestamp and chat_id) to the new joinee(technically a person who refresheed will also behave as a new joinee only).

5. Now we have a beautifull and fast chat app where people can send messages they are quickly stored and then asynchorusly made persistent, Every new joinee can quickly see these messages whenever he/she reloads.

6. But in above system we have left something very important, Can you guess it?
If you guessed it right congratulations, the thing we have left is loading entries from persistent db to redis. See redis is in memory storage db therefore information can be lost there and its possible that our chats for a chat room might also be deleted, If this happens it will be problematic because our chat app relies on redis to serve old messages to new joinees, if old messages are stored in persistent db and not available in redis there is no point because user will still not see these old messsages, therefore I had to now design a way to load all the previous entires from persistent db to redis.

7. Let's see to it then, Since reading using django orms would be slow, I have yet again used background processes and the fan-out approach for this as well. How it works is whenever a user connects the system checks if a key with the name of that chat_room exists in the redis program loops messages from that key and shows it to the user, but if it is not available we run a master process, this master process queries the postgresql db and find all the previous messages for that specific room in ordered manner(timestamp, chat_id) ascending and then it runs various child processes to push/create these entries into the redis key with the name of this specific chat_room. This approach loads all the messages into redis list and our application then uses this redis list to show all the previous messages to this user. Mind it this loading of messages can be slow at first when a user joins since data is not available in redis yet, but after it loads messages into redis the user can reload the page or any new joinees can join this page and the time for the messages to load would be extremely less compared to the first time a user came to the chat app.

So this is how in general this chat app is design and implemented, The frontend of this app might not be beautifull but what is beautifull is its backend, and as a backend developer that's the one thing I care about the most.
