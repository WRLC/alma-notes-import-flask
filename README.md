# alma-notes-import-flask
Flask app for batch updating fields in Alma item records by barcode from a CSV file

## Local development

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [local-dev-traefik](https://github.com/WRLC/local-dev-traefik) (for networking between containers)
- [aladin-sp-v3](https://github.com/WRLC/aladin-sp-v3) (for authentication)

### Installation

```bash
git clone git@github.com:WRLC/alma-notes-import-flask.git  # clone the repository
cd alma-notes-import-flask  # change to the project directory
docker-compose up -d  # start the container
```

Site will be available at [https://almanotesimport.wrlc.localhost](https://almanotesimport.wrlc.localhost)

### Updating packages

Packages are managed with [Poetry](https://python-poetry.org/).

```bash
docker exec -i -t almanotesimport /bin/bash  # open a shell in the container
poetry show --outdated  # check for outdated packages
poetry update <package>  # repeat for each outdated package
exit # exit the shell
git checkout -b update/<YYYY-MM-DD>  # create a new branch
git add .  # stage all changes
git commit -m "Update packages"  # commit changes
git push -u origin update/<YYYY-MM-DD>  # push changes to GitHub
```

Then create a pull request on GitHub and merge the changes.

## Deploying updates to production

```bash
sudo su - almanotes  # switch to the almanotes user
cd /opt/local/alma-notes-import-flask  # change to the project directory
git pull  # pull the latest changes from GitHub
~/poetry/bin/poetry install  # install any new dependencies (using the poetry binary in the user's home directory)
sudo systemctl restart almanotesimport  # restart the systemd service
```
