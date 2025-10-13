# Use AWS Lambda Python 3.13 base image
FROM public.ecr.aws/lambda/python:3.13

# Copy function code to Lambda task root
COPY ses_feedback_processor.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["ses_feedback_processor.handler"]

