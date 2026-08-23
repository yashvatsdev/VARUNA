"""
VARUNA GRID v2 — the locked contract package.

Every other package imports FROM here and never redefines these types.
Changing anything in this package requires an ADR (see docs/adr/).

  evidence.py  EvidenceEnvelope, trust/validity vocabulary, Bounded Evidence Influence
  states.py    case state vector (4 axes), mission FSM, invariant checker
  phi.py       structured Phi object with first-class diagnostics
  decision.py  attribution output, Validity/Uncertainty Gate
  schemas.py   v1 domain payloads (detections, AIS, forecasts, tasking, evidence packs)
"""

from varuna_contracts.evidence import (
    AnomalyFlag,
    CalibrationState,
    DegradationState,
    EnvelopedArtifact,
    EvidenceEnvelope,
    Provenance,
    QualityMetrics,
    TrustState,
    UncertaintyBlock,
    ValidityState,
)
from varuna_contracts.states import (
    CaseLifecycle,
    CaseStateVector,
    EvidenceState,
    InvestigationState,
    MissionRecord,
    MissionState,
    OutcomeState,
    ResponseState,
    check_case_invariants,
    is_legal_mission_transition,
)
from varuna_contracts.phi import (
    ConvergenceFlag,
    PhiDiagnostics,
    PhiField,
    SensitivityBlock,
    SpatialMode,
    TimeDistribution,
)
from varuna_contracts.decision import (
    AttributionResultV2,
    CandidateScore,
    DecisionState,
    GateCheck,
    LatentFinding,
    PriorContribution,
    ValidityGateResult,
)
from varuna_contracts.schemas import (
    AISGap,
    AISPoint,
    AssetTasking,
    AssetType,
    BBox,
    DarkVesselDetection,
    EvidenceManifest,
    ForwardForecast,
    GeoPoint,
    LandfallPrediction,
    LookAlikeType,
    SearchBox,
    SlickClass,
    SlickDetection,
    VesselTrack,
    VesselType,
)

CONTRACT_VERSION = "2.0.0"

__all__ = [
    "CONTRACT_VERSION",
    # evidence
    "EvidenceEnvelope", "EnvelopedArtifact", "Provenance", "QualityMetrics",
    "UncertaintyBlock", "TrustState", "ValidityState", "DegradationState",
    "CalibrationState", "AnomalyFlag",
    # states
    "CaseStateVector", "InvestigationState", "OutcomeState", "ResponseState",
    "EvidenceState", "CaseLifecycle", "MissionState", "MissionRecord",
    "check_case_invariants", "is_legal_mission_transition",
    # phi
    "PhiField", "PhiDiagnostics", "SensitivityBlock", "SpatialMode",
    "TimeDistribution", "ConvergenceFlag",
    # decision
    "AttributionResultV2", "CandidateScore", "DecisionState", "LatentFinding",
    "PriorContribution", "ValidityGateResult", "GateCheck",
    # domain payloads
    "GeoPoint", "BBox", "SlickDetection", "SlickClass", "LookAlikeType",
    "AISPoint", "AISGap", "VesselTrack", "VesselType", "DarkVesselDetection",
    "LandfallPrediction", "ForwardForecast", "SearchBox", "AssetTasking",
    "AssetType", "EvidenceManifest",
]
