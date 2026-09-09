import asyncio
import logging
from typing import Optional

from pypsrp.exceptions import (
    AuthenticationError,
    WinRMTransportError,
    WSManFaultError,
)
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

from .base import Connection

logger = logging.getLogger(__name__)


class WinRMConnection(Connection):
    """
    Async-compatible WinRM connection based on pypsrp.

    The actual pypsrp/WSMan operations are synchronous, so they are
    executed in a worker thread to avoid blocking the asyncio event loop.

    Supported authentication:
        - negotiate
        - ntlm
        - kerberos
        - credssp
        - basic
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        https: bool = False,
        verify_tls: bool = False,
        timeout: int = 15,
        auth: str = "ntlm",
        operation_timeout: int = 20,
        read_timeout: int = 30,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.https = https
        self.verify_tls = verify_tls

        self.timeout = timeout
        self.operation_timeout = operation_timeout
        self.read_timeout = read_timeout

        self.auth = auth.lower()

        self.wsman: Optional[WSMan] = None
        self.runspace: Optional[RunspacePool] = None

        self._connected = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self):
        """
        Establishes a WinRM/WSMan connection and initializes a PSRP
        runspace.

        A small PowerShell command is executed as a connectivity/auth
        test.
        """

        if self._connected:
            return self

        await asyncio.wait_for(
            asyncio.to_thread(self._connect_sync),
            timeout=self.timeout,
        )

        self._connected = True

        logger.info(
            "WinRM connected: host=%s port=%s https=%s auth=%s user=%s",
            self.host,
            self.port,
            self.https,
            self.auth,
            self.username,
        )

        return self

    def _connect_sync(self):
        """
        Synchronous pypsrp connection initialization.

        Executed inside a worker thread by connect().
        """

        self.wsman = WSMan(
            server=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            ssl=self.https,
            path="wsman",
            auth=self.auth,
            cert_validation=self.verify_tls,
            connection_timeout=self.timeout,
            operation_timeout=self.operation_timeout,
            read_timeout=self.read_timeout,
            encryption="auto",
        )

        self.runspace = RunspacePool(
            self.wsman,
            configuration_name="Microsoft.PowerShell",
        )

        try:
            self.runspace.open()

            # Connectivity/authentication test.
            ps = PowerShell(self.runspace)

            ps.add_cmdlet("Write-Output")
            ps.add_argument(
                "$PSVersionTable.PSVersion.ToString()"
            )

            ps.invoke()

            if ps.had_errors:
                errors = "\n".join(
                    str(error)
                    for error in ps.streams.error
                )

                raise RuntimeError(
                    f"WinRM PowerShell initialization failed: {errors}"
                )

        except Exception:
            self._close_sync()
            raise

    # ------------------------------------------------------------------
    # PowerShell execution
    # ------------------------------------------------------------------

    async def run(self, command: str) -> str:
        """
        Executes PowerShell through the existing PSRP runspace.

        Returns:
            stdout as string.

        Raises:
            RuntimeError:
                if the connection isn't established or PowerShell
                reports an error.
        """

        if not self._connected or self.runspace is None:
            raise RuntimeError(
                "WinRM connection is not established"
            )

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self._run_sync,
                    command,
                ),
                timeout=self.timeout,
            )

        except asyncio.TimeoutError:
            logger.error(
                "WinRM command timed out: host=%s command=%s",
                self.host,
                command[:200],
            )
            raise

        except (
            AuthenticationError,
            WinRMTransportError,
            WSManFaultError,
        ):
            self._connected = False
            raise

    def _run_sync(self, command: str) -> str:
        """
        Synchronous PSRP command execution.

        Executed in a worker thread.
        """

        if self.runspace is None:
            raise RuntimeError(
                "WinRM runspace is not initialized"
            )

        logger.debug(
            "Executing PowerShell on %s: %s",
            self.host,
            command[:500],
        )

        ps = PowerShell(self.runspace)

        # Invoke-Expression allows the collectors to continue passing
        # ordinary PowerShell strings through Connection.run().
        ps.add_cmdlet("Invoke-Expression")
        ps.add_parameter(
            "Command",
            command,
        )

        ps.invoke()

        # PSRP deserializes objects. Convert them to strings in a way
        # compatible with the JSON-based collectors.
        output = []

        for item in ps.output:
            output.append(str(item))

        stdout = "\n".join(output)

        if ps.had_errors:
            errors = []

            for error in ps.streams.error:
                errors.append(str(error))

            stderr = "\n".join(errors)

            raise RuntimeError(
                f"WinRM PowerShell command failed: {stderr}"
            )

        return stdout

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    async def close(self):
        """
        Closes the PSRP runspace and WSMan transport.
        """

        if not self.runspace and not self.wsman:
            self._connected = False
            return

        try:
            await asyncio.to_thread(
                self._close_sync,
            )
        finally:
            self.runspace = None
            self.wsman = None
            self._connected = False

        logger.debug(
            "WinRM connection closed: %s",
            self.host,
        )

    def _close_sync(self):
        """
        Synchronous cleanup.
        """

        if self.runspace is not None:
            try:
                self.runspace.close()
            except Exception as exc:
                logger.debug(
                    "Failed to close WinRM runspace: %s",
                    exc,
                )

        self.runspace = None
        self.wsman = None