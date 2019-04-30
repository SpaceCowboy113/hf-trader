from datetime import datetime


def get_epoch(zulu_date: str) -> float:
    ''' Returns epoch (as a float in seconds) from zulu formatted date string
    (zulu date strings are given by coinbase)
    '''

    return datetime.strptime(zulu_date, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()


def get_timestamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
