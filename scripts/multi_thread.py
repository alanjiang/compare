# -*- coding: utf-8 -*


import threading
import time

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED,as_completed
import time

exitFlag = 0


#单线程
class myThread (threading.Thread):   #继承父类threading.Thread
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):  #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数 
        print('Starting {}\n'.format(self.name))
        
        print ("Exiting {}\n".format(self.name))

def reset_time(threadName, delay, counter):
    while counter > 0:
        if exitFlag:
            thread.exit()
        time.sleep(delay)
        
        counter -= 1

def runSingleThreads():

    # 创建新线程
    thread1 = myThread(1, "Thread-1", 1)
    thread2 = myThread(2, "Thread-2", 2)

    # 开启线程
    thread1.start()
    thread2.start()

    print("Exiting Main Thread")




def spider(page):
    
    print(f"crawl task{page} finished\n")
    return page

def runThreadPool ():

    
    with ThreadPoolExecutor(max_workers=30) as t:

        '''
        all_task = [t.submit(spider, page) for page in range(1, 100)]
        '''
        all_task = []
        for page in range(1,100):
            all_task.append(t.submit(spider,page))
            
        wait(all_task, return_when=ALL_COMPLETED)
        print('finished')
        #print(wait(all_task, timeout=2.5))






def runThreadPoolAsComplete():

    
    with ThreadPoolExecutor(max_workers=30) as t:

        '''
        all_task = [t.submit(spider, page) for page in range(1, 100)]
        '''
        all_task = []
        for page in range(1,100):
            all_task.append(t.submit(spider,page))
            
        for future in as_completed(all_task):
            data = future.result()
            print(f"main: {data}")
            
        print('finished')
        #print(wait(all_task, timeout=2.5))

if __name__ == "__main__":

    #runSingleThreads()
    #runThreadPool()
    runThreadPoolAsComplete()
