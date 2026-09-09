import asyncio, asyncssh
from .base import Connection
class SSHConnection(Connection):
    def __init__(self, host, port, username, password=None, private_key=None, timeout=10, command_timeout=30):
        self.host,self.port,self.username=host,port,username; self.password=password; self.private_key=private_key; self.timeout=timeout; self.command_timeout=command_timeout; self.conn=None
    async def connect(self):
        kwargs={"host":self.host,"port":self.port,"username":self.username,"connect_timeout":self.timeout,"known_hosts":None}
        if self.password is not None: kwargs["password"]=self.password
        if self.private_key is not None: kwargs["client_keys"]=[asyncssh.import_private_key(self.private_key)]
        self.conn=await asyncssh.connect(**kwargs); return self
    async def run(self, command):
        if not self.conn: raise RuntimeError("SSH connection is not established")
        result=await asyncio.wait_for(self.conn.run(command,check=True),self.command_timeout); return result.stdout
    async def close(self):
        if self.conn:
            self.conn.close(); await self.conn.wait_closed(); self.conn=None
