import paramiko
import re

class Switch(object):
    """
    Represents a generic HP Networking switch.
    """
    def __init__(self, hostname, username, password):
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

        The `timeout` given in seconds dictates how long this method should wait for the switch to send the command
        output before raising a `socket.timeout` exception.

        Returns the output of the command.
        """
        # Set the timout for the SSH channel to return the command output and run the desired command.
        self._ssh_pty.settimeout(timeout)
        self._ssh_pty.send(command + '\n')

        recv_buffer = ''
        while True:
            # Receive lots of bytes so that in most cases, another `recv()` call is not required.
            recv_buffer += self._ssh_pty.recv(1000000)
            # Clean up the vt100 control sequences that the switch inserts. The regular expression is stolen from a
            # thread on [python-list](http://mail.python.org/pipermail/python-list/2009-September/1219674.html).
            recv_buffer = re.sub("\x1B[^A-Za-z]*?[A-Za-z]", '', recv_buffer)
            # Check if the received string ends with a `# ` shell-prompt. If so, it's pretty safe to assume that the
            # command has finished executing and all desired output has been received.
            if recv_buffer.endswith('# '):
                break

        # Strip off the command entered command at the beginning and the last line containing the shell prompt
        recv_buffer = re.sub(r"^" + command, "", recv_buffer)
        recv_buffer = re.sub(r"\r\n.*?# $", "", recv_buffer)

        return recv_buffer

