# GLOHA - Automatic Switching based on Network Connectivity

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

## Overview

GLOHA (Global High Availability) is a Python tool designed to automatically switch between startup scripts or NAT forwarding rules based on network connectivity. It determines network connectivity using TCP connections and ICMP latency checks.

## Installation & Quick Start

### Requirements

- Python 3.x
- [ping3](https://pypi.org/project/ping3/) module

### Steps

1. Clone the GLOHA repository:  

```bash
git clone https://github.com/your-username/GLOHA.git
cd GLOHA
```
   
2. Customize the config  

3. Run `python3 ./main.py <config_file> <log_level (0-3)>`.  


## Usage Examples

### Configuration

#### JSON style

GLOHA uses a configuration file in JSON format. Example configuration:  

```javascript
{
  // Example of NAT redirect node
  // TCP traffic to 192.168.10.185:80 will be redirected to 192.168.10.1:8800 or 192.168.10.2:8001,
  // decided by connectivity of 127.0.0.1:8000 and 127.0.0.1:8001
  "RULE_1": {
    "check_interval": 10,  // Connectivity check interval (second). If not set, default is 20
    "check_scheme": "tcp",  // "tcp" or "icmp"
    "run_mode": "redirect:tcp:192.168.10.185:80",  // If not set, default is "ps"
    "server_list": {
      // There must be a "0" node as first select node
      "0": {
        "host": "127.0.0.1:8000",  // GLOHA will check connectivity of this host
        "target": "192.168.10.1:8800",  // Target of redirect
        "timeout": 200  // If latency to the host over this value, the node is seen as unavaliable
      },
      // If "0" node failed, switch to the next node
      "1": {
        "host": "127.0.0.1:8001",
        "target": "192.168.10.2:8001",
        "timeout": 200
      }
    }
  },

  // Example of PS node
  // If 192.168.1.1 is accessible, "gost -L=socks://127.0.0.1:1080" will be executed
  // Otherwise, if 192.168.1.2 is accessible now, "gost -L=socks://127.0.0.1:1081" will be executed
  "RULE_2": {
    "check_interval": 20,
    "check_scheme": "icmp",
    "run_mode": "ps",
    "server_list": {
      "0": {
        "host": "192.168.1.1",
        "exec": "gost -L=socks://127.0.0.1:1080",
        "timeout": 200
      },
      "1": {
        "host": "192.168.1.2",
        "exec": "gost -L=socks://127.0.0.1:1081",
        "timeout": 300
      }
    }
  }
}
```

#### Simplified style

From 2024/12/3, a new config style became available, which provides a much more graceful choice :)

```text
*RED_EXAMPLE
# chk_interval, chk_scheme, red_from
10, tcp, redirect:tcp:192.168.10.185:80
# chk_host, red_to, permit_timeout
127.0.0.1:8000, 192.168.10.1:8800, 200
127.0.0.1:8001, 192.168.10.2:8001, 200

*EXEC_EXAMPLE
# chk_interval, chk_scheme, run_mode
15, icmp, ps
# chk_host, exec, permit_timeout
192.168.1.1, gost -L="socks://127.0.0.1:1080", 200
192.168.1.2, gost -L="socks://127.0.0.1:1081", 300
```

### Launch

Run `python3 ./main.py ./config.json 2` (JSON style)  
Or `python3 ./main.py ./config.conf 2` (Simplified style)  

### Other functions

- Show runing processes: `python3 ./main.py -p`  
- Terminate running: `python3 ./main.py -t`  

## Solved Bugs

### bug-230306
Signal(2) cannot kill processes that launched by "nohup".

### bug-230228
Process out of control when a session is empty (all nodes died) and then the config is reloaded.

