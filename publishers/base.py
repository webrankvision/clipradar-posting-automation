from abc import ABC, abstractmethod
from models import ContentPackage, PostResult


class BasePublisher(ABC):
    platform_name: str = ""

    @abstractmethod
    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        """Upload and publish the video. Returns a PostResult."""
        pass

    def _result(self, success: bool, post_id=None, url=None, error=None) -> PostResult:
        return PostResult(
            platform=self.platform_name,
            success=success,
            post_id=post_id,
            url=url,
            error=str(error) if error else None,
        )
