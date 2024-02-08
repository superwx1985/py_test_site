from daphne.cli import CommandLineInterface
from daphne.server import Server, logger


class VicServer(Server):

    def log_action(self, protocol, action, details):
        """
        Dispatches to any registered action logger, if there is one.
        """
        # if self.action_logger:
        #     self.action_logger(protocol, action, details)
        msg = None
        # HTTP requests
        if protocol == "http" and action == "complete":
            msg = "HTTP %(method)s %(path)s %(status)s [%(time_taken).2f, %(client)s]\n" % details
        # websocket requests
        elif protocol == "websocket" and action == "connected":
            msg = "WebSocket CONNECT %(path)s [%(client)s]\n" % details
        elif protocol == "websocket" and action == "disconnected":
            msg = "WebSocket DISCONNECT %(path)s [%(client)s]\n" % details
        elif protocol == "websocket" and action == "connecting":
            msg = "WebSocket HANDSHAKING %(path)s [%(client)s]\n" % details
        elif protocol == "websocket" and action == "rejected":
            msg = "WebSocket REJECT %(path)s [%(client)s]\n" % details

        if msg and msg[-1] == '\n':
            msg = msg[0:-1]
        logger.info(msg)


class VicCommandLineInterface(CommandLineInterface):

    server_class = VicServer


if __name__ == "__main__":
    vc = VicCommandLineInterface()
    vc.entrypoint()
