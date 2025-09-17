import logging
import sys

def get_logger(name:str=__name__,log_file:str=None,level=logging.INFO):
    logger=logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        formatter=logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        ch=logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if log_file:
            fh=logging.FileHandler(log_file,encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger