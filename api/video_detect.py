# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-s3-developer-guide/blob/master/LICENSE-SAMPLECODE.)
# Example code for calling Rekognition Video operations
# For more information, see https://docs.aws.amazon.com/rekognition/latest/dg/video.html
import asyncio
import logging
from time import sleep
import aioboto3
from PIL import Image
import imagehash

from models.video_detect_model import TextDetections
from settings import BUCKET_VIDEO

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VideoDetect:
    bucket = BUCKET_VIDEO

    def __init__(self, video_name, s3_key_video, position=1):
        self.video_name = video_name
        self.s3_key_video = s3_key_video
        self.is_commercial = False
        self.position = position

    async def _text_detection(self):
        await asyncio.sleep(self.position * 2)
        # sleep(1)

        session = aioboto3.Session()
        async with session.client("rekognition") as rekognition:
            response = await rekognition.start_text_detection(
                Video={'S3Object': {'Bucket': self.bucket, 'Name': self.s3_key_video}},
            )

            self.startJobId = response['JobId']
            logger.info(f'Start Job Id: {self.startJobId}, file_name: {self.s3_key_video}')

            max_results = 10
            pagination_token = ''
            finished = False

            logger.info(f's3_key : {self.s3_key_video}, file_name: {self.s3_key_video}')
            counter = 1

            while not finished:
                await asyncio.sleep(1 * counter)
                # sleep(1)
                response = await rekognition.get_text_detection(
                    JobId=self.startJobId,
                    MaxResults=max_results,
                    NextToken=pagination_token
                )

                if response['JobStatus'] == 'IN_PROGRESS':
                    logger.info(f'Job is still in progress , startJobId: {self.startJobId}, file_name: {self.s3_key_video}')
                    continue
                if response['JobStatus'] == 'FAILED':
                    raise Exception(f'Label detection failed for {self.s3_key_video}, response: {response}')

                logger.info(f"JobStatus: {response['JobStatus']}, startJobId: {self.startJobId}, file_name: {self.s3_key_video}")

                for text_detection in response['TextDetections']:
                    text_detections = TextDetections.from_dict(text_detection)

                    if text_detections.commercial_text():
                        self.is_commercial = True
                        logger.info(f'Commercial text: {text_detections.to_json()}, file_name: {self.s3_key_video}')
                        break
                else:
                    logger.info(f'Commercial text not found, file_name: {self.s3_key_video}')

                if 'NextToken' in response:
                    pagination_token = response['NextToken']
                else:
                    finished = True

                # counter += 10

    async def run(self):
        await self._text_detection()
        return self.video_name, self.is_commercial


class CompareImage(object):

    def __init__(self, video, source, target):
        self.source = source
        self.target = target
        self.video = video

    def run(self):
        print(f"start {self.source}.")
        hash0 = imagehash.average_hash(Image.open(self.source))
        hash1 = imagehash.average_hash(Image.open(self.target))
        cutoff = 5  # maximum bits that could be different between the hashes.
        diff = hash0 - hash1
        is_commercial = diff < cutoff
        print(f"source : {self.source}, target : {self.target}, diff: {diff}, cutoff: {cutoff}, is_commercial: {is_commercial}")
        return self.video, is_commercial


def func_compare_image(args):
    print("func_compare_image")
    return CompareImage(args[0], args[1], args[2]).run()


if __name__ == "__main__":
    CompareImage().run()
