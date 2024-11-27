git pull

venv=.venv/bin/

if [[ -d "${venv}" && ! -L "${venv}" ]]; then
	source ${venv}/activate
else
	echo "venv not found."
fi

pip install -U -r requirements.txt
python3 lfinancialbot.py
