In this page you will find our recommended way of installing Docker on your machine. 
This guide is made for OSX users.

## Install Docker

First install Docker using [Homebrew](https://brew.sh/)
```
$ brew install docker
```

You can then install [Docker Desktop](https://docs.docker.com/get-docker/) if you wish, or use `docker-machine`. As we prefer the second option, we will only document this one.

## Setup your Docker

Install `docker-machine`
```
$ brew install docker-machine
```

Then install [VirtualBox](https://www.virtualbox.org/) with [Homebrew Cask](https://github.com/Homebrew/homebrew-cask) to get a driver for your Docker machine
```
$ brew cask install virtualbox
```

You may need to enter your password and authorize the application in your `System Settings` > `Security & Privacy`.

Create now a new machine, set it up as default and connect your shell to it (here we use zsh. The commands should anyway be displayed in each steps' output)

```
$ docker-machine create --driver virtualbox default
$ docker-machine env default
$ eval "$(docker-machine env default)"
```

Now you're all setup to use our provided Docker image!

## Build the image

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
tox -e py36-django31
```

If you'd like to sue an env other that `py36-django31`, run `tox --listenvs` to see the list of available envs.
Feel free to contact us if you have any questions.
