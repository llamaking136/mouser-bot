# import stdlib
# import loguru
import threading
import time
# logger = loguru.logger

__threads = {}
__threads_should_close = False

def __thread_func(func, args, name):
    # logger.info("thread " + name + " start")
    while not __threads_should_close:
        func(*args)
    # logger.info("thread " + name + " stop")

def _start_thread(func, args, name):
    thread = threading.Thread(target = __thread_func, args = (func, args, name))
    __threads[name] = {"thread": thread, "running": True, "function": func}
    thread.start()

def _stop_threads():
    global __threads_should_close
    __threads_should_close = True

if __name__ == "__main__":
    def test():
        # print("test")
        # time.sleep(1)
        while not __threads_should_close: pass

    _start_thread(test, (), "test")
    
    time.sleep(5)

    # logger.debug("Killing all threads?")
    _stop_threads()
