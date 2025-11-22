"""
Agentic AI Modülü - Yatırım Kurulu

Farklı rollere bürünmüş 3 yapay zeka ajanı:
- Boğa (Bull): Sadece alım fırsatlarını ve olumlu haberleri savunur
- Ayı (Bear): Riskleri, olumsuzlukları ve satış gerekçelerini savunur
- Hakem (Referee): İkisini dinler ve nihai kararı verir
"""

from .bull_agent import BullAgent
from .bear_agent import BearAgent
from .referee_agent import RefereeAgent
from .investment_board import InvestmentBoard

__all__ = ['BullAgent', 'BearAgent', 'RefereeAgent', 'InvestmentBoard']

