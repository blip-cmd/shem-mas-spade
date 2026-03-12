"""Convenience entry point for the Day 6 SHEM stress test."""

import asyncio

from main import run_stress_test


if __name__ == "__main__":
	asyncio.run(run_stress_test())