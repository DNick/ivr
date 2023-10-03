from App_creators.config import s3

def get_logo_url_from_course_id(course_id):
    url = s3.generate_presigned_url('get_object', Params={'Bucket': 'mybacket',
                                                            'Key': f'logos/{course_id}.jpg'})
    return url

