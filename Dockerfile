# Use the official Python image from the Docker Hub
FROM python:3.11-slim

ARG USER=greg
ARG GROUP=greg
ARG APP_DIR=/app

# Set the working directory inside the container
WORKDIR ${APP_DIR}

# Create a group and Create a user and add the user to the group
RUN groupadd ${GROUP} && \
    useradd -ms /bin/bash -g ${GROUP} ${USER}

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Copy the rest of the application code into the container
ADD --chown=root:${GROUP} tailproxy.py ${APP_DIR}/
COPY --chown=root:${GROUP} config/setup.sh ${APP_DIR}/
COPY --chown=root:${GROUP} config/entrypoint.sh /bin/entrypoint

RUN chmod -R 550 ${APP_DIR}/  /bin/entrypoint

# Switch to the new user
USER ${USER}

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
ENTRYPOINT [ "/bin/entrypoint" ]
