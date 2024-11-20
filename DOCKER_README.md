## Build the image

> Make sure to have [Docker installed](https://docs.docker.com/engine/install/)

```bash
docker build -t algoliasearch-django .
```

## Run the image

You need to provide a few environment variables at runtime to be able to run the image and the test suite.

```bash
docker run -it --rm --env ALGOLIA_APPLICATION_ID=XXXXXX \
                    --env ALGOLIA_API_KEY=XXXXXXXXXXXXXX \
                    -v $PWD:/code -w /app algoliasearch-django bash
```

However, we advise you to export them. That way, you can use [Docker's shorten syntax](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file) to set your variables.

```bash
export ALGOLIA_APPLICATION_ID=XXXXXX
export ALGOLIA_API_KEY=XXX

docker run -it --rm --env ALGOLIA_APPLICATION_ID --env ALGOLIA_API_KEY -v $PWD:/code -w /code algoliasearch-django bash
```

Once your container is running, any changes you make in your IDE are directly reflected in the container.

To launch the tests, you can use this command

```bash
tox -e py313-django51
```

If you'd like to sue an env other that `py313-django51`, run `tox --listenvs` to see the list of available envs.
Feel free to contact us if you have any questions.
