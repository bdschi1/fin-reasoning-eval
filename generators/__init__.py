"""Problem generators for Financial Reasoning Eval Benchmark."""

from .base import BaseGenerator
from .earnings_surprise import EarningsSurpriseGenerator
from .dcf_sanity import DCFSanityGenerator
from .accounting_red_flags import AccountingRedFlagGenerator
from .catalyst_identification import CatalystIdentificationGenerator
from .formula_audit import FormulaAuditGenerator
from .financial_statement import FinancialStatementGenerator

__all__ = [
    'BaseGenerator',
    'EarningsSurpriseGenerator',
    'DCFSanityGenerator',
    'AccountingRedFlagGenerator',
    'CatalystIdentificationGenerator',
    'FormulaAuditGenerator',
    'FinancialStatementGenerator',
]
