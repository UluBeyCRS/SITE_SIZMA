git clone https://github.com/UluBeyCRS/SITE_SIZMA.git

cd SITE_SIZMA

# Kali Linux 

sudo apt update && sudo apt upgrade -y

sudo apt install python3 python3-pip -y

pip3 install requests

chmod +x sızma_test.py

python3 sızma_test.py 


# Termux

pkg update && pkg upgrade -y

pkg install python -y

pip install requests

chmod +x sızma_test.py

python sızma_test.py 
