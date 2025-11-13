import subprocess
import asyncio
import json
import logging
from typing import List
from pathlib import Path

from models import Vulnerability, SeverityLevel
from config import Config

logger = logging.getLogger(__name__)


class ImageScannerService:
    """
    Orchestrates Docker image scanning using Trivy.
    Responsible for running the scanner and parsing results.
    """

    SEVERITY_ORDER = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
        "UNKNOWN": 4,
    }

    def __init__(self, scanner_tool: str = "trivy"):
        self.scanner_tool = scanner_tool
        self._validate_scanner()

    def _validate_scanner(self) -> None:
        """Check if Trivy is available."""
        try:
            result = subprocess.run(
                [self.scanner_tool, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(f"{self.scanner_tool} not found or not working")
            logger.info(f"Scanner validation successful: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Trivy not found. Install it: https://github.com/aquasecurity/trivy"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to validate scanner: {str(e)}")

    async def scan_image(self, image_name: str) -> List[Vulnerability]:
        """
        Scan Docker image using Trivy and return vulnerabilities.

        Args:
            image_name: Docker image name (e.g., 'nginx:latest')

        Returns:
            List of Vulnerability objects sorted by severity
        """
        logger.info(f"Starting scan of image: {image_name}")

        try:
            trivy_output = await self._run_trivy_scan_async(image_name)
            vulnerabilities = self._parse_trivy_output(trivy_output)
            filtered = self._filter_by_severity(vulnerabilities, Config.MIN_SEVERITY)

            logger.info(f"Found {len(filtered)} vulnerabilities in {image_name}")
            return filtered

        except asyncio.TimeoutError:
            raise RuntimeError(f"Trivy scan timed out after {Config.TRIVY_TIMEOUT_SECONDS}s")
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            raise

    async def _run_trivy_scan_async(self, image_name: str) -> str:
        """
        Execute Trivy scan command asynchronously (non-blocking).

        Args:
            image_name: Docker image name

        Returns:
            JSON output from Trivy
        """
        command = [
            self.scanner_tool,
            "image",
            "--format",
            "json",
            "--severity",
            "LOW,MEDIUM,HIGH,CRITICAL",
            "--scanners",
            "vuln",
            image_name,
        ]

        logger.debug(f"Running command: {' '.join(command)}")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=Config.TRIVY_TIMEOUT_SECONDS
            )

            stdout_text = stdout.decode('utf-8')
            stderr_text = stderr.decode('utf-8')

            if process.returncode not in [0, 1]:
                raise RuntimeError(
                    f"Trivy scan failed (exit code {process.returncode}): {stderr_text or stdout_text}"
                )

            return stdout_text

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

    def _parse_trivy_output(self, json_output: str) -> List[Vulnerability]:
        """
        Parse Trivy JSON output into Vulnerability objects.

        Args:
            json_output: JSON string from Trivy

        Returns:
            List of parsed Vulnerability objects
        """
        vulnerabilities = []

        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Trivy output: {str(e)}")
            return vulnerabilities

        results = data.get("Results", [])

        for result in results:
            target = result.get("Target", "")
            vulns = result.get("Vulnerabilities", [])

            for vuln in vulns:
                try:
                    vulnerability = Vulnerability(
                        cve_id=vuln.get("VulnerabilityID", "UNKNOWN"),
                        package_name=vuln.get("PkgName", ""),
                        installed_version=vuln.get("InstalledVersion", ""),
                        severity=SeverityLevel(vuln.get("Severity", "UNKNOWN")),
                        type=result.get("Type", "UNKNOWN"),
                        description=vuln.get("Title", "") or vuln.get("Description", ""),
                        cvss_score=self._extract_cvss_score(vuln),
                    )
                    vulnerabilities.append(vulnerability)
                except ValueError as e:
                    logger.warning(f"Failed to parse vulnerability: {str(e)}")
                    continue

        return vulnerabilities

    def _extract_cvss_score(self, vuln: dict) -> float:
        """Extract CVSS score from vulnerability data."""
        try:
            cvss = vuln.get("CVSS", {})
            if isinstance(cvss, dict):
                for key in ["nvd", "ghsa"]:
                    if key in cvss:
                        score = cvss[key].get("V3Score") or cvss[key].get("V2Score")
                        if score:
                            return float(score)
            return None
        except Exception:
            return None

    def _filter_by_severity(
        self, vulns: List[Vulnerability], min_severity: str = "MEDIUM"
    ) -> List[Vulnerability]:
        """
        Filter vulnerabilities by minimum severity level.

        Args:
            vulns: List of vulnerabilities
            min_severity: Minimum severity to include

        Returns:
            Filtered list sorted by severity
        """
        min_index = self.SEVERITY_ORDER.get(min_severity.upper(), 999)

        filtered = [
            v
            for v in vulns
            if self.SEVERITY_ORDER.get(v.severity.value.upper(), 999) <= min_index
        ]

        return sorted(
            filtered,
            key=lambda v: self.SEVERITY_ORDER.get(v.severity.value.upper(), 999),
        )
