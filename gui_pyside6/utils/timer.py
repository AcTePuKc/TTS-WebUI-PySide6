import time
from contextlib import contextmanager


@contextmanager
def Timer():
    start_time = time.time()
    yield
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Generated in", "{:.3f}".format(elapsed_time), "seconds")
