import random

def get_density():
    return {
        'North': random.randint(10, 100),
        'South': random.randint(10, 100),
        'East': random.randint(10, 100),
        'West': random.randint(10, 100)
    }
