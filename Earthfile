VERSION 0.8

all:
    ARG EARTHLY_GIT_SHORT_HASH
    ARG IMAGE_TAG=$EARTHLY_GIT_SHORT_HASH
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG BASEIMAGE=ghcr.io/$EARTHLY_GIT_PROJECT_NAME

    BUILD ./server+test
    BUILD --platform=linux/amd64 --platform=linux/arm64 ./server+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/amd64 --platform=linux/arm64 ./viewer+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/amd64 --platform=linux/arm64 ./groovy-randomizer+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/arm64 ./rusty-hunter+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE} --target=aarch64-unknown-linux-musl
    BUILD --platform=linux/amd64 ./rusty-hunter+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE} --target=x86_64-unknown-linux-musl
