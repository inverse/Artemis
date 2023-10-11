import os
from typing import Any, Callable, Dict, List

from artemis.reporting.base.language import Language
from artemis.reporting.base.normal_form import (
    NormalForm,
    get_domain_normal_form,
    get_domain_score,
)
from artemis.reporting.base.report import Report
from artemis.reporting.base.report_type import ReportType
from artemis.reporting.base.reporter import Reporter
from artemis.reporting.base.templating import ReportEmailTemplateFragment
from artemis.reporting.utils import get_top_level_target


class DomainExpirationScannerReporter(Reporter):
    CLOSE_DOMAIN_EXPIRATION_DATE = ReportType("close_domain_expiration_date")

    @staticmethod
    def create_reports(task_result: Dict[str, Any], language: Language) -> List[Report]:
        if task_result["headers"]["receiver"] != "domain_expiration_scanner":
            return []

        if not task_result["status"] == "INTERESTING":
            return []

        if not isinstance(task_result["result"], dict):
            return []

        data = task_result["result"]
        expiration_date_from_result = data["expiration_date"]
        expiration_date = expiration_date_from_result.strftime("%d-%m-%Y")

        return [
            Report(
                top_level_target=get_top_level_target(task_result),
                target=task_result["payload"]["domain"],
                report_type=DomainExpirationScannerReporter.CLOSE_DOMAIN_EXPIRATION_DATE,
                additional_data={"expiration_date": expiration_date},
                timestamp=task_result["created_at"],
            )
        ]

    @staticmethod
    def get_email_template_fragments() -> List[ReportEmailTemplateFragment]:
        return [
            ReportEmailTemplateFragment.from_file(
                os.path.join(os.path.dirname(__file__), "template_close_domain_expiration_scanner.jinja2"),
                priority=5,
            ),
        ]

    @staticmethod
    def get_scoring_rules() -> Dict[ReportType, Callable[[Report], List[int]]]:
        """See the docstring in the parent class."""
        return {
            DomainExpirationScannerReporter.CLOSE_DOMAIN_EXPIRATION_DATE: lambda report: [
                get_domain_score(report.target)
            ]
        }

    @staticmethod
    def get_normal_form_rules() -> Dict[ReportType, Callable[[Report], NormalForm]]:
        """See the docstring in the Reporter class."""
        return {
            DomainExpirationScannerReporter.CLOSE_DOMAIN_EXPIRATION_DATE: lambda report: Reporter.dict_to_tuple(
                {
                    "type": report.report_type,
                    "target": get_domain_normal_form(report.target),
                    "message": report.additional_data["expiration_date"],
                }
            )
        }
