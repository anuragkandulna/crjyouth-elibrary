#!/usr/bin/env bash


# Function to check if python 3 is installed
check_python_installed() {
    if command -v python3 &> /dev/null
    then
        echo "Python 3 is already installed. Version: $(python3 --version)"
    elif command -v python &> /dev/null
    then
        echo "Python 3 is already installed. Version: $(python --version)"
    else
        echo "Python 3 is not installed. Please install Python 3."
        exit 1
    fi
}


# Function to create Python 3 virtual environment
create_python_venv() {
    # Cleaning up local virtual environment
    if [ -d $ENV ]; then
        echo "Python Virtual environment ${ENV} already exist."
        return 1
    fi

    # Creating a new environment
    echo "Creating new virtual environment..."
    if command -v python3 &> /dev/null
    then
        python3 -m venv $ENV
    else
        python -m venv $ENV
    fi

    # Verify environment creation was success
    if [ $? -eq 0 ]; then
        echo "Successfully created virtual environment in directory: ${ENV}"
    else
        echo "Failed to create virtual environment. Exiting now!"
        exit 1
    fi

}


# Function to activate Python 3 venv and update packages
update_python_packages() {
    # Check if .pyenv312 directory exists
    if [ -d $ENV ]; then
        echo "Python Virtual environment ${ENV} exist. Updating packages..."
    else
        echo "No ${ENV} python virtual environment found. Exiting now!"
        exit 1
    fi

      # Activate the virtual environment
    source $ENV/bin/activate

    # Check if the virtual environment is activated by showing the Python executable path
    echo "Python executable used in virtual environment:"
    which python3

    # Check the location of pip
    echo "Pip executable used in virtual environment:"
    which pip3

    # Install the packages from requirements_3_12.txt
    if [ -f $REQUIREMENTS_FILE ]; then
        pip3 install -r $REQUIREMENTS_FILE
        echo "Python packages installed from ${REQUIREMENTS_FILE} ..."
    else
        echo "${REQUIREMENTS_FILE} not found. Exiting now!"
        exit 1
    fi

    # Show the currently installed packages in the virtual environment
    echo "Currently installed packages in the virtual environment:"
    pip3 list

    # Deactivate the python virtual environment
    deactivate
    echo "Python virtual environment deactivated. Success!"
}


# ------------------------------------------ START HERE ----------------------------------------- #
# Start python virtual environment creation with hidden dir .pyenv312
ENV=".pyenv312"
REQUIREMENTS_FILE="requirements.txt"

# Invoke functions to do the respective task
check_python_installed
create_python_venv
update_python_packages