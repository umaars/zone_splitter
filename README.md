# zone_splitter
Use MiniConda and create an environment with python3, centos 7 does not support python3 natively.

conda create --name myenv python=3.8
conda activate myenv
conda install requests

python ./net.py
