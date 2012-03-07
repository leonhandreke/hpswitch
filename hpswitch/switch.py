import paramiko
import re

class Switch(object):
    def __init__(self, hostname, username, password):
        """
        Construct a new Switch instance.
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def execute_command(self, command, timeout = 5):
        """
        Execute a command on the switch using the SSH protocol.
        Returns the output of the command.
        """
        self.ssh.connect(self.hostname, username=self.username, password=self.password, allow_agent=False)
        channel = self.ssh.invoke_shell()
        # get a big-ass pty - we do not want to emulate scrolling
        channel.resize_pty(width = 1000000, height=1000000)
        channel.settimeout(timeout)
        # skip the welcome message
        channel.recv(9000)
        channel.send('\n')
        channel.recv(9000)
        # execute the desired command
        channel.send(command + '\n')

        recv_buffer = ''
        while True:
            # receive lots of bytes
            recv_buffer += channel.recv(1000000)
            # clean up the vt100 control sequences
            # http://mail.python.org/pipermail/python-list/2009-September/607067.html
            recv_buffer = re.sub("\x1B[^A-Za-z]*?[A-Za-z]", '', recv_buffer)
            # see if the buffer ends with a shell prompt
            # TODO: figure out a better heuristic to detect the end of the command
            if recv_buffer.endswith('# '):
                # strip off the first and the last line; The first one
                # contains the repeated command, the last one the prompt
                recv_buffer = re.sub(r"^.*?\r\n", "", recv_buffer)
                recv_buffer = re.sub(r"\r\n.*?# $", "", recv_buffer)
                # exit the loop - we've read enough
                break

        # close the ssh connection to the switch
        self.ssh.close()
        return recv_buffer

