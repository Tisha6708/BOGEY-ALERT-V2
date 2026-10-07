from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassificationResult:
    is_sensitive: bool
    sensitivity_level: str
    category: Optional[str]
    confidence: float


class SensitiveFileClassifier:
    """
    Local metadata-based sensitive-file classifier.

    IMPORTANT:
    File contents are NOT uploaded to the backend.

    Classification is performed locally using:
    - filename patterns
    - extension
    - location
    - combinations of signals

    The classifier is intentionally conservative so that ordinary
    development and personal files are not automatically treated
    as sensitive.
    """

    # ---------------------------------------------------------
    # HIGH-CONFIDENCE SENSITIVE KEYWORDS
    # ---------------------------------------------------------

    HIGH_RISK_KEYWORDS = {
        "confidential",
        "restricted",
        "secret",
        "credentials",
        "credential",
        "password",
        "passwords",
        "payroll",
        "salary",
        "customer_data",
        "customer-data",
        "employee_data",
        "employee-data",
        "financial_report",
        "financial-report",
        "private_key",
        "private-key",
        "access_token",
        "access-token",
        "api_key",
        "api-key",
        "bank_account",
        "bank-account",
    }

    # ---------------------------------------------------------
    # MEDIUM-RISK BUSINESS TERMS
    # ---------------------------------------------------------

    MEDIUM_RISK_KEYWORDS = {
        "finance",
        "employee",
        "customer",
        "client",
        "invoice",
        "contract",
        "database",
        "backup",
    }

    # ---------------------------------------------------------
    # CREDENTIAL / KEY MATERIAL
    # ---------------------------------------------------------

    CREDENTIAL_EXTENSIONS = {
        ".pem",
        ".key",
        ".pfx",
        ".p12",
    }

    # ---------------------------------------------------------
    # DATA FILES
    # ---------------------------------------------------------

    DATA_EXTENSIONS = {
        ".csv",
        ".xlsx",
        ".xls",
        ".json",
        ".sql",
        ".db",
        ".sqlite",
    }

    # ---------------------------------------------------------
    # DOCUMENT FILES
    # ---------------------------------------------------------

    DOCUMENT_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
    }

    # ---------------------------------------------------------
    # COMMON DEVELOPMENT FILES
    #
    # These are NOT sensitive by extension alone.
    # They remain observable filesystem events.
    # ---------------------------------------------------------

    DEVELOPMENT_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".css",
        ".html",
        ".xml",
        ".yml",
        ".yaml",
        ".md",
    }

    def classify(
        self,
        file_path: str,
        directory_type: Optional[str] = None,
    ) -> ClassificationResult:

        path = Path(file_path)

        filename = path.name.lower().strip()
        extension = path.suffix.lower()

        # Remove extension from the filename so keyword matching
        # works on the actual filename rather than the extension.
        filename_without_extension = path.stem.lower().strip()

        # ---------------------------------------------------------
        # 1. CREDENTIAL / KEY MATERIAL
        # ---------------------------------------------------------

        if extension in self.CREDENTIAL_EXTENSIONS:
            return ClassificationResult(
                is_sensitive=True,
                sensitivity_level="critical",
                category="credential_material",
                confidence=0.98,
            )

        # ---------------------------------------------------------
        # 2. EXPLICIT HIGH-RISK FILENAME
        #
        # Examples:
        #   confidential_report.docx
        #   employee_data.xlsx
        #   password_list.txt
        #   private_key.pem
        # ---------------------------------------------------------

        high_risk_found = self._find_high_risk_keyword(
            filename_without_extension
        )

        if high_risk_found:
            return ClassificationResult(
                is_sensitive=True,
                sensitivity_level="high",
                category="confidential_data",
                confidence=0.95,
            )

        # ---------------------------------------------------------
        # 3. MEDIUM-RISK BUSINESS DATA
        #
        # Data formats + business keyword:
        #
        #   customer_data.csv
        #   employee_database.xlsx
        #   finance_backup.sql
        #
        # A generic file such as:
        #
        #   report.csv
        #
        # is NOT automatically sensitive.
        # ---------------------------------------------------------

        medium_keyword_found = self._find_medium_keyword(
            filename_without_extension
        )

        if (
            medium_keyword_found
            and extension in self.DATA_EXTENSIONS
        ):
            return ClassificationResult(
                is_sensitive=True,
                sensitivity_level="high",
                category="business_data",
                confidence=0.88,
            )

        # ---------------------------------------------------------
        # 4. EXPLICIT BUSINESS DOCUMENT
        #
        # Documents are sensitive only when the filename contains
        # a reasonably specific business keyword.
        #
        # Examples:
        #   employee_contract.docx
        #   customer_invoice.pdf
        #   finance_contract.pdf
        #
        # Generic:
        #   report.docx
        #   resume.docx
        #   project_report.docx
        #
        # remain non-sensitive.
        # ---------------------------------------------------------

        if (
            medium_keyword_found
            and extension in self.DOCUMENT_EXTENSIONS
        ):
            return ClassificationResult(
                is_sensitive=True,
                sensitivity_level="medium",
                category="business_document",
                confidence=0.78,
            )

        # ---------------------------------------------------------
        # 5. COMPANY WORKSPACE + DATA FILE
        #
        # A data file inside an explicitly identified company
        # workspace is treated as potentially sensitive.
        #
        # This does NOT apply to normal Desktop/Downloads/
        # Documents locations.
        # ---------------------------------------------------------

        if (
            directory_type == "company_workspace"
            and extension in self.DATA_EXTENSIONS
        ):
            return ClassificationResult(
                is_sensitive=True,
                sensitivity_level="medium",
                category="company_data",
                confidence=0.70,
            )

        # ---------------------------------------------------------
        # 6. DEVELOPMENT FILES
        #
        # .py, .js, .jsx, etc. are monitored but are NOT sensitive
        # simply because of their extension.
        # ---------------------------------------------------------

        if extension in self.DEVELOPMENT_EXTENSIONS:
            return ClassificationResult(
                is_sensitive=False,
                sensitivity_level="none",
                category=None,
                confidence=0.0,
            )

        # ---------------------------------------------------------
        # 7. EVERYTHING ELSE
        # ---------------------------------------------------------

        return ClassificationResult(
            is_sensitive=False,
            sensitivity_level="none",
            category=None,
            confidence=0.0,
        )

    # =============================================================
    # KEYWORD HELPERS
    # =============================================================

    @classmethod
    def _find_high_risk_keyword(
        cls,
        filename: str,
    ) -> Optional[str]:
        """
        Find an explicit high-risk keyword in the filename.

        Supports filenames such as:
            confidential_report
            employee_data
            private-key
            api_key
        """

        normalized = (
            filename
            .replace("-", "_")
            .replace(" ", "_")
        )

        for keyword in cls.HIGH_RISK_KEYWORDS:
            normalized_keyword = (
                keyword
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_keyword in normalized:
                return keyword

        return None

    @classmethod
    def _find_medium_keyword(
        cls,
        filename: str,
    ) -> Optional[str]:
        """
        Find a business-related keyword in the filename.
        """

        normalized = (
            filename
            .replace("-", "_")
            .replace(" ", "_")
        )

        for keyword in cls.MEDIUM_RISK_KEYWORDS:
            normalized_keyword = (
                keyword
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_keyword in normalized:
                return keyword

        return None