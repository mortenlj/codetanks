import logging
from enum import Enum

from pydantic_settings import BaseSettings


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class Settings(BaseSettings):
    mode: Mode = Mode.RELEASE
    log_level: str = logging.getLevelName(logging.INFO)
    advertise_address: str = "localhost"
    registration_port: int = 13337
    viewer_port: int = 13338
    grpc_port: int = 13339

    event_port_range: tuple[int, int] = (1337, 1340)
    cmd_port_range: tuple[int, int] = (2337, 2340)

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()

if __name__ == '__main__':
    from pprint import pprint

    pprint(settings.model_dump_json())
