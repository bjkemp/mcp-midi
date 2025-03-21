FROM python:3.10-slim

WORKDIR /app

# Copy the package files
COPY pyproject.toml setup.py README.md uv.lock ./
COPY src ./src

# Install uv
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Install dependencies using uv
RUN uv pip install -e .

# Run the server
ENTRYPOINT ["mcp-midi"]
