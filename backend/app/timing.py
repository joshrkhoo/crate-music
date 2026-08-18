import logging
import time

logger = logging.getLogger("crate.timing")


def log_stage(label: str, seconds: float, **fields: object) -> None:
    extra = " ".join(f"{key}={value}" for key, value in fields.items())
    if extra:
        logger.info("crate %s: %.2fs %s", label, seconds, extra)
    else:
        logger.info("crate %s: %.2fs", label, seconds)


def log_call(label: str, **fields: object) -> None:
    extra = " ".join(f"{key}={value}" for key, value in fields.items())
    if extra:
        logger.info("crate %s %s", label, extra)
    else:
        logger.info("crate %s", label)


def stage_start() -> float:
    return time.perf_counter()


def stage_elapsed(start: float) -> float:
    return time.perf_counter() - start
