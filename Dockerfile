FROM alpine:latest

# Install necessary packages and tools
RUN apk --no-cache add \
    curl \
    git \
    jq \
    yq \
    && rm -rf /var/cache/apk/*

CMD ["sh"]
