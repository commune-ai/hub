
## Installation Guide

### Prerequisites
- Docker
- Python 3

### Setup Steps

1. Clone the hub repository:
   ```
   git clone https://github.com/commune-ai/hub.git
   cd hub;
   git checkout arena;
   ```

2. Install hub:


### Docker Setup:


 Make scripts executable if they arent:
```
make chmod_scripts 
```
or
```
chmod +x ./hub/scripts/*
```

Build the container
```
make build # ./hub/scripts/build.sh

```


Start the Container
```
make start 
```
or 
```
make up
```


Run tests in the container (optional):

```
make tests
```


### Local Setup (Python):

npm install -g pm2
pip install -e ./

To setup inside a virtual environment:

python3 -m venv env
source env/bin/activate
pip install -e ./

to exit the virtual environment:

deactivate


3.
4. Build and start the Docker container:
   ```
   make build
   make start
   ```

5. Run tests (optional):
   ```
   make tests
   ```

6. Start the main application:
   ```
   make app
   ```
