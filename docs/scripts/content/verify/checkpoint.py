#!/usr/bin/env python3
"""
PROJECT-OMEGA: Progress Verification Script
Verifies completion of phases and modules
"""

import sys
import os
from pathlib import Path

def check_phase_completion(phase_num):
    """Check if a phase is complete"""
    phase_dirs = {
        1: "docs/phases/phase1-infra",
        2: "docs/phases/phase2-foundations",
        3: "docs/phases/phase3-transformers",
        4: "docs/phases/phase4-quantization",
        5: "docs/phases/phase5-finetuning",
        6: "docs/phases/phase6-rag",
        7: "docs/phases/phase7-agentic"
    }

    phase_dir = Path(phase_dirs[phase_num])
    if not phase_dir.exists():
        return False, f"Phase {phase_num} directory not found"

    checkpoint = phase_dir / "CHECKPOINT.md"
    if not checkpoint.exists():
        return False, f"Checkpoint file missing for Phase {phase_num}"

    print(f"✓ Phase {phase_num}: FOUND")
    return True, "OK"

def main():
    print("PROJECT-OMEGA Progress Verification")
    print("=" * 50)
    print()

    # Check all phases
    print("Phase Completion Status:")
    print("-" * 50)

    completed_phases = 0
    for phase in range(1, 8):
        exists, msg = check_phase_completion(phase)
        if exists:
            completed_phases += 1

    print()
    print(f"Phases Completed: {completed_phases}/7")

    # Overall progress
    print()
    print("=" * 50)
    print(f"Overall Progress: {completed_phases / 7 * 100:.1f}%")
    print("=" * 50)

if __name__ == "__main__":
    main()
