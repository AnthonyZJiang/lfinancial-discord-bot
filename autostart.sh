venv=.venv/bin/

if [[ -d "${venv}" && ! -L "${venv}" ]]; then
	source ${venv}/activate
else
	echo "venv not found."
fi
python3 lfinancialbot.py
