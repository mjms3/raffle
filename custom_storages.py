from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    bucket_name = 'cboe-raffle-media'
    custom_domain = 'cboe-raffle-media.s3.amazonaws.com'