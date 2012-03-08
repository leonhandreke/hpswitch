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

        # Establish a new SSH connection to the switch.

        # TODO: what happens if the connection drops?
        self._ssh_connection = paramiko.SSHClient()
        self._ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh_connection.connect(self.hostname,
                username=self.username, password=self.password,
                allow_agent=False)
        # Request a new pseudo-terminal and immediately resize it to something huge. Else, the switch will try to make
        # the output scrollable with a keyboard, which is somewhat hard to emulate in code.
        self._ssh_pty = self._ssh_connection.invoke_shell()
        self._ssh_pty.resize_pty(width = 1000000, height=1000000)
        # Receive the annoying HP welcome message and skip it immediately.
        self._ssh_pty.recv(9000)
        self._ssh_pty.send('\n')
        self._ssh_pty.recv(9000)

    def execute_command(self, command, timeout=5):
        """
        Execute a command on the switch using the SSH protocol.
        Returns the output of the command.
        """
        # Set the timout for the SSH channel to return the command output and run the desired command.
        self._ssh_pty.settimeout(timeout)
        self._ssh_pty.send(command + '\n')

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

