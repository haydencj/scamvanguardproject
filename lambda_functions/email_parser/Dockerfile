# Use AWS Lambda Python 3.13 base image
FROM public.ecr.aws/lambda/python:3.13

# Copy function code to Lambda task root
COPY email_parser.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["email_parser.handler"]

