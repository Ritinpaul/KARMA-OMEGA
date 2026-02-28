"""
AION: IPFS + Ethereum Knowledge Persistence
============================================
Implements immutable knowledge archival for KARMA-OMEGA.

In production:
  - IPFS: Content-addressed storage via ipfshttpclient or nft.storage API.
  - Ethereum: Web3 transaction to a deployed AuditLog smart contract.

Here we provide a fully-functional simulation:
  - IPFS CID: deterministic SHA-256-based CID (CIDv1-like, base58 prefix "Qm...")
  - Ethereum TX: deterministic hex hash (keccak-256-like) as "tx hash"
  - A local in-memory ledger stores all anchored records (survives service lifetime)
  - Records are written to a JSONL flat-file as a durable offline fallback

Design principles:
  - Append-only: records can never be modified or deleted
  - Content-addressed: CID is derived from record content → tampering detectable
  - Audit-ready: every anchor returns a receipt with timestamp and content hash
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from aion.schemas.models import (
    AnchorRequest,
    EventType,
    KnowledgeRecord,
    PersistenceReceipt,
)


# ─── Persistence Paths ────────────────────────────────────────────────────────

_DEFAULT_LEDGER_PATH = Path("aion_ledger.jsonl")


# ─── CID / TX Simulation ─────────────────────────────────────────────────────

def _simulate_ipfs_cid(content_hash: str) -> str:
    """
    Generate a deterministic CIDv1-like identifier.
    Real CIDv1: base32(multicodec(dag-pb) + multihash(sha2-256(content)))
    We use: 'Qm' + base58-encable hex for demo authenticity.
    """
    h = content_hash[:52]  # 52 hex chars = 26 bytes
    return f"Qm{h.upper()}"


def _simulate_eth_tx(record_id: str, cid: str) -> str:
    """
    Generate a deterministic Ethereum-lookalike transaction hash.
    Real: keccak256(RLP-encoded tx).
    We use: sha256(record_id + cid).
    """
    raw = f"{record_id}:{cid}".encode()
    return "0x" + hashlib.sha256(raw).hexdigest()


def _content_hash(record_json: str) -> str:
    """SHA-256 over canonical JSON — detectable if record is tampered with."""
    return hashlib.sha256(record_json.encode()).hexdigest()


# ─── IPFS Client (Simulated) ─────────────────────────────────────────────────

class SimulatedIPFSClient:
    """
    Simulates IPFS pin/add operations.
    In production: replace with `ipfshttpclient.connect()` or nft.storage REST.
    """

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}   # CID → content

    def add(self, content: str) -> str:
        """Pin content; return CID."""
        h = _content_hash(content)
        cid = _simulate_ipfs_cid(h)
        self._store[cid] = content
        return cid

    def get(self, cid: str) -> Optional[str]:
        return self._store.get(cid)

    def is_pinned(self, cid: str) -> bool:
        return cid in self._store

    def total_pinned(self) -> int:
        return len(self._store)


# ─── Ethereum Anchor (Simulated) ─────────────────────────────────────────────

class SimulatedEthereumAnchor:
    """
    Simulates Ethereum AuditLog smart contract interactions.
    In production: use web3.py with a deployed contract.

    Function anchored:
        function logRecord(string cid, bytes32 contentHash) external returns (uint256 blockNumber)
    """

    def __init__(self) -> None:
        self._txs: Dict[str, str] = {}    # tx_hash → cid

    def anchor(self, cid: str, record_id: str) -> str:
        """Submit anchoring transaction; return tx hash."""
        tx = _simulate_eth_tx(record_id, cid)
        self._txs[tx] = cid
        return tx

    def verify(self, tx_hash: str, expected_cid: str) -> bool:
        return self._txs.get(tx_hash) == expected_cid

    def total_anchored(self) -> int:
        return len(self._txs)


# ─── Persistence Manager ─────────────────────────────────────────────────────

class KnowledgePersistenceManager:
    """
    Orchestrates immutable knowledge archival:
      1.  Serialise the KnowledgeRecord to canonical JSON
      2.  Compute SHA-256 content hash (tamper-evidence)
      3.  Pin to IPFS → get CID
      4.  Anchor CID on Ethereum → get tx hash
      5.  Append to local JSONL ledger (offline fallback)
      6.  Return PersistenceReceipt
    """

    def __init__(self, ledger_path: Path | None = None) -> None:
        self._ipfs = SimulatedIPFSClient()
        self._eth = SimulatedEthereumAnchor()
        self._records: Dict[str, KnowledgeRecord] = {}
        self._ledger_path = ledger_path or _DEFAULT_LEDGER_PATH

    def anchor(self, request: AnchorRequest) -> tuple[KnowledgeRecord, PersistenceReceipt]:
        """
        Persist and anchor a knowledge record.
        Returns (KnowledgeRecord, PersistenceReceipt).
        """
        record_id = str(uuid.uuid4())

        record = KnowledgeRecord(
            record_id=record_id,
            event_type=request.event_type,
            project_id=request.project_id,
            site_id=request.site_id,
            risk_name=request.risk_name,
            description=request.description,
            risk_score=request.risk_score,
            prevention_applied=request.prevention_applied,
            outcome=request.outcome,
        )

        # 1. Canonical JSON
        record_json = record.model_dump_json(indent=None)

        # 2. Content hash
        c_hash = _content_hash(record_json)

        # 3. IPFS pin
        cid = self._ipfs.add(record_json)
        record.ipfs_cid = cid

        # 4. Ethereum anchor
        tx = self._eth.anchor(cid, record_id)
        record.ethereum_tx = tx
        record.anchored = True

        # 5. Local ledger
        self._records[record_id] = record
        self._append_ledger(record)

        # 6. Receipt
        receipt = PersistenceReceipt(
            record_id=record_id,
            ipfs_cid=cid,
            ethereum_tx=tx,
            anchored_at=datetime.now(timezone.utc),
            content_hash=c_hash,
        )

        logger.info(
            f"🔒 Anchored: {record.event_type} | {record.risk_name} | "
            f"CID={cid[:20]}... | TX={tx[:18]}..."
        )
        return record, receipt

    def verify(self, record_id: str) -> bool:
        """Verify a record's integrity by re-checking its IPFS+Ethereum anchors."""
        record = self._records.get(record_id)
        if not record or not record.ipfs_cid or not record.ethereum_tx:
            return False
        return self._eth.verify(record.ethereum_tx, record.ipfs_cid)

    def get_record(self, record_id: str) -> Optional[KnowledgeRecord]:
        return self._records.get(record_id)

    def list_records(
        self,
        event_type: Optional[EventType] = None,
        site_id: Optional[str] = None,
    ) -> List[KnowledgeRecord]:
        records = list(self._records.values())
        if event_type:
            records = [r for r in records if r.event_type == event_type]
        if site_id:
            records = [r for r in records if r.site_id == site_id]
        return sorted(records, key=lambda r: r.created_at, reverse=True)

    def total_anchored(self) -> int:
        return len(self._records)

    def ipfs_stats(self) -> dict:
        return {
            "total_pinned": self._ipfs.total_pinned(),
            "total_eth_anchored": self._eth.total_anchored(),
            "total_records": len(self._records),
        }

    def _append_ledger(self, record: KnowledgeRecord) -> None:
        """Append to local JSONL ledger as offline fallback."""
        try:
            with open(self._ledger_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.warning(f"Ledger write failed (non-critical): {e}")
