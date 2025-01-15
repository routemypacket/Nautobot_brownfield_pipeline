FROM deadtree101/netauto:latest
# Install Git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
# Set working directory
WORKDIR /app
# Re-add the main application (if needed)
COPY . /app
