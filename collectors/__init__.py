from collectors.abstract import SeleniumCollector, RequestCollector
from collectors.spokeo import Spokeo
from collectors.mylife import MyLife
from collectors.radaris import Radaris

COLLECTORS = (
    Spokeo,
    MyLife,
    Radaris,
)
