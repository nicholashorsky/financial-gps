"""Calculator exports."""

from fire_engine.calculators.cpp_estimator import CPPEstimate, estimate_cpp_monthly
from fire_engine.calculators.decumulation import DecumulationResult, sequence_withdrawals
from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.fhsa_state import FHSAStateResult, calculate_fhsa_state
from fire_engine.calculators.gis_estimator import GISEstimate, estimate_gis
from fire_engine.calculators.oas_estimator import OASEstimate, estimate_oas_monthly
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.calculators.rrsp_room import RRSPRoomResult, calculate_rrsp_room
from fire_engine.calculators.tfsa_room import TFSARoomResult, calculate_tfsa_room

__all__ = [
    "CPPEstimate",
    "DecumulationResult",
    "FHSAStateResult",
    "GISEstimate",
    "OASEstimate",
    "RRSPRoomResult",
    "TFSARoomResult",
    "calculate_federal_tax",
    "calculate_fhsa_state",
    "calculate_ontario_tax",
    "calculate_rrsp_room",
    "calculate_tfsa_room",
    "estimate_cpp_monthly",
    "estimate_gis",
    "estimate_oas_monthly",
    "sequence_withdrawals",
]
