from datetime import datetime
from typing import Optional


class Experiment(object):
    def __init__(
        self,
        ident: Optional[int] = None,
        version: int = 3,
        purpose: str = "",
        comments: str = "",
        public: bool = False,
        deleted: bool = False,
        sources: str = "",
        experimentName: str = "",
        gateVersion: int = 0,
        createdAt: Optional[str] = None,
        updatedAt: Optional[str] = None,
        primaryResearcherId: Optional[int] = None,
        principalInvestigatorId: Optional[int] = None,
        uploaderId: Optional[int] = None,
        projectId: Optional[int] = None,
        clonedFrom: Optional[int] = None,
        createdFrom: Optional[int] = None,
        childType: Optional[int] = None,
        createdFromUrl: Optional[int] = None,
        publishedReportId: Optional[int] = None,
    ):
        self.id = ident
        self.version = version
        self.purpose = purpose
        self.comments = comments
        self.public = public
        self.deleted = deleted
        self.sources = sources
        self.experimentName = experimentName
        self.gateVersion = gateVersion
        self.createdAt = (
            datetime.fromisoformat(createdAt.rstrip("Z"))
            if createdAt is not None
            else None
        )
        self.updatedAt = (
            datetime.fromisoformat(updatedAt.rstrip("Z"))
            if updatedAt is not None
            else None
        )
        self.primaryResearcherId = primaryResearcherId
        self.principalInvestigatorId = principalInvestigatorId
        self.uploaderId = uploaderId
        self.projectId = projectId
        self.clonedFrom = clonedFrom
        self.createdFrom = createdFrom
        self.childType = childType
        self.createdFromUrl = createdFromUrl
        self.publishedReportId = publishedReportId

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.experimentName}: {self.id}"

    def __getitem__(self, item):
        return getattr(self, item)

    def print_details(self):
        print(
            f"id: {self.id}\n"
            f"version: {self.version}\n"
            f"purpose: {self.purpose}\n"
            f"comments: {self.comments}\n"
            f"public: {self.public}\n"
            f"deleted: {self.deleted}\n"
            f"sources: {self.sources}\n"
            f"experimentName: {self.experimentName}\n"
            f"gateVersion: {self.gateVersion}\n"
            f"createdAt: {self.createdAt}\n"
            f"updatedAt: {self.updatedAt}\n"
            f"primaryResearcherId: {self.primaryResearcherId}\n"
            f"principalInvestigatorId: {self.principalInvestigatorId}\n"
            f"uploaderId: {self.uploaderId}\n"
            f"projectId: {self.projectId}\n"
            f"clonedFrom: {self.clonedFrom}\n"
            f"createdFrom: {self.createdFrom}\n"
            f"childType: {self.childType}\n"
            f"createdFromUrl: {self.createdFromUrl}\n"
            f"publishedReportId: {self.publishedReportId}"
        )

    @classmethod
    def from_dict(cls, source):
        exp = cls()

        exp.id = source["id"]
        exp.version = source["version"]
        exp.purpose = source["purpose"]
        exp.comments = source["comments"]
        exp.public = source["public"]
        exp.deleted = source["deleted"]
        exp.sources = source["sources"]
        exp.experimentName = source["experimentName"]
        exp.gateVersion = source["gateVersion"]
        exp.createdAt = (
            datetime.fromisoformat(source["createdAt"].rstrip("Z"))
            if source["createdAt"] is not None
            else None
        )
        exp.updatedAt = (
            datetime.fromisoformat(source["updatedAt"].rstrip("Z"))
            if source["updatedAt"] is not None
            else None
        )
        exp.primaryResearcherId = source["primaryResearcherId"]
        exp.principalInvestigatorId = source["principalInvestigatorId"]
        exp.uploaderId = source["uploaderId"]
        exp.projectId = source["projectId"]
        exp.clonedFrom = source["clonedFrom"]
        exp.createdFrom = source["createdFrom"]
        exp.childType = source["childType"]
        exp.createdFromUrl = source["createdFromUrl"]
        exp.publishedReportId = source["publishedReportId"]
        return exp


# class ExperimentList(list):

#     def __init__():
