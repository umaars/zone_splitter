# zone_splitter

Make sure to take a snapshot of the OnApp VM before you proceed to protect against any mistakes.

Use MiniConda and create an environment with python3, centos 7 does not support python3 natively.
https://docs.conda.io/en/latest/miniconda.html

conda create --name myenv python=3.8

conda activate myenv

conda install requests

conda install -c conda-forge requests-cache

# Now run the script

python ./net.py
