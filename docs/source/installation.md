# Installation guide

## Python projects (js_crawler, flask_server)

Use pipenv file to install everything!

## VPNs

Some VPNs habe been used to test our hipothesis. In this section, I will explain how I installed them.

### Windscribe

ProtonVPN has been tested in Ubuntu 20.04.1 LTS. These are the installation instructions

1. Add key file

```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key FDC247B7
```

2. Add repository

```bash
echo 'deb https://repo.windscribe.com/ubuntu bionic main' | sudo tee /etc/apt/sources.list.d/windscribe-repo.list
```

3. Update and install

```bash
sudo apt-get update && sudo apt-get install windscribe-cli
```

You can now loggin and connect to the VPN. Here is the list help page:

```
Usage: windscribe [<options>] <command> [<args>]...

  ██╗    ██╗██╗███╗   ██╗██████╗ ███████╗ ██████╗██████╗ ██╗██████╗ ███████╗
  ██║    ██║██║████╗  ██║██╔══██╗██╔════╝██╔════╝██╔══██╗██║██╔══██╗██╔════╝
  ██║ █╗ ██║██║██╔██╗ ██║██║  ██║███████╗██║     ██████╔╝██║██████╔╝█████╗
  ██║███╗██║██║██║╚██╗██║██║  ██║╚════██║██║     ██╔══██╗██║██╔══██╗██╔══╝
  ╔███╔███╔╝██║██║ ╚████║██████╔╝███████║╚██████╗██║  ██║██║██████╔╝███████╗
  ╚═══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝

  Windscribe CLI client v1.4

  If you experience any issues, please send a debug log and contact support:
  support@windscribe.com or submit a ticket:
  https://windscribe.com/support/ticket

Options:
  --help  Show this message and exit.

Commands:
  status      Check status of Windscribe and connection
  account     Output current account details
  connect     Connect to Windscribe
  disconnect  Disconnect from VPN
  examples    Show usage examples
  firewall    View/Modify Firewall mode
  lanbypass   View/Modify Firewall LAN bypass
  locations   Output list of all available server locations
  login       Login to Windscribe account
  logout      Logout and disconnect
  port        View/Modify default Port
  protocol    View/Modify default Protocol
  proxy       View/Modify Proxy Settings
  sendlog     Send the debug log to Support
  speedtest   Test the connection speed
  viewlog     View the debug log
```

### ProtonVPN

ProtonVPN has been tested in Ubuntu 20.04.1 LTS. These are the installation instructions

1. Install required dependencies.

```bash
sudo apt-get install openvpn python3.8 dialog python3-pip python3-setuptools
```

2. Install VPN client

```bash
sudo pip3 install protonvpn-cli
```

3. Initialize profile

```bash
sudo protonvpn init
```

Once this command is run, it will ask your OpenVPN credentialsm your plan and the protocol to use. You will find your credentials at <https://account.protonvpn.com/account>. I have used the Free plan, using TCP protocol.

List of example commands:
```
protonvpn connect
               Display a menu and select server interactively.

protonvpn c BE-5
               Connect to BE#5 with the default protocol.

protonvpn connect NO#3 -p tcp
               Connect to NO#3 with TCP.

protonvpn c --fastest
               Connect to the fastest VPN Server.

protonvpn connect --cc AU
               Connect to the fastest Australian server
               with the default protocol.

protonvpn c --p2p -p tcp
               Connect to the fastest torrent server with TCP.

protonvpn c --sc
               Connect to the fastest Secure-Core server with
               the default protocol.

protonvpn reconnect
               Reconnect the currently active session or connect
               to the last connected server.

protonvpn disconnect
               Disconnect the current session.

protonvpn s
               Print information about the current session.
```
