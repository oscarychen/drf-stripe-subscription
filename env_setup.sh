
#!/bin/bash

echo "Removing existing environment/ directory..."
rm -r environment

echo "Creating new environment at environment/ ..."
python3 -m venv environment/

if [[ "$OSTYPE" == "msys"* ]]
then
	ENVPATH="environment/Scripts/activate"
elif [[ "$OSTYPE" == "cygwin"* ]]
then
	ENVPATH="environment/Scripts/activate"
	COMMENT_SYNTAX="rem"
elif [[ "$OSTYPE" == "win32"* ]]
then
	ENVPATH="environment/Scripts/activate"
else
	ENVPATH="environment/bin/activate"
fi

echo "Installing python packages to environment at $ENVPATH ..."
source $ENVPATH
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
deactivate

echo "Creating activate.sh..."
touch activate.sh
echo > activate.sh
echo "# Created by env_setup.sh, modify the environment variables below if needed.">>activate.sh
echo "source $ENVPATH">> activate.sh
echo >> activate.sh

echo 'Finished setting up environment.'
echo 'To activate environment, run `source activate.sh`.'



