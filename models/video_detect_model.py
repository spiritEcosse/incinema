from _decimal import Decimal
from dataclasses import dataclass
from typing import List, Dict

from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy

from serializer import DataClassJSONSerializer


@dataclass
class BoundingBox(DataClassJSONSerializer):
    Height: float
    Left: float
    Top: float
    Width: float


class FormattedPoint(SerializationStrategy):
    def __init__(self, precision):
        self.precision = precision

    def deserialize(self, value: str) -> Decimal:
        return Decimal(value).quantize(Decimal(self.precision))

    def serialize(self, value: Decimal) -> str:
        return str(value)


@dataclass
class Polygon(DataClassJSONSerializer):
    X: float
    Y: float

    class Config(BaseConfig):
        serialization_strategy = {
            float: FormattedPoint(".0")
        }


@dataclass
class Geometry(DataClassJSONSerializer):
    BoundingBox: BoundingBox
    Polygon: List[Polygon]

    # def angle_exists(self):
    #     """
    #     >>> # CAPSTONE
    #     >>> Geometry.from_dict(\
    #     {\
    #         'BoundingBox': {\
    #             'Height': 0.3466249108314514,\
    #             'Left': 0.48102936148643494,\
    #             'Top': 0.1610700488090515,\
    #             'Width': 0.05190141499042511\
    #         },\
    #         "Polygon": [\
    #         {\
    #             'X': 0.10986328125, 'Y': 0.5712890625\
    #         }, {\
    #             'X': 0.89154052734375, 'Y': 0.5712890625\
    #         }, {\
    #             'X': 0.89154052734375, 'Y': 0.7919921875\
    #         }, {\
    #             'X': 0.10986328125, 'Y': 0.7919921875\
    #         }\
    #     ]\
    #     }).angle_exists()
    #     False
    #     >>> # CREMATED
    #     >>> Geometry.from_dict(\
    #     {\
    #         'BoundingBox': {\
    #             'Height': 0.3466249108314514,\
    #             'Left': 0.48102936148643494,\
    #             'Top': 0.1610700488090515,\
    #             'Width': 0.05190141499042511\
    #         },\
    #         "Polygon": [\
    #             {\
    #                 'X': 0.14677849411964417, 'Y': 0.6305301189422607\
    #             }, {\
    #                 'X': 0.3539269268512726, 'Y': 0.39562931656837463\
    #             }, {\
    #                 'X': 0.3749523460865021, 'Y': 0.45422929525375366\
    #             }, {\
    #                 'X': 0.16780392825603485, 'Y': 0.6891300678253174\
    #             }\
    #         ]\
    #     }).angle_exists()
    #     True
    #     >>> # REMAINS
    #     >>> Geometry.from_dict(\
    #     {\
    #         'BoundingBox': {\
    #             'Height': 0.3466249108314514,\
    #             'Left': 0.48102936148643494,\
    #             'Top': 0.1610700488090515,\
    #             'Width': 0.05190141499042511\
    #         },\
    #         "Polygon": [\
    #             {\
    #                 'X': 0.21222630143165588, 'Y': 0.6559238433837891\
    #             }, {\
    #                 'X': 0.3876423239707947, 'Y': 0.44886502623558044\
    #             }, {\
    #                 'X': 0.408836305141449, 'Y': 0.5056120157241821\
    #             }, {\
    #                 'X': 0.23342028260231018, 'Y': 0.7126708626747131\
    #             }\
    #         ]\
    #     }).angle_exists()
    #     True
    #     >>> # AUGUST
    #     >>> Geometry.from_dict(\
    #     {\
    #         'BoundingBox': {\
    #             'Height': 0.3466249108314514,\
    #             'Left': 0.48102936148643494,\
    #             'Top': 0.1610700488090515,\
    #             'Width': 0.05190141499042511\
    #         },\
    #         "Polygon": [\
    #             {\
    #                 'X': 0.4130859375, 'Y': 0.4111328125\
    #             }, {\
    #                 'X': 0.604248046875, 'Y': 0.4111328125\
    #             }, {\
    #                 'X': 0.604248046875, 'Y': 0.5419921875\
    #             }, {\
    #                 'X': 0.4130859375, 'Y': 0.5419921875\
    #             }\
    #         ]\
    #     }).angle_exists()
    #     False
    #     >>> # FALL
    #     >>> Geometry.from_dict(\
    #     {\
    #         'BoundingBox': {\
    #             'Height': 0.3466249108314514,\
    #             'Left': 0.48102936148643494,\
    #             'Top': 0.1610700488090515,\
    #             'Width': 0.05190141499042511\
    #         },\
    #         "Polygon": [\
    #             {\
    #                 'X': 0.4820109009742737, 'Y': 0.15437597036361694\
    #             }, {\
    #                 'X': 0.5322397351264954, 'Y': 0.15422038733959198\
    #             }, {\
    #                 'X': 0.532885730266571, 'Y': 0.8134135007858276\
    #             }, {\
    #                 'X': 0.48265689611434937, 'Y': 0.8135691285133362\
    #             }\
    #         ]\
    #     }).angle_exists()
    #     False
    #
    #     :return:
    #     """
    #     sorted(self.Polygon, key=lambda p: p.Y)
    #     return self.Polygon[0].Y != self.Polygon[1].Y


@dataclass
class TextDetection(DataClassJSONSerializer):
    Confidence: float
    DetectedText: str
    Geometry: Geometry
    Id: int
    Type: str


@dataclass
class ResponseMetadata(DataClassJSONSerializer):
    HTTPHeaders: Dict[str, str]
    HTTPStatusCode: int
    RequestId: str
    RetryAttempts: int


@dataclass
class VideoMetadata(DataClassJSONSerializer):
    Codec: str
    ColorRange: str
    DurationMillis: int
    Format: str
    FrameHeight: int
    FrameRate: float
    FrameWidth: int


@dataclass
class TextDetections(DataClassJSONSerializer):
    TextDetection: TextDetection
    Timestamp: int

    def commercial_text(self):
        return self.TextDetection.Type == 'WORD'


@dataclass
class VideoDetectModel(DataClassJSONSerializer):
    JobStatus: str
    NextToken: str
    ResponseMetadata: ResponseMetadata
    TextDetections: List[TextDetections]
    TextModelVersion: str
    VideoMetadata: VideoMetadata
