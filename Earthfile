VERSION 0.8

ARG --global EARTHLY_GIT_SHORT_HASH
ARG --global IMAGE_TAG=$EARTHLY_GIT_SHORT_HASH
ARG --global EARTHLY_GIT_PROJECT_NAME
ARG --global BASEIMAGE=ghcr.io/$EARTHLY_GIT_PROJECT_NAME

manifests:
    FROM dinutac/jinja2docker:latest
    WORKDIR /manifests
    COPY deploy/* /templates
    LET IMAGE="not used"
    LET NAME="not used"

    FOR tank IN groovy-randomizer rusty-hunter
        SET IMAGE=${BASEIMAGE}/${tank}:${IMAGE_TAG}
        SET NAME=${tank}

        FOR template IN $(ls /templates/*.j2)
            RUN jinja2 ${template} >> ./deploy.yaml
        END

        FOR template IN $(ls /templates/*.yaml)
            RUN cat ${template} >> ./deploy.yaml
        END

    END
    SAVE ARTIFACT ./deploy.yaml AS LOCAL deploy.yaml

all:
    FROM busybox
    ARG NATIVEPLATFORM
    ARG SKIP_TESTS_FOR_CI=false

    IF [[ "${SKIP_TESTS_FOR_CI}" == "true" ]]
        RUN echo "Skipping tests for CI"
    ELSE
        BUILD --platform=${NATIVEPLATFORM} ./server+test
    END

    BUILD --platform=linux/amd64 --platform=linux/arm64 ./server+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/amd64 --platform=linux/arm64 ./viewer+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/amd64 --platform=linux/arm64 ./groovy-randomizer+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE}
    BUILD --platform=linux/arm64 ./rusty-hunter+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE} --target=aarch64-unknown-linux-musl
    BUILD --platform=linux/amd64 ./rusty-hunter+docker --IMAGE_TAG=${IMAGE_TAG} --BASEIMAGE=${BASEIMAGE} --target=x86_64-unknown-linux-musl
    BUILD +manifests
