import paramiko
import config

# Test SFTP connection using config values from config.py
print('Testing SFTP connection...')
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config.SFTP_HOST,
        port=config.SFTP_PORT,
        username=config.SFTP_USERNAME,
        password=config.SFTP_PASSWORD
    )
    sftp = ssh.open_sftp()
    files = sftp.listdir(config.SFTP_SERVER_PATH)
    print(f'SFTP Connected!')
    print(f'Files in {config.SFTP_SERVER_PATH}: {len(files)} files')
    for f in files[:5]:  # show first 5 files as sample 
        print(f'  - {f}')
    sftp.close()
    ssh.close()
except Exception as e:
    print(f'SFTP Error: {e}')
