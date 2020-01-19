# -*- coding: utf-8 -*

import redis

import json


redis = redis.StrictRedis(host='127.0.0.1', port=6379,password='redis2017', db=0, decode_responses=True)
#redis = redis.Redis(host='127.0.0.1', port=6379,password='redis2017',db=0)

def writeToCollection(tableName, value):

     redis.rpush(tableName,value)


def clearCollection(tableName):

     collection = redis.lrange(tableName,0,-1)

     for ele in collection:

         redis.lrem(tableName,0, ele)

#写入集合，元素不可重复

def writeToSet(tableName, value):

     redis.sadd(tableName,value)

    
def clearSet(tableName):
    
     set = redis.smembers(tableName)
     
     print('==>list type:{},list:{}'.format(type(list),list))
     print(len(set))
     for ele in set:

         redis.srem(tableName, ele)
     

#返回set集合
def getSet(tableName):
 
    return redis.smembers(tableName)    

if __name__ == "__main__":

     
     '''
     redis.set("year",'2019')

     print(str(redis.get("year")))

     list = ['A','B','C']

     key='myList'

     writeToList(key,list,redis)

     readList(key,redis)
     
     '''
     
     writeToSet('table','a')
     writeToSet('table','b')
     clearSet('table')
     set=getSet('table')

     print(len(set))
   

     
