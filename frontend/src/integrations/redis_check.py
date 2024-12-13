import redis
client = redis.StrictRedis(host="127.0.0.1", port=6379)
print(client.ping())